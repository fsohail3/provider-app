ffrom flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
import base64
from werkzeug.utils import secure_filename
import os
from medical_rag import MedicalRAG
from medical_database import MedicalKnowledgeBase

# Initialize knowledge base and RAG
knowledge_base = MedicalKnowledgeBase()
knowledge_base.load_medical_data()
medical_rag = MedicalRAG(knowledge_base)

app = Flask(__name__)

# Replace it with:
CORS(app, resources={
    r"/*": {
        "origins": "*",  # In production, replace with your frontend domain
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

client = OpenAI(api_key="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")

@app.route('/diagnose', methods=['POST', 'OPTIONS'])
def diagnose():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
        
    try:
        # Get JSON data
        data = json.loads(request.form['data'])
        
        # Handle image uploads (keeping your existing image handling)
        image_descriptions = []
        for key in request.files:
            # ... your existing image processing code ...

        # Construct prompt with image descriptions
        image_analysis = "\n\nImage Analysis:\n" + "\n".join(image_descriptions) if image_descriptions else ""
        
        # Add image analysis to the data for RAG
        data['additional_info'] = data.get('additionalInfo', '') + image_analysis

        # Get RAG-based diagnosis with citations
        diagnosis_result = medical_rag.get_diagnosis(data)
        
        return jsonify(diagnosis_result)
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)