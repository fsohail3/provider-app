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
    """AI chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        # Simple AI response (you can enhance this with OpenAI)
        if 'checklist' in message.lower():
            response = "I can help you generate role-based checklists for medical procedures. Please specify the procedure and your role."
        elif 'risk' in message.lower():
            response = "I can help assess patient risk factors. Please provide patient information and the planned procedure."
        else:
            response = "I'm here to help with healthcare procedures, checklists, and risk assessments. How can I assist you today?"
        
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

if __name__ == '__main__':
    print("Starting Healthcare AI Procedure Assistant...")
    print("Visit: http://localhost:5000")
    # Disable Flask's automatic .env loading
    import os
    os.environ['FLASK_SKIP_DOTENV'] = '1'
    app.run(debug=True, host='0.0.0.0', port=5000)
