from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import json
import base64
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Change the OpenAI initialization
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/diagnose', methods=['POST', 'OPTIONS'])
def diagnose():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
        
    try:
        # Get JSON data
        data = json.loads(request.form['data'])
        
        # Handle image uploads
        image_descriptions = []
        for key in request.files:
            file = request.files[key]
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Use OpenAI's vision model to analyze the image
                try:
                    with open(filepath, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                        
                    vision_response = openai.ChatCompletion.create(
                        model="gpt-4-vision-preview",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Please describe any visible medical symptoms or conditions in this image, focusing on relevant clinical observations."},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}"
                                        }
                                    }
                                ]
                            }
                        ]
                    )
                    image_descriptions.append(vision_response.choices[0].message['content'])
                except Exception as e:
                    print(f"Error analyzing image: {str(e)}")
                    image_descriptions.append(f"Error analyzing image: {str(e)}")
                
                # Clean up uploaded file
                os.remove(filepath)

        # Construct prompt with image descriptions
        image_analysis = "\n\nImage Analysis:\n" + "\n".join(image_descriptions) if image_descriptions else ""
        
        prompt = f"""Given the following patient information:
Age: {data.get('age', 'N/A')}
Gender: {data.get('gender', 'N/A')}
Symptoms: {data.get('symptoms', 'N/A')}
Duration: {data.get('duration', 'N/A')}
Additional Info: {data.get('additionalInfo', 'N/A')}
{image_analysis}

Please provide:
1. Possible diagnoses (ranked by likelihood)
2. Recommended diagnostic tests for confirmation
3. Scientific references supporting these diagnoses
4. Red flags to watch for
5. Differential diagnoses to consider"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert pediatric diagnostic assistant. Provide evidence-based medical insights while always noting that final diagnosis should be made by a qualified healthcare provider."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return jsonify({"diagnosis": response.choices[0].message['content']})
    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)