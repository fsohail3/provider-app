#!/usr/bin/env python3
"""
Healthcare AI Procedure Assistant with Epic FHIR Integration
Enhanced version with comprehensive role-based checklists and patient data integration
"""
import os
import json
import base64
import requests
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TypeDecorator, String
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from logging.handlers import RotatingFileHandler
import openai
from dotenv import load_dotenv
from typing import Dict

# Import enhanced Epic FHIR client and role-based system
# from epic_fhir_client import EpicFHIRClient
# from role_based_checklist import RoleBasedChecklistGenerator

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    print("WARNING: OPENAI_API_KEY not found in environment variables")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Encryption setup
class EncryptedType(TypeDecorator):
    impl = String

    def __init__(self):
        super().__init__()
        self.encryption_key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())
        self.fernet = Fernet(self.encryption_key)

    def process_bind_param(self, value, dialect):
        if value is not None:
            return self.fernet.encrypt(value.encode()).decode()
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            return self.fernet.decrypt(value.encode()).decode()
        return None

# Enhanced security configurations
app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Strict',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    SQLALCHEMY_DATABASE_URI='sqlite:///healthcare.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.urandom(32)
)

# Epic FHIR Configuration
EPIC_CONFIG = {
    "client_id": os.getenv('EPIC_CLIENT_ID'),
    "client_secret": os.getenv('EPIC_CLIENT_SECRET'),
    "redirect_uri": "https://provider-app-icbi.onrender.com/launch",
    "jwks_url": "https://provider-app-icbi.onrender.com/.well-known/jwks.json",
    "auth_method": "client_secret_basic",
    "persistent_access": True,
    "fhir_base_url": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
}

# Generate RSA key pair for JWK (do this once and store securely)
def generate_epic_keys():
    """Generate RSA key pair for Epic authentication"""
    try:
        # Check if keys already exist
        if os.path.exists('epic_private_key.pem') and os.path.exists('epic_public_key.pem'):
            with open('epic_private_key.pem', 'rb') as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)
            with open('epic_public_key.pem', 'rb') as f:
                public_key = serialization.load_pem_public_key(f.read())
        else:
            # Generate new keys
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            public_key = private_key.public_key()
            
            # Save keys securely
            with open('epic_private_key.pem', 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            with open('epic_public_key.pem', 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
        
        return private_key, public_key
    except Exception as e:
        app.logger.error(f"Error generating Epic keys: {str(e)}")
        return None, None

# Initialize Epic keys
EPIC_PRIVATE_KEY, EPIC_PUBLIC_KEY = generate_epic_keys()

# Setup logging
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/healthcare.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Healthcare AI startup')

# Initialize extensions
db = SQLAlchemy(app)

# Replace with simple consent tracking
class ConsentTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50))
    consent_date = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))

class User(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    subscription_status = db.Column(db.String(20), default='trial')  # 'trial' or 'active'
    query_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_query = db.Column(db.DateTime)

# Update consent check
@app.before_request
def check_consent():
    # Skip consent check for static files, privacy page, terms page, Epic endpoints, and the consent submission endpoint
    if (request.endpoint in ['static', 'privacy', 'terms'] or 
        request.path == '/accept-consent' or
        request.path == '/launch' or
        request.path == '/app' or
        request.path.startswith('/.well-known/')):
        return
    
    consent = session.get('consent_accepted')
    if not consent:
        app.logger.info(f"No consent found, redirecting to privacy. Session ID: {session.get('session_id', 'none')}")
        return redirect(url_for('privacy'))

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if not session.get('consent_accepted'):
        app.logger.info(f"No consent found, redirecting to privacy. Session ID: {session.get('session_id', 'none')}")
        return redirect(url_for('privacy'))
    app.logger.info(f"Consent verified, rendering main app. Session ID: {session.get('session_id', 'none')}")
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        app.logger.info('Chat endpoint called')
        app.logger.info(f'Headers: {dict(request.headers)}')
        
        # Get or create user session ID
        user_id = session.get('user_id')
        app.logger.info(f'User ID from session: {user_id}')
        
        if not user_id:
            user_id = os.urandom(16).hex()
            session['user_id'] = user_id
            app.logger.info(f'Created new user ID: {user_id}')

        # Log request data
        data = request.json
        app.logger.info(f'Request data: {json.dumps(data, indent=2)}')

        # Check subscription status
        user = User.query.get(user_id)
        if not user:
            app.logger.info(f'Creating new user with ID: {user_id}')
            user = User(id=user_id, subscription_status='trial', query_count=0)
            db.session.add(user)
            db.session.commit()

        if user.subscription_status != 'active' and user.query_count >= 10:
            app.logger.info(f'Trial limit reached for user: {user_id}')
            return jsonify({
                "response": "Trial limit reached",
                "show_payment": True
            })

        # Get practitioner role from request
        practitioner_role = data.get('practitionerRole', 'Unknown')
        app.logger.info(f'Practitioner role: {practitioner_role}')
        
        # Get Epic patient data if available
        epic_patient_data = session.get('epic_patient_data', {})
        has_epic_data = bool(epic_patient_data)
        
        # Create enhanced system prompt with role and Epic data
        system_prompt = create_enhanced_system_prompt(
            data.get('consultationType'),
            practitioner_role,
            epic_patient_data
        )
        
        # Create messages array
        messages = [{"role": "system", "content": system_prompt}]
        
        chat_history = data.get('chatHistory', [])
        if chat_history:
            messages.extend(chat_history[-4:])
        
        # Add user message
        user_message = create_user_message(data, practitioner_role, epic_patient_data)
        messages.append({"role": "user", "content": user_message})
        
        app.logger.info(f'Sending request to OpenAI with {len(messages)} messages')
        
        # Call OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Update user query count
        user.query_count += 1
        user.last_query = datetime.utcnow()
        db.session.commit()
        
        app.logger.info(f'AI response generated successfully. User query count: {user.query_count}')
        
        return jsonify({
            "response": ai_response,
            "show_payment": False
        })
        
    except Exception as e:
        app.logger.error(f'Error in chat endpoint: {str(e)}')
        import traceback
        app.logger.error(f'Full traceback: {traceback.format_exc()}')
        return jsonify({"error": "An error occurred while processing your request"}), 500

def create_enhanced_system_prompt(consultation_type, practitioner_role, epic_patient_data):
    """Create enhanced system prompt with role-based and Epic data integration"""
    
    base_prompt = f"""You are an AI healthcare assistant specialized in providing {consultation_type} guidance for healthcare professionals.

**Your Role:** You are assisting a {practitioner_role} with patient care and procedure guidance.

**Key Responsibilities:**
- Provide evidence-based recommendations
- Highlight safety considerations specific to the {practitioner_role} role
- Consider patient-specific factors and risks
- Offer practical, actionable guidance
- Maintain professional medical standards

**Role-Specific Focus Areas for {practitioner_role}:**
"""
    
    # Add role-specific guidance
    role_guidance = get_role_specific_guidance(practitioner_role)
    base_prompt += role_guidance
    
    # Add Epic patient data if available
    if epic_patient_data:
        base_prompt += "\n\n**Patient Data from Epic EHR:**\n"
        base_prompt += format_epic_patient_data(epic_patient_data)
    
    base_prompt += """

**Response Guidelines:**
- Be concise but comprehensive
- Prioritize safety and best practices
- Consider the practitioner's specific role and scope
- Highlight any patient-specific risks or considerations
- Provide actionable next steps
- Use clear, professional medical terminology

**Medical Disclaimer:** This is for educational purposes only. Always use clinical judgment and follow institutional protocols.
"""
    
    return base_prompt

def get_role_specific_guidance(role):
    """Get role-specific guidance for the system prompt"""
    role_guidance = {
        'ER Nurse': """
- Focus on rapid assessment and triage protocols
- Prioritize time-critical interventions
- Consider emergency equipment and medication availability
- Emphasize patient safety and monitoring
- Address immediate stabilization needs""",
        
        'ICU Nurse': """
- Emphasize critical care monitoring and interventions
- Focus on hemodynamic stability and ventilation management
- Consider medication titration and side effects
- Address family communication and support
- Prioritize infection control and prevention""",
        
        'Nurse Practitioner': """
- Provide comprehensive assessment guidance
- Consider diagnostic reasoning and differential diagnoses
- Address medication management and interactions
- Focus on patient education and follow-up planning
- Emphasize care coordination and referrals""",
        
        'Medical Assistant': """
- Focus on patient preparation and vital signs
- Emphasize equipment setup and sterilization
- Consider patient comfort and safety
- Address documentation and communication
- Prioritize infection control protocols""",
        
        'Surgical Technologist': """
- Emphasize surgical equipment and instrument management
- Focus on sterilization and aseptic technique
- Consider surgical count and safety protocols
- Address emergency equipment readiness
- Prioritize specimen handling and documentation""",
        
        'Emergency Medical Technician': """
- Focus on scene safety and rapid assessment
- Emphasize basic life support interventions
- Consider transport safety and patient monitoring
- Address communication with medical control
- Prioritize equipment operation and maintenance""",
        
        'Paramedic': """
- Emphasize advanced life support interventions
- Focus on cardiac monitoring and medication administration
- Consider medical control consultation
- Address transport safety and patient stabilization
- Prioritize documentation and quality improvement""",
        
        'Phlebotomist': """
- Focus on venipuncture technique and patient preparation
- Emphasize specimen collection and labeling
- Consider infection control and safety protocols
- Address patient comfort and communication
- Prioritize quality control and documentation""",
        
        'Occupational Therapist': """
- Focus on functional assessment and therapeutic interventions
- Emphasize equipment and adaptive device training
- Consider patient safety and progress monitoring
- Address home program development and instruction
- Prioritize care coordination and follow-up planning""",
        
        'Lab Technologist': """
- Emphasize test methodology and quality control
- Focus on equipment operation and maintenance
- Consider specimen processing and result validation
- Address safety protocols and documentation
- Prioritize accuracy and reliability""",
        
        'Lab Technician': """
- Focus on test execution and monitoring
- Emphasize quality control testing and verification
- Consider equipment operation and maintenance
- Address safety protocol compliance
- Prioritize documentation and reporting""",
        
        'Patient Care Technician': """
- Focus on basic patient care and comfort
- Emphasize vital signs measurement and documentation
- Consider patient safety and monitoring
- Address equipment operation and management
- Prioritize infection control and communication""",
        
        'Charge Nurse': """
- Emphasize staff supervision and resource management
- Focus on quality and safety oversight
- Consider communication and coordination
- Address emergency response preparation
- Prioritize documentation and quality improvement""",
        
        'Nurse Aide': """
- Focus on basic care and patient comfort
- Emphasize vital signs and patient monitoring
- Consider patient safety and positioning
- Address equipment setup and maintenance
- Prioritize infection control and communication""",
        
        'Nursing Assistant': """
- Focus on basic care and patient comfort
- Emphasize vital signs and patient monitoring
- Consider patient safety and positioning
- Address equipment setup and maintenance
- Prioritize infection control and communication""",
        
        'CNA': """
- Focus on basic care and patient comfort
- Emphasize vital signs and patient monitoring
- Consider patient safety and positioning
- Address equipment setup and maintenance
- Prioritize infection control and communication"""
    }
    
    return role_guidance.get(role, """
- Provide general healthcare guidance
- Consider patient safety and best practices
- Address documentation and communication
- Prioritize quality care delivery
- Emphasize professional standards""")

def format_epic_patient_data(epic_data):
    """Format Epic patient data for the system prompt"""
    formatted = ""
    
    # Demographics
    if epic_data.get('demographics'):
        demo = epic_data['demographics']
        formatted += f"- **Patient:** {demo.get('name', 'Unknown')}, Age: {demo.get('age', 'Unknown')}, Gender: {demo.get('gender', 'Unknown')}\n"
    
    # Vital signs
    if epic_data.get('vital_signs'):
        vitals = epic_data['vital_signs'][:3]  # Most recent 3
        formatted += f"- **Recent Vitals:** {len(vitals)} readings available\n"
    
    # Allergies
    if epic_data.get('allergies'):
        active_allergies = [a for a in epic_data['allergies'] if a.get('status', '').lower() != 'inactive']
        formatted += f"- **Active Allergies:** {len(active_allergies)} documented\n"
    
    # Medications
    if epic_data.get('medications'):
        active_meds = [m for m in epic_data['medications'] if m.get('status', '').lower() in ['active', 'active']]
        formatted += f"- **Active Medications:** {len(active_meds)} current medications\n"
    
    # Conditions
    if epic_data.get('medical_history'):
        active_conditions = [c for c in epic_data['medical_history'] if c.get('status', '').lower() in ['active', 'recurrence', 'relapse']]
        formatted += f"- **Active Conditions:** {len(active_conditions)} documented\n"
    
    # Labs
    if epic_data.get('labs'):
        abnormal_labs = [l for l in epic_data['labs'] if l.get('abnormal', False)]
        formatted += f"- **Abnormal Labs:** {len(abnormal_labs)} abnormal results\n"
    
    # Surgeries
    if epic_data.get('surgeries'):
        recent_surgeries = epic_data['surgeries'][:2]  # Most recent 2
        formatted += f"- **Recent Surgeries:** {len(recent_surgeries)} documented procedures\n"
    
    return formatted

def create_user_message(data, practitioner_role, epic_patient_data):
    """Create user message with role and Epic data integration"""
    
    # Build the user message
    message_parts = []
    
    # Consultation type
    consultation_type = data.get('consultationType', 'general')
    message_parts.append(f"Consultation Type: {consultation_type}")
    
    # Practitioner role
    message_parts.append(f"Practitioner Role: {practitioner_role}")
    
    # Procedure name
    if data.get('procedureName'):
        message_parts.append(f"Procedure: {data['procedureName']}")
    
    # Patient information
    patient_info = []
    if data.get('age'): patient_info.append(f"Age: {data['age']}")
    if data.get('gender'): patient_info.append(f"Gender: {data['gender']}")
    if data.get('chiefComplaint'): patient_info.append(f"Chief Complaint: {data['chiefComplaint']}")
    
    # Vitals
    vitals = []
    if data.get('bp'): vitals.append(f"BP: {data['bp']}")
    if data.get('heartRate'): vitals.append(f"HR: {data['heartRate']} bpm")
    if data.get('temperature'): vitals.append(f"Temp: {data['temperature']}°F")
    if data.get('spo2'): vitals.append(f"SpO2: {data['spo2']}%")
    
    if vitals:
        patient_info.append(f"Vitals: {', '.join(vitals)}")
    
    # Medical information
    if data.get('allergies'): patient_info.append(f"Allergies: {data['allergies']}")
    if data.get('medicalHistory'): patient_info.append(f"Medical History: {data['medicalHistory']}")
    if data.get('medications'): patient_info.append(f"Medications: {data['medications']}")
    if data.get('testResults'): patient_info.append(f"Test Results: {data['testResults']}")
    
    if patient_info:
        message_parts.append(f"Patient Information: {'; '.join(patient_info)}")
    
    # Epic data summary
    if epic_patient_data:
        epic_summary = []
        if epic_patient_data.get('demographics', {}).get('name'):
            epic_summary.append("Epic patient data available")
        if epic_patient_data.get('allergies'):
            epic_summary.append(f"{len(epic_patient_data['allergies'])} allergies documented")
        if epic_patient_data.get('medications'):
            epic_summary.append(f"{len(epic_patient_data['medications'])} medications documented")
        
        if epic_summary:
            message_parts.append(f"Epic EHR Data: {'; '.join(epic_summary)}")
    
    return "\n".join(message_parts)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

# Epic FHIR Integration Endpoints

@app.route('/.well-known/jwks.json')
def jwks():
    """JSON Web Key Set endpoint for Epic authentication"""
    try:
        if not EPIC_PUBLIC_KEY:
            return jsonify({"error": "Public key not available"}), 500
        
        # Get public key numbers
        public_numbers = EPIC_PUBLIC_KEY.public_numbers()
        
        # Convert to base64url encoding
        def int_to_base64url(value):
            """Convert integer to base64url encoding"""
            byte_length = (value.bit_length() + 7) // 8
            value_bytes = value.to_bytes(byte_length, byteorder='big')
            return base64.urlsafe_b64encode(value_bytes).decode('utf-8').rstrip('=')
        
        jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "kid": "provider-app-key-1",
                    "n": int_to_base64url(public_numbers.n),
                    "e": int_to_base64url(public_numbers.e),
                    "alg": "RS256"
                }
            ]
        }
        
        app.logger.info("JWK endpoint accessed successfully")
        return jsonify(jwks)
    
    except Exception as e:
        app.logger.error(f"Error in JWK endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
        return jsonify({"error": "Internal server error"}), 500

@app.route('/launch')
def epic_launch():
    """Handle Epic SMART App Launch with enhanced role-based system"""
    try:
        app.logger.info("🚀 Epic launch initiated with enhanced system")
        
        # Extract launch parameters from Epic
        iss = request.args.get('iss')  # Epic's FHIR server URL
        launch = request.args.get('launch')  # Launch token
        state = request.args.get('state')  # State parameter
        
        app.logger.info(f"Launch parameters - iss: {iss}, launch: {launch[:10]}..., state: {state}")
        
        if not iss or not launch:
            app.logger.error("Missing required launch parameters")
            return "Missing launch parameters", 400
        
        # Exchange launch token for access token
        token_response = exchange_launch_token(iss, launch)
        
        if not token_response:
            app.logger.error("Failed to exchange launch token")
            return "Launch failed", 400
        
        app.logger.info("✅ Successfully exchanged launch token")
        
        # Store tokens securely in session
        session['epic_access_token'] = token_response['access_token']
        session['epic_patient_id'] = token_response.get('patient')
        session['epic_iss'] = iss
        
        if 'refresh_token' in token_response:
            session['epic_refresh_token'] = token_response['refresh_token']
        
        # Initialize enhanced Epic FHIR client
        epic_client = EpicFHIRClient(
            access_token=token_response['access_token'],
            patient_id=token_response['patient'],
            fhir_base_url=iss
        )
        
        # Fetch comprehensive patient data
        app.logger.info("📊 Fetching comprehensive patient data from Epic")
        patient_data = epic_client.get_comprehensive_patient_data()
        
        # Initialize role-based checklist generator
        checklist_generator = RoleBasedChecklistGenerator()
        
        # Detect practitioner role
        practitioner_role = checklist_generator.detect_practitioner_role(
            patient_data.get('practitioner_role', {})
        )
        
        app.logger.info(f"👨‍⚕️ Detected practitioner role: {practitioner_role}")
        
        # Generate role-based checklist
        app.logger.info("📋 Generating role-based checklist")
        checklist = checklist_generator.generate_role_based_checklist(
            practitioner_role=practitioner_role,
            patient_data=patient_data,
            procedure_type='general'
        )
        
        # Store comprehensive data in session
        session['epic_patient_data'] = patient_data
        session['practitioner_role'] = practitioner_role
        session['role_based_checklist'] = checklist
        
        app.logger.info(f"✅ Epic integration complete - Role: {practitioner_role}, Patient: {token_response['patient']}")
        
        # Redirect to main app with Epic context
        return redirect('/app?epic_patient=' + token_response['patient'] + '&role=' + practitioner_role)
        
    except Exception as e:
        app.logger.error(f"❌ Error in Epic launch: {str(e)}")
        return "Launch failed", 500

def exchange_launch_token(iss, launch):
    """Exchange Epic launch token for access token"""
    try:
        token_url = f"{iss}/oauth2/token"
        
        # Use client_secret_basic authentication
        auth = (EPIC_CONFIG['client_id'], EPIC_CONFIG['client_secret'])
        
        payload = {
            'grant_type': 'authorization_code',
            'code': launch,
            'redirect_uri': EPIC_CONFIG['redirect_uri']
        }
        
        app.logger.info(f"Exchanging launch token with Epic at: {token_url}")
        
        response = requests.post(token_url, auth=auth, data=payload)
        
        if response.status_code == 200:
            token_data = response.json()
            app.logger.info("Successfully exchanged launch token")
            return token_data
        else:
            app.logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        app.logger.error(f"Error exchanging launch token: {str(e)}")
        return None

def fetch_epic_patient_data(access_token, patient_id, iss):
    """Fetch patient data from Epic FHIR server"""
    try:
        # Fetch patient demographics
        patient_url = f"{iss}/Patient/{patient_id}"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        app.logger.info(f"Fetching patient data from Epic: {patient_url}")
        
        response = requests.get(patient_url, headers=headers)
        
        if response.status_code == 200:
            patient_data = response.json()
            
            # Fetch additional patient data
            epic_data = {
                'demographics': patient_data,
                'vitals': fetch_epic_vitals(access_token, patient_id, iss),
                'allergies': fetch_epic_allergies(access_token, patient_id, iss),
                'medications': fetch_epic_medications(access_token, patient_id, iss),
                'conditions': fetch_epic_conditions(access_token, patient_id, iss)
            }
            
            app.logger.info("Successfully fetched Epic patient data")
            return epic_data
        else:
            app.logger.error(f"Failed to fetch patient data: {response.status_code}")
            return {}
            
    except Exception as e:
        app.logger.error(f"Error fetching Epic patient data: {str(e)}")
        return {}

def fetch_epic_vitals(access_token, patient_id, iss):
    """Fetch latest vital signs from Epic"""
    try:
        vitals_url = f"{iss}/Observation"
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'patient': patient_id,
            'category': 'vital-signs',
            '_sort': '-date',
            '_count': 10
        }
        
        response = requests.get(vitals_url, headers=headers, params=params)
        
        if response.status_code == 200:
            vitals_data = response.json()
            return parse_epic_vitals(vitals_data)
        return {}
        
    except Exception as e:
        app.logger.error(f"Error fetching Epic vitals: {str(e)}")
        return {}

def fetch_epic_allergies(access_token, patient_id, iss):
    """Fetch allergies from Epic"""
    try:
        allergies_url = f"{iss}/AllergyIntolerance"
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'patient': patient_id,
            'status': 'active'
        }
        
        response = requests.get(allergies_url, headers=headers, params=params)
        
        if response.status_code == 200:
            allergies_data = response.json()
            return parse_epic_allergies(allergies_data)
        return []
        
    except Exception as e:
        app.logger.error(f"Error fetching Epic allergies: {str(e)}")
        return []

def fetch_epic_medications(access_token, patient_id, iss):
    """Fetch active medications from Epic"""
    try:
        meds_url = f"{iss}/MedicationRequest"
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'patient': patient_id,
            'status': 'active,on-hold'
        }
        
        response = requests.get(meds_url, headers=headers, params=params)
        
        if response.status_code == 200:
            meds_data = response.json()
            return parse_epic_medications(meds_data)
        return []
        
    except Exception as e:
        app.logger.error(f"Error fetching Epic medications: {str(e)}")
        return []

def fetch_epic_conditions(access_token, patient_id, iss):
    """Fetch active conditions from Epic"""
    try:
        conditions_url = f"{iss}/Condition"
        headers = {'Authorization': f'Bearer {access_token}'}
        params = {
            'patient': patient_id,
            'clinical-status': 'active'
        }
        
        response = requests.get(conditions_url, headers=headers, params=params)
        
        if response.status_code == 200:
            conditions_data = response.json()
            return parse_epic_conditions(conditions_data)
        return []
        
    except Exception as e:
        app.logger.error(f"Error fetching Epic conditions: {str(e)}")
        return []

def parse_epic_vitals(vitals_data):
    """Parse Epic vital signs data"""
    vitals = {}
    try:
        for entry in vitals_data.get('entry', []):
            resource = entry.get('resource', {})
            code = resource.get('code', {}).get('coding', [{}])[0].get('code')
            value = resource.get('valueQuantity', {}).get('value')
            
            if code == 'blood-pressure':
                vitals['bp'] = value
            elif code == 'heart-rate':
                vitals['hr'] = value
            elif code == 'body-temperature':
                vitals['temp'] = value
            elif code == 'oxygen-saturation':
                vitals['spo2'] = value
                
        return vitals
    except Exception as e:
        app.logger.error(f"Error parsing Epic vitals: {str(e)}")
        return {}

def parse_epic_allergies(allergies_data):
    """Parse Epic allergies data"""
    allergies = []
    try:
        for entry in allergies_data.get('entry', []):
            resource = entry.get('resource', {})
            substance = resource.get('code', {}).get('text', 'Unknown')
            severity = resource.get('reaction', [{}])[0].get('severity', 'unknown')
            
            allergies.append({
                'substance': substance,
                'severity': severity
            })
        return allergies
    except Exception as e:
        app.logger.error(f"Error parsing Epic allergies: {str(e)}")
        return []

def parse_epic_medications(meds_data):
    """Parse Epic medications data"""
    medications = []
    try:
        for entry in meds_data.get('entry', []):
            resource = entry.get('resource', {})
            medication_ref = resource.get('medicationReference', {}).get('reference')
            status = resource.get('status', 'unknown')
            
            medications.append({
                'reference': medication_ref,
                'status': status
            })
        return medications
    except Exception as e:
        app.logger.error(f"Error parsing Epic medications: {str(e)}")
        return []

def parse_epic_conditions(conditions_data):
    """Parse Epic conditions data"""
    conditions = []
    try:
        for entry in conditions_data.get('entry', []):
            resource = entry.get('resource', {})
            code = resource.get('code', {}).get('text', 'Unknown')
            status = resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'unknown')
            
            conditions.append({
                'condition': code,
                'status': status
            })
        return conditions
    except Exception as e:
        app.logger.error(f"Error parsing Epic conditions: {str(e)}")
        return []

@app.route('/app')
def epic_app():
    """Main app page with enhanced Epic integration and role-based system"""
    epic_patient = request.args.get('epic_patient')
    practitioner_role = request.args.get('role')
    
    # Get comprehensive data from session
    epic_patient_data = session.get('epic_patient_data', {})
    session_role = session.get('practitioner_role')
    role_based_checklist = session.get('role_based_checklist', {})
    
    # Use role from URL or session
    final_role = practitioner_role or session_role or 'Unknown'
    
    app.logger.info(f"🎯 Rendering app with Epic data - Role: {final_role}, Patient: {epic_patient}")
    
    # Prepare enhanced context for template
    context = {
        'epic_patient_data': epic_patient_data,
        'practitioner_role': final_role,
        'role_based_checklist': role_based_checklist,
        'patient_summary': _generate_patient_summary(epic_patient_data),
        'role_info': _get_role_info(final_role),
        'has_epic_data': bool(epic_patient_data),
        'checklist_ready': bool(role_based_checklist)
    }
    
    return render_template('index.html', **context)

def _generate_patient_summary(patient_data: Dict) -> Dict:
    """Generate a summary of patient data for display"""
    if not patient_data:
        return {}
    
    summary = {
        'demographics': patient_data.get('demographics', {}),
        'vital_signs_count': len(patient_data.get('vital_signs', [])),
        'allergies_count': len(patient_data.get('allergies', [])),
        'medications_count': len(patient_data.get('medications', [])),
        'conditions_count': len(patient_data.get('medical_history', [])),
        'labs_count': len(patient_data.get('labs', [])),
        'surgeries_count': len(patient_data.get('surgeries', [])),
        'abnormal_labs_count': len([lab for lab in patient_data.get('labs', []) if lab.get('abnormal', False)]),
        'recent_vitals': patient_data.get('vital_signs', [])[:3],  # Most recent 3
        'active_allergies': [allergy for allergy in patient_data.get('allergies', []) 
                           if allergy.get('status', '').lower() != 'inactive'][:3],
        'active_medications': [med for med in patient_data.get('medications', []) 
                             if med.get('status', '').lower() in ['active', 'active']][:3]
    }
    
    return summary

def _get_role_info(role: str) -> Dict:
    """Get information about a specific role"""
    checklist_generator = RoleBasedChecklistGenerator()
    supported_roles = checklist_generator.supported_roles
    
    if role in supported_roles:
        return supported_roles[role]
    else:
        return {
            'display_name': role,
            'icon': '👨‍⚕️',
            'priority': 999,
            'specialties': ['general']
        }

@app.route('/accept-consent', methods=['POST'])
def accept_consent():
    try:
        # Generate a unique session ID if not exists
        if not session.get('session_id'):
            session['session_id'] = os.urandom(16).hex()
            app.logger.info(f"Generated new session ID: {session['session_id']}")

        session['consent_accepted'] = True
        session['consent_date'] = datetime.utcnow().isoformat()
        session.modified = True  # Force session modification
        
        app.logger.info(f"Session data before redirect: consent_accepted={session.get('consent_accepted')}, session_id={session.get('session_id')}")
        
        consent = ConsentTracking(
            session_id=session.get('session_id'),
            ip_address=request.remote_addr
        )
        db.session.add(consent)
        db.session.commit()
        
        app.logger.info("Consent saved to database successfully")
        
        # Simple redirect
        app.logger.info("Redirecting to home page")
        return redirect(url_for('home'))
    except Exception as e:
        app.logger.error(f"Error in accept_consent: {str(e)}")
        return "Error processing consent", 500 