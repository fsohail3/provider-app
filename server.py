import os
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
from openai import OpenAI
import stripe
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

load_dotenv()  # This will work locally but skip if file not found

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4-turbo-preview")
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    email = db.Column(db.String(120), unique=True)
    query_count = db.Column(db.Integer, default=0)
    subscription_status = db.Column(db.String(20), default='trial')
    subscription_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
For each case:
1. List possible diagnoses with ICD-10 codes (format: • Diagnosis (ICD-10))
2. Recommend specific tests with CPT codes (format: • Test (CPT))
3. Highlight key risk factors with '!RISK:' prefix
4. Reference relevant clinical guidelines with '[PROTOCOL: guideline name]'
5. Use bullet points (•) instead of checkboxes for all lists
6. Consider patient's allergies and previous test results in your assessment"""
    else:
        return """You are a medical AI assistant helping healthcare providers with procedures. 
For each case:
1. List pre-procedure requirements using bullet points (•)
2. List contraindications with '!RISK:' prefix
3. Reference relevant protocols with '[PROTOCOL: protocol name]'
4. List specific monitoring requirements using bullet points (•)
5. List post-procedure care instructions using bullet points (•)
6. Consider patient's allergies and medical history in your recommendations"""

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