#!/usr/bin/env python3
"""
Healthcare AI Procedure Assistant
Clean version with role-based checklists and patient data integration
"""
import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
from logging.handlers import RotatingFileHandler
import openai
from typing import Dict

# Import role-based system
from role_based_checklist import RoleBasedChecklistGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced security configurations
app = Flask(__name__)
app.config.update(
    SESSION_COOKIE_SECURE=True,  # HTTPS in production
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///healthcare.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SECRET_KEY=os.getenv('SECRET_KEY', os.urandom(32))
)

# App Configuration
APP_CONFIG = {
    "app_name": "Healthcare AI Procedure Assistant",
    "version": "1.0.0",
    "description": "AI-powered healthcare procedure assistant with role-based checklists"
}

# Initialize role-based checklist generator
checklist_generator = RoleBasedChecklistGenerator()

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

# Database models
class ConsentTracking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50))
    consent_date = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))

class User(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    subscription_status = db.Column(db.String(20), default='trial')
    query_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_query = db.Column(db.DateTime)

# Consent check
@app.before_request
def check_consent():
    # Skip consent check for static files, privacy page, terms page, and consent submission
    if (request.endpoint in ['static', 'privacy', 'terms'] or 
        request.path == '/accept-consent'):
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

@app.route('/test')
def test():
    """Simple test endpoint to verify the server is working"""
    return jsonify({
        "status": "ok",
        "message": "Server is running",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/checklist', methods=['POST'])
def generate_checklist():
    """Generate role-based checklist"""
    try:
        data = request.get_json()
        procedure = data.get('procedure', 'General Procedure')
        role = data.get('role', 'Nurse')
        patient_data = data.get('patient_data', {})
        
        # Generate checklist using the role-based system
        checklist = checklist_generator.generate_checklist(
            procedure=procedure,
            role=role,
            patient_data=patient_data
        )
        
        return jsonify({
            'status': 'success',
            'checklist': checklist
        })
        
    except Exception as e:
        app.logger.error(f"Error generating checklist: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/risk-assessment', methods=['POST'])
def risk_assessment():
    """Generate risk assessment"""
    try:
        data = request.get_json()
        patient_data = data.get('patient_data', {})
        procedure = data.get('procedure', 'General')
        
        # Simple risk assessment logic
        risk_score = 0
        risk_factors = []
        
        age = patient_data.get('age', 50)
        if age > 65:
            risk_score += 2
            risk_factors.append('Advanced age')
        if age > 80:
            risk_score += 3
            risk_factors.append('Very advanced age')
            
        # Add more risk factors based on patient data
        if patient_data.get('diabetes'):
            risk_score += 2
            risk_factors.append('Diabetes')
        if patient_data.get('hypertension'):
            risk_score += 1
            risk_factors.append('Hypertension')
        if patient_data.get('heart_disease'):
            risk_score += 3
            risk_factors.append('Heart disease')
            
        # Determine risk level
        if risk_score >= 5:
            risk_level = 'High'
        elif risk_score >= 2:
            risk_level = 'Medium'
        else:
            risk_level = 'Low'
            
        # Generate recommendations
        recommendations = []
        if risk_level == 'High':
            recommendations.extend([
                'Consider additional monitoring',
                'Review with senior staff',
                'Ensure emergency protocols are ready'
            ])
        elif risk_level == 'Medium':
            recommendations.extend([
                'Monitor vital signs closely',
                'Ensure adequate hydration',
                'Review medications'
            ])
        else:
            recommendations.extend([
                'Standard monitoring',
                'Regular vital signs',
                'Patient comfort measures'
            ])
        
        assessment = {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'assessment': assessment
        })
        
    except Exception as e:
        app.logger.error(f"Error in risk assessment: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/roles', methods=['GET'])
def get_roles():
    """Get available healthcare roles"""
    try:
        roles = checklist_generator.get_supported_roles()
        return jsonify({
            'status': 'success',
            'roles': roles
        })
    except Exception as e:
        app.logger.error(f"Error getting roles: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@app.route('/accept-consent', methods=['POST'])
def accept_consent():
    """Accept privacy consent"""
    try:
        # Generate session ID if not exists
        if 'session_id' not in session:
            session['session_id'] = os.urandom(16).hex()
        
        # Store consent
        session['consent_accepted'] = True
        session['consent_date'] = datetime.utcnow().isoformat()
        
        # Log consent
        consent_record = ConsentTracking(
            session_id=session['session_id'],
            ip_address=request.remote_addr
        )
        db.session.add(consent_record)
        db.session.commit()
        
        app.logger.info(f"Consent accepted for session: {session['session_id']}")
        
        return jsonify({
            'status': 'success',
            'message': 'Consent accepted',
            'redirect': url_for('home')
        })
        
    except Exception as e:
        app.logger.error(f"Error accepting consent: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Enhanced AI chat endpoint with role-based responses"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        role = data.get('role', 'Unknown')
        procedure = data.get('procedure', 'General Procedure')
        patient_data = data.get('patient_data', {})
        
        # Generate detailed role-based response using the checklist generator
        if 'checklist' in message.lower() or 'procedure' in message.lower():
            # Use the role-based checklist generator for detailed responses
            checklist = checklist_generator.generate_checklist(
                procedure=procedure,
                role=role,
                patient_data=patient_data
            )
            
            # Format response with medical codes and detailed instructions
            response = format_detailed_medical_response(checklist, role, procedure, patient_data)
            
        elif 'risk' in message.lower():
            # Generate risk assessment
            risk_data = {
                'age': patient_data.get('age', 50),
                'gender': patient_data.get('gender', 'Unknown'),
                'vital_signs': {
                    'bp': patient_data.get('bp', '120/80'),
                    'hr': patient_data.get('hr', 70),
                    'temp': patient_data.get('temp', 98.6),
                    'spo2': patient_data.get('spo2', 98)
                },
                'medical_history': patient_data.get('medical_history', ''),
                'allergies': patient_data.get('allergies', ''),
                'medications': patient_data.get('medications', '')
            }
            
            response = generate_risk_assessment_response(risk_data, procedure)
            
        else:
            response = "I can provide detailed medical procedure checklists, risk assessments, and clinical guidance. Please specify a procedure and your role for comprehensive assistance."
        
        return jsonify({
            'status': 'success',
            'response': response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error in chat: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

def format_detailed_medical_response(checklist, role, procedure, patient_data):
    """Format detailed medical response with codes and references"""
    
    # Medical procedure codes mapping
    procedure_codes = {
        'resuscitation': {
            'cpt': '92950',  # CPR
            'icd10': 'Z51.11',  # Encounter for antineoplastic chemotherapy
            'snomed': '225358003'  # Cardiopulmonary resuscitation
        },
        'intubation': {
            'cpt': '31500',  # Intubation
            'icd10': 'Z51.11',
            'snomed': '172003'
        },
        'blood draw': {
            'cpt': '36415',  # Venipuncture
            'icd10': 'Z51.11',
            'snomed': '225158006'
        }
    }
    
    # Get codes for the procedure
    proc_lower = procedure.lower()
    codes = procedure_codes.get(proc_lower, {
        'cpt': 'N/A',
        'icd10': 'N/A', 
        'snomed': 'N/A'
    })
    
    response = f"""**Detailed Medical Procedure Guidelines for {role}**

**Procedure:** {procedure}
**Medical Codes:**
- CPT Code: {codes['cpt']}
- ICD-10: {codes['icd10']}
- SNOMED CT: {codes['snomed']}

**Role-Specific Responsibilities:**

{format_role_specific_instructions(role, procedure)}

**Pre-Procedure Checklist:**
{format_pre_procedure_checklist(role, procedure, patient_data)}

**Procedure Steps:**
{format_procedure_steps(role, procedure)}

**Post-Procedure Documentation:**
{format_documentation_requirements(role, procedure)}

**Safety Considerations:**
{format_safety_considerations(role, procedure, patient_data)}

**References:**
- AHA Guidelines for CPR and ECC
- Joint Commission Standards
- Facility-specific protocols
- Evidence-based practice guidelines

*This information is for licensed healthcare providers only. Always follow your facility's protocols and consult with supervising physicians as needed.*"""

    return response

def format_role_specific_instructions(role, procedure):
    """Generate role-specific instructions"""
    role_instructions = {
        'Paramedic': f"""
• Assess scene safety and patient condition
• Perform primary and secondary surveys
• Initiate appropriate interventions per protocol
• Monitor patient response and vital signs
• Coordinate with receiving facility
• Document all interventions and patient responses
• Maintain sterile technique when required
• Follow ALS protocols for {procedure}""",
        
        'ER Nurse': f"""
• Prepare patient and equipment for {procedure}
• Assist physician with procedure performance
• Monitor patient throughout procedure
• Document all observations and interventions
• Ensure patient comfort and safety
• Follow infection control protocols
• Coordinate with healthcare team""",
        
        'ICU Nurse': f"""
• Monitor hemodynamic parameters continuously
• Assess patient response to {procedure}
• Maintain invasive monitoring lines
• Document detailed patient status
• Coordinate with critical care team
• Follow ICU-specific protocols
• Ensure patient and family education"""
    }
    
    return role_instructions.get(role, f"""
• Follow standard protocols for {procedure}
• Ensure patient safety and comfort
• Document all activities accurately
• Communicate with healthcare team
• Monitor patient response
• Follow infection control measures""")

def format_pre_procedure_checklist(role, procedure, patient_data):
    """Generate pre-procedure checklist"""
    checklist = f"""
□ Verify patient identity (2 identifiers)
□ Confirm procedure consent
□ Check allergies and contraindications
□ Review patient medical history
□ Assess current vital signs
□ Prepare necessary equipment
□ Ensure sterile field if required
□ Brief team on procedure plan
□ Confirm patient understanding
□ Document pre-procedure assessment"""
    
    if patient_data.get('allergies'):
        checklist += f"\n□ **CRITICAL:** Patient has known allergies: {patient_data['allergies']}"
    
    if int(patient_data.get('age', 0)) > 65:
        checklist += f"\n□ **CRITICAL:** Advanced age - increased monitoring required"
    
    return checklist

def format_procedure_steps(role, procedure):
    """Generate procedure steps"""
    if 'resuscitation' in procedure.lower():
        return """
1. **Assess responsiveness** - Tap and shout
2. **Activate emergency response** - Call for help
3. **Check pulse and breathing** - 10 seconds max
4. **Begin CPR** - 30 compressions, 2 breaths
5. **Apply AED** - Follow voice prompts
6. **Continue cycles** - Until help arrives or patient recovers
7. **Monitor response** - Check for return of circulation
8. **Document interventions** - Time, response, medications"""
    
    return f"""
1. **Preparation** - Gather equipment and supplies
2. **Patient positioning** - Optimal position for {procedure}
3. **Sterile technique** - If required for procedure
4. **Procedure performance** - Follow established protocols
5. **Monitoring** - Continuous patient assessment
6. **Completion** - Ensure procedure goals met
7. **Post-procedure care** - Monitor and document
8. **Patient education** - Discharge instructions"""

def format_documentation_requirements(role, procedure):
    """Generate documentation requirements"""
    return f"""
• **Procedure note** - Detailed description of {procedure}
• **Vital signs** - Before, during, and after
• **Patient response** - Any adverse reactions
• **Medications administered** - Dosage, route, time
• **Equipment used** - Model, lot numbers if applicable
• **Complications** - Any issues encountered
• **Patient education** - Instructions provided
• **Follow-up plan** - Next steps and monitoring
• **Provider signature** - Legible name and credentials
• **Time documentation** - Start and end times"""

def format_safety_considerations(role, procedure, patient_data):
    """Generate safety considerations"""
    safety = f"""
• **Universal precautions** - PPE and infection control
• **Patient identification** - Verify before any intervention
• **Allergy verification** - Check all medications and materials
• **Contraindication review** - Assess for procedure risks
• **Emergency preparedness** - Know emergency protocols
• **Team communication** - Clear roles and responsibilities
• **Equipment check** - Verify functionality before use"""
    
    if patient_data.get('allergies'):
        safety += f"\n• **ALLERGY ALERT:** {patient_data['allergies']} - Avoid all related substances"
    
    if int(patient_data.get('age', 0)) > 65:
        safety += f"\n• **GERIATRIC CONSIDERATIONS:** Increased fall risk, medication sensitivity"
    
    return safety

def generate_risk_assessment_response(risk_data, procedure):
    """Generate detailed risk assessment"""
    age = risk_data.get('age', 50)
    vital_signs = risk_data.get('vital_signs', {})
    
    risk_score = 0
    risk_factors = []
    
    # Age-based risk
    if age > 65:
        risk_score += 2
        risk_factors.append(f"Advanced age ({age} years)")
    if age > 80:
        risk_score += 3
        risk_factors.append(f"Very advanced age ({age} years)")
    
    # Vital signs assessment
    bp = vital_signs.get('bp', '120/80')
    hr = vital_signs.get('hr', 70)
    temp = vital_signs.get('temp', 98.6)
    spo2 = vital_signs.get('spo2', 98)
    
    if hr > 100 or hr < 60:
        risk_score += 2
        risk_factors.append(f"Abnormal heart rate ({hr} bpm)")
    
    if temp > 100.4 or temp < 97:
        risk_score += 2
        risk_factors.append(f"Abnormal temperature ({temp}°F)")
    
    if spo2 < 95:
        risk_score += 3
        risk_factors.append(f"Low oxygen saturation ({spo2}%)")
    
    # Determine risk level
    if risk_score >= 5:
        risk_level = "HIGH"
        color = "🔴"
    elif risk_score >= 2:
        risk_level = "MEDIUM"
        color = "🟡"
    else:
        risk_level = "LOW"
        color = "🟢"
    
    return f"""**Comprehensive Risk Assessment for {procedure}**

**Risk Level:** {color} {risk_level} RISK (Score: {risk_score}/10)

**Risk Factors Identified:**
{chr(10).join([f"• {factor}" for factor in risk_factors]) if risk_factors else "• No significant risk factors identified"}

**Current Vital Signs:**
• Blood Pressure: {bp} mmHg
• Heart Rate: {hr} bpm
• Temperature: {temp}°F
• Oxygen Saturation: {spo2}%

**Recommendations:**
{generate_risk_recommendations(risk_level, risk_factors)}

**Monitoring Requirements:**
{generate_monitoring_requirements(risk_level)}

**Documentation Codes:**
• Risk Assessment: Z51.11
• Procedure Planning: Z51.12
• Patient Education: Z51.13

*This assessment is based on current clinical data and should be reviewed with supervising physician.*"""

def generate_risk_recommendations(risk_level, risk_factors):
    """Generate risk-based recommendations"""
    if risk_level == "HIGH":
        return """
• **IMMEDIATE PHYSICIAN CONSULTATION REQUIRED**
• Consider procedure postponement
• Implement enhanced monitoring protocols
• Prepare emergency response equipment
• Obtain additional consents if needed
• Consider alternative approaches
• Document all risk discussions with patient/family"""
    
    elif risk_level == "MEDIUM":
        return """
• **ENHANCED MONITORING RECOMMENDED**
• Review procedure with supervising physician
• Implement additional safety measures
• Consider pre-procedure optimization
• Ensure emergency equipment readily available
• Document risk discussion with patient"""
    
    else:
        return """
• **STANDARD MONITORING PROTOCOLS**
• Proceed with standard procedure protocols
• Maintain routine safety measures
• Document baseline assessment
• Provide standard patient education"""

def generate_monitoring_requirements(risk_level):
    """Generate monitoring requirements based on risk level"""
    if risk_level == "HIGH":
        return """
• **CONTINUOUS MONITORING REQUIRED**
• Continuous ECG monitoring
• Continuous pulse oximetry
• Blood pressure every 5 minutes
• Temperature monitoring
• Neurological checks every 15 minutes
• Emergency equipment at bedside
• Dedicated staff member for monitoring"""
    
    elif risk_level == "MEDIUM":
        return """
• **ENHANCED MONITORING**
• ECG monitoring throughout procedure
• Pulse oximetry continuous
• Blood pressure every 10 minutes
• Temperature checks
• Neurological assessment every 30 minutes
• Emergency equipment readily available"""
    
    else:
        return """
• **STANDARD MONITORING**
• Baseline vital signs
• Periodic vital sign checks
• Pulse oximetry as indicated
• Routine safety monitoring
• Standard emergency preparedness"""

if __name__ == '__main__':
    print("Starting Healthcare AI Procedure Assistant...")
    print("Visit: http://localhost:5000")
    # Disable Flask's automatic .env loading
    import os
    os.environ['FLASK_SKIP_DOTENV'] = '1'
    app.run(debug=True, host='0.0.0.0', port=5000)
