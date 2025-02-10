import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from dotenv import load_dotenv
from openai import OpenAI
import stripe
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, String
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from logging.handlers import RotatingFileHandler
import json
from enum import Enum
import re

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
    SECRET_KEY=os.urandom(32),
    MINIMUM_PASSWORD_LENGTH=8,
    REQUIRE_SPECIAL_CHARS=True,
    DATA_ENCRYPTION_REQUIRED=True
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
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Add after imports
from enum import Enum
import re
from datetime import datetime, timedelta

class StateSecurityRequirements(Enum):
    CA = {
        'password_length': 12,
        'special_chars': True,
        'numbers': True,
        'uppercase': True,
        'max_login_attempts': 5,
        'lockout_duration': 30,  # minutes
        'session_timeout': 15,  # minutes
        'encryption_standard': 'AES-256',
        'data_retention': 7 * 365,  # days
        'breach_notification': 15,  # days
    }
    NY = {
        'password_length': 8,
        'special_chars': True,
        'numbers': True,
        'uppercase': True,
        'max_login_attempts': 3,
        'lockout_duration': 60,
        'session_timeout': 20,
        'encryption_standard': 'AES-256',
        'data_retention': 6 * 365,
        'breach_notification': 30,
    }
    TX = {
        'password_length': 10,
        'special_chars': True,
        'numbers': True,
        'uppercase': True,
        'max_login_attempts': 4,
        'lockout_duration': 45,
        'session_timeout': 30,
        'encryption_standard': 'AES-256',
        'data_retention': 5 * 365,
        'breach_notification': 45,
    }
    FL = {
        'password_length': 8,
        'special_chars': True,
        'numbers': True,
        'uppercase': True,
        'max_login_attempts': 5,
        'lockout_duration': 30,
        'session_timeout': 20,
        'encryption_standard': 'AES-256',
        'data_retention': 5 * 365,
        'breach_notification': 30,
    }

class SecurityEnforcer:
    def __init__(self, state):
        self.requirements = StateSecurityRequirements[state].value
        
    def validate_password(self, password):
        if len(password) < self.requirements['password_length']:
            return False, f"Password must be at least {self.requirements['password_length']} characters"
        
        if self.requirements['special_chars'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain special characters"
            
        if self.requirements['numbers'] and not re.search(r'\d', password):
            return False, "Password must contain numbers"
            
        if self.requirements['uppercase'] and not re.search(r'[A-Z]', password):
            return False, "Password must contain uppercase letters"
            
        return True, "Password meets requirements"

# Enhanced User model with encryption
class User(UserMixin, db.Model):
    id = db.Column(db.String(50), primary_key=True)
    email = db.Column(EncryptedType(), unique=True)
    password_hash = db.Column(db.String(200))
    state = db.Column(db.String(2))  # Two-letter state code
    failed_login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime)
    account_locked_until = db.Column(db.DateTime)
    query_count = db.Column(db.Integer, default=0)
    subscription_status = db.Column(db.String(20), default='trial')
    subscription_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Audit fields
    access_logs = db.relationship('AccessLog', backref='user', lazy='dynamic')

    def is_account_locked(self):
        if self.account_locked_until and self.account_locked_until > datetime.utcnow():
            return True
        return False
    
    def increment_failed_login(self):
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.utcnow()
        
        security = SecurityEnforcer(self.state)
        if self.failed_login_attempts >= security.requirements['max_login_attempts']:
            self.account_locked_until = datetime.utcnow() + timedelta(
                minutes=security.requirements['lockout_duration']
            )
        
        db.session.commit()

# Audit logging model
class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'))
    action = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))
    details = db.Column(EncryptedType())

# Add California-specific consent
class CaliforniaConsent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'))
    ccpa_consent = db.Column(db.Boolean, default=False)
    cmia_consent = db.Column(db.Boolean, default=False)
    consent_date = db.Column(db.DateTime, default=datetime.utcnow)

# Add Texas-specific data retention
class DataRetention(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_type = db.Column(db.String(50))
    retention_period = db.Column(db.Integer)  # in days
    deletion_date = db.Column(db.DateTime)

def log_access(action, details=None):
    if current_user.is_authenticated:
        log = AccessLog(
            user_id=current_user.id,
            action=action,
            ip_address=request.remote_addr,
            details=json.dumps(details) if details else None
        )
        db.session.add(log)
        db.session.commit()

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        # Get or create user session ID
        user_id = session.get('user_id')
        if not user_id:
            user_id = os.urandom(16).hex()
            session['user_id'] = user_id

        # Check subscription status
        user = User.query.get(user_id)
        if not user:
            user = User(id=user_id, subscription_status='trial', query_count=0)
            db.session.add(user)
            db.session.commit()

        if user.subscription_status != 'active' and user.query_count >= 10:
            return jsonify({
                "response": "Trial limit reached",
                "show_payment": True
            })

        # Get request data
        data = request.json
        consultation_type = data.get('consultationType')
        
        # Create messages array
        messages = [{"role": "system", "content": create_system_prompt(consultation_type)}]
        
        chat_history = data.get('chatHistory', [])
        if chat_history:
            messages.extend(chat_history[-4:])
        
        messages.append({
            "role": "user",
            "content": create_patient_context(data)
        })

        # Make OpenAI API call
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7
        )
        
        # Update query count for trial users
        if user.subscription_status == 'trial':
            user.query_count += 1
            db.session.commit()

        response_data = {
            "response": completion.choices[0].message.content,
            "queries_remaining": 10 - user.query_count if user.subscription_status == 'trial' else None
        }
        
        return jsonify(response_data)

    except Exception as e:
        print(f"Error in chat route: {str(e)}")
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

@app.before_request
def check_consent():
    if not current_user.is_authenticated and request.endpoint not in ['login', 'static', 'privacy', 'terms']:
        return redirect(url_for('login')) 

# Add Florida breach notification requirements
def florida_breach_notification(breach_data):
    if any(user.state == 'FL' for user in affected_users):
        notify_within_days = 30
        notify_if_affected_users_exceed = 500 

# Update login route to use state-specific security
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user:
            if user.is_account_locked():
                flash('Account is temporarily locked. Please try again later.')
                return render_template('login.html')
            
            if check_password_hash(user.password_hash, password):
                user.failed_login_attempts = 0
                user.last_login = datetime.utcnow()
                db.session.commit()
                login_user(user)
                
                # Set session timeout based on state requirements
                security = SecurityEnforcer(user.state)
                session.permanent = True
                app.permanent_session_lifetime = timedelta(
                    minutes=security.requirements['session_timeout']
                )
                
                return redirect(url_for('home'))
            else:
                user.increment_failed_login()
                flash('Invalid password.')
        else:
            flash('Email not found.')
            
    return render_template('login.html')

# Add security middleware
@app.before_request
def security_middleware():
    if current_user.is_authenticated:
        # Check session timeout
        security = SecurityEnforcer(current_user.state)
        session_age = datetime.utcnow() - datetime.fromtimestamp(session.get('_created', 0))
        if session_age > timedelta(minutes=security.requirements['session_timeout']):
            logout_user()
            flash('Session expired. Please login again.')
            return redirect(url_for('login')) 