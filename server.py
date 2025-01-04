from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
import base64
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import httpx
from medical_database import MedicalKnowledgeBase
from risk_assessment import RiskAssessment
from checklist_generator import ChecklistGenerator
import requests

load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://provider-app.onrender.com",
            "http://localhost:8000"
        ]
    }
})

class MedicalAssistant:
    def __init__(self):
        self.medical_db = MedicalKnowledgeBase()
        self.risk_assessor = RiskAssessment(self.medical_db)
        self.checklist_generator = ChecklistGenerator(self.medical_db, self.risk_assessor)
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    async def handle_query(self, query_type, data, images=None):
        """Handle both diagnosis and procedure queries"""
        try:
            if query_type == "procedure":
                return await self.handle_procedure_query(data)
            else:
                return await self.handle_diagnosis_query(data, images)
        except Exception as e:
            print(f"Error handling query: {str(e)}")
            return {"error": str(e)}

    async def handle_procedure_query(self, data):
        """Handle procedure guidance requests"""
        procedure_type = data.get('type')
        patient_info = data.get('patientInfo', {})
        
        # Get comprehensive procedure guidance
        guidance = await self.medical_db.get_procedure_guidance(procedure_type, patient_info)
        
        # Get AI insights for patient-specific considerations
        ai_insights = await self._get_ai_insights(procedure_type, patient_info)
        
        return {
            'procedure_guidance': guidance,
            'ai_insights': ai_insights,
            'alerts': self._generate_alerts(guidance['risks'], patient_info)
        }

    async def handle_diagnosis_query(self, data, images=None):
        """Handle diagnostic queries"""
        # Existing diagnosis logic...
        pass

    async def _get_ai_insights(self, procedure_type, patient_info):
        """Get AI-powered insights for procedure and patient combination"""
        prompt = self._create_procedure_prompt(procedure_type, patient_info)
        
        response = await self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert medical assistant providing guidance on medical procedures."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content

    def _create_procedure_prompt(self, procedure_type, patient_info):
        """Create detailed prompt for procedure guidance"""
        return f"""
        Provide detailed guidance for {procedure_type} considering the following patient factors:
        Age: {patient_info.get('age')}
        Weight: {patient_info.get('weight')}
        Medical History: {patient_info.get('medicalHistory')}
        Current Medications: {patient_info.get('currentMedications')}
        Allergies: {patient_info.get('allergies')}
        Vital Signs: {patient_info.get('vitals')}

        Please include:
        1. Patient-specific considerations
        2. Risk factors and contraindications
        3. Modified steps if needed for this patient
        4. Special monitoring requirements
        5. Potential complications to watch for
        """

    def _generate_alerts(self, risks, patient_info):
        """Generate relevant alerts based on risks and patient factors"""
        alerts = []
        
        # Check for high-priority risks
        if risks.get('contraindications'):
            for contra in risks['contraindications']:
                alerts.append({
                    'severity': 'high',
                    'message': f"CONTRAINDICATION: {contra}"
                })

        # Check patient-specific risks
        for risk in risks.get('patient_specific', []):
            alerts.append({
                'severity': 'medium',
                'message': f"Patient Risk Factor: {risk}"
            })

        return alerts

@app.route('/query', methods=['POST'])
async def handle_query():
    try:
        data = json.loads(request.form['data'])
        query_type = request.form.get('queryType', 'diagnosis')
        
        # Handle image uploads
        images = []
        for key in request.files:
            file = request.files[key]
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                with open(filepath, "rb") as image_file:
                    images.append({
                        "name": filename,
                        "data": base64.b64encode(image_file.read()).decode('utf-8')
                    })
                os.remove(filepath)

        medical_assistant = MedicalAssistant()
        result = await medical_assistant.handle_query(query_type, data, images)
        
        return jsonify(result)
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "api_status": {
            "pubmed": check_api_status("pubmed"),
            "uptodate": check_api_status("uptodate"),
            "clinicaltrials": check_api_status("clinicaltrials")
        }
    })

def check_api_status(api_name):
    """Check if an API is responding"""
    try:
        medical_db = MedicalKnowledgeBase()
        if api_name == "pubmed":
            response = requests.get(f"{medical_db.api_endpoints['pubmed']}einfo.fcgi")
        elif api_name == "uptodate":
            response = requests.get(
                f"{medical_db.api_endpoints['uptodate']}status",
                headers={"Authorization": f"Bearer {medical_db.api_keys['uptodate']}"}
            )
        elif api_name == "clinicaltrials":
            response = requests.get(f"{medical_db.api_endpoints['clinicaltrials']}info")
        
        return "available" if response.status_code == 200 else "unavailable"
    except:
        return "unavailable"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)