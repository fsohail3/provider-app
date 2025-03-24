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