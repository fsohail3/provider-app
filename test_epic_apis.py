#!/usr/bin/env python3
"""
Test script for Epic FHIR APIs to understand data structure
"""
import requests
import json
import os
from datetime import datetime

# Epic FHIR Configuration
EPIC_CONFIG = {
    "client_id": os.getenv('EPIC_CLIENT_ID'),
    "client_secret": os.getenv('EPIC_CLIENT_SECRET'),
    "fhir_base_url": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
}

def test_epic_api(access_token, patient_id, resource_type, params=None):
    """Test a specific Epic FHIR API endpoint"""
    try:
        url = f"{EPIC_CONFIG['fhir_base_url']}/{resource_type}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/fhir+json'
        }
        
        # Add patient filter
        if params is None:
            params = {}
        params['patient'] = patient_id
        
        print(f"\n🔍 Testing: {resource_type}")
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        response = requests.get(url, headers=headers, params=params)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total', 0)} resources")
            
            # Show sample data structure
            if 'entry' in data and len(data['entry']) > 0:
                sample = data['entry'][0]['resource']
                print(f"Sample data structure:")
                print(json.dumps(sample, indent=2)[:500] + "...")
            else:
                print("No data returned")
                
            return data
        else:
            print(f"❌ Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_all_epic_apis():
    """Test all the Epic FHIR APIs we need"""
    print("🚀 Testing Epic FHIR APIs")
    print("=" * 50)
    
    # Note: This is a test script - in real implementation, we'll get access_token from Epic launch
    # For now, we'll just test the API structure
    
    # Test APIs in order of priority
    test_apis = [
        # 1. Vital Signs
        ("Observation", {"category": "vital-signs"}),
        
        # 2. Medical History (Conditions)
        ("Condition", {"category": "problem-list-item"}),
        
        # 3. Reason for Visit
        ("Condition", {"category": "encounter-diagnosis"}),
        
        # 4. Medications
        ("MedicationRequest", {}),
        
        # 5. Labs
        ("Observation", {"category": "laboratory"}),
        
        # 6. Patient Reported Surgical History
        ("Procedure", {"category": "patient-reported-surgical-history"}),
        
        # 7. Surgeries
        ("Procedure", {"category": "surgery"}),
        
        # 8. Demographics
        ("Patient", {}),
        
        # 9. Clinical Notes
        ("DocumentReference", {"type": "clinical-notes"}),
        
        # 10. Practitioner Role
        ("PractitionerRole", {}),
        
        # 11. Allergies
        ("AllergyIntolerance", {}),
        
        # 12. Appointments
        ("Appointment", {}),
        
        # 13. Social Determinants
        ("Observation", {"category": "social-history"}),
        
        # 14. Family History
        ("Observation", {"category": "family-history"}),
    ]
    
    print("📋 API Test Plan:")
    for i, (resource, params) in enumerate(test_apis, 1):
        print(f"{i:2d}. {resource} - {params}")
    
    print("\n" + "=" * 50)
    print("Note: This test script shows the API structure.")
    print("In real implementation, access_token comes from Epic launch.")
    print("=" * 50)

if __name__ == "__main__":
    test_all_epic_apis() 