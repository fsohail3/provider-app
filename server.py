import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, make_response
from dotenv import load_dotenv
from openai import OpenAI
import stripe
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, String
import logging
from logging.handlers import RotatingFileHandler
import json
# Epic FHIR integration imports
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import requests
import base64

load_dotenv()  # This will work locally but skip if file not found

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4-turbo-preview")
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

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
    # Skip consent check for static files, privacy page, terms page, and the consent submission endpoint
    if request.endpoint in ['static', 'privacy', 'terms'] or request.path == '/accept-consent':
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

        # Create messages array
        messages = [{"role": "system", "content": create_system_prompt(data.get('consultationType'))}]
        
        chat_history = data.get('chatHistory', [])
        if chat_history:
            messages.extend(chat_history[-4:])
        
        messages.append({
            "role": "user",
            "content": create_patient_context(data)
        })

        app.logger.info('Making OpenAI API call')
        # Make OpenAI API call
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7
        )
        
        app.logger.info('OpenAI API call successful')
        
        # Update query count for trial users
        if user.subscription_status == 'trial':
            user.query_count += 1
            db.session.commit()
            app.logger.info(f'Updated query count for user {user_id}: {user.query_count}')

        response_data = {
            "response": completion.choices[0].message.content,
            "queries_remaining": 10 - user.query_count if user.subscription_status == 'trial' else None
        }
        
        app.logger.info('Sending response back to client')
        return jsonify(response_data)

    except Exception as e:
        app.logger.error(f"Error in chat route: {str(e)}", exc_info=True)
        return jsonify({
            "response": "I apologize, but I encountered an error. Please try again."
        }), 500

# Add these helper functions
def create_system_prompt(consultation_type):
    if consultation_type == 'diagnosis':
        return """You are a medical AI assistant helping healthcare providers with diagnoses. 
Structure your response in this order:

1. Initial Assessment:
   • List possible diagnoses with ICD-10 codes (format: • Diagnosis (ICD-10))
   • Highlight immediate risk factors with '!RISK:' prefix

2. Recommended Testing Sequence:
   A. Immediate Tests (to be done today):
      • List urgent tests with CPT codes (format: • Test (CPT))
      • Explain why each test is needed
   
   B. Follow-up Tests (if needed):
      • List secondary tests with CPT codes
      • Specify conditions that would trigger these tests

3. Next Steps Based on Test Results:
   A. If Test A positive:
      • Recommended actions
      • Follow-up timeline
   B. If Test B positive:
      • Recommended actions
      • Follow-up timeline

4. Follow-up Plan:
   • Recommend follow-up timeline
   • Specify conditions requiring immediate return
   • List symptoms to monitor

5. Clinical Guidelines:
   [PROTOCOL: guideline name]
   • Key points from relevant guidelines
   • Specific protocol recommendations"""
    else:
        return """You are a medical AI assistant helping healthcare providers with procedures. 
Provide a clear, interactive checklist format:

1. PROCEDURE CHECKLIST:
   □ Step 1: [specific action]
   □ Step 2: [specific action]
   □ Step 3: [specific action]
   (Continue with detailed steps in chronological order)

2. PATIENT-SPECIFIC RISKS:
   Based on this patient's specific conditions:

   !RISK: [Risk 1 - Explain why this is a risk for this specific patient]
   • Required precautions
   • Specific monitoring needs

   !RISK: [Risk 2 - Explain why this is a risk for this specific patient]
   • Required precautions
   • Specific monitoring needs

   [Continue with all identified risks]

3. CRITICAL CHECKPOINTS:
   □ Pre-procedure vital signs acceptable
   □ Required equipment verified
   □ Patient consent obtained
   □ Site marking verified (if applicable)
   □ Time-out performed

4. EMERGENCY RESPONSE PLAN:
   If [specific complication] occurs:
   • Immediate action steps
   • Emergency contacts
   • Critical supplies location

[PROTOCOL: Relevant guideline name]

Remember to:
• Highlight any risk factors specific to this patient's conditions
• Provide clear go/no-go criteria
• Include specific monitoring parameters
• Note any medication adjustments needed"""

def create_patient_context(data):
    context = f"""
Patient Information:
- Age: {data.get('age')}
- Gender: {data.get('gender')}
- Chief Complaint: {data.get('chiefComplaint')}
- Vitals:
  * BP: {data.get('bp')}
  * HR: {data.get('heartRate')}
  * Temp: {data.get('temperature')}°F
  * SpO2: {data.get('spo2')}%
- Known Allergies: {data.get('allergies')}
- Medical History: {data.get('medicalHistory')}
- Previous Test Results: {data.get('testResults')}
- Current Medications: {data.get('medications')}

Query: {data.get('query')}
"""
    if data.get('consultationType') == 'procedure':
        context = f"Procedure Requested: {data.get('procedureName')}\n" + context
    return context 

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

@app.route('/launch')
def epic_launch():
    """Handle Epic SMART App Launch"""
    try:
        app.logger.info("Epic launch initiated")
        
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
        
        app.logger.info("Successfully exchanged launch token")
        
        # Store tokens securely in session
        session['epic_access_token'] = token_response['access_token']
        session['epic_patient_id'] = token_response.get('patient')
        session['epic_iss'] = iss
        
        if 'refresh_token' in token_response:
            session['epic_refresh_token'] = token_response['refresh_token']
        
        # Fetch patient context from Epic
        patient_data = fetch_epic_patient_data(
            token_response['access_token'],
            token_response['patient'],
            iss
        )
        
        # Store patient data in session
        session['epic_patient_data'] = patient_data
        
        app.logger.info(f"Epic patient data fetched for patient: {token_response['patient']}")
        
        # Redirect to main app with Epic context
        return redirect('/app?epic_patient=' + token_response['patient'])
        
    except Exception as e:
        app.logger.error(f"Error in Epic launch: {str(e)}")
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
    """Main app page with Epic integration"""
    epic_patient = request.args.get('epic_patient')
    epic_patient_data = session.get('epic_patient_data', {})
    
    if epic_patient_data:
        app.logger.info(f"Rendering app with Epic patient data for patient: {epic_patient}")
        return render_template('index.html', epic_patient_data=epic_patient_data)
    else:
        app.logger.info("Rendering app without Epic patient data")
        return render_template('index.html')

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