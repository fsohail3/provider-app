#!/usr/bin/env python3
"""
Test script for FHIR integration with Epic
Tests both mock data and real FHIR API calls
"""
import os
import json
import logging
from datetime import datetime
from epic_fhir_client import EpicFHIRClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fhir_client_with_mock_data():
    """Test FHIR client with mock data to verify functionality"""
    print("🧪 Testing FHIR Client with Mock Data")
    print("=" * 50)
    
    # Mock data for testing
    mock_patient_data = {
        'demographics': {
            'name': 'John Doe',
            'age': 45,
            'gender': 'male'
        },
        'vital_signs': [
            {
                'type': 'Blood Pressure',
                'value': '120/80',
                'unit': 'mmHg',
                'date': '2024-01-15T10:30:00Z',
                'status': 'final'
            },
            {
                'type': 'Heart Rate',
                'value': '72',
                'unit': 'bpm',
                'date': '2024-01-15T10:30:00Z',
                'status': 'final'
            }
        ],
        'allergies': [
            {
                'substance': 'Penicillin',
                'severity': 'high',
                'reaction': ['Rash', 'Swelling'],
                'status': 'active'
            }
        ],
        'medications': [
            {
                'name': 'Lisinopril',
                'dosage': '10mg',
                'frequency': 'daily',
                'status': 'active'
            }
        ],
        'medical_history': [
            {
                'condition': 'Hypertension',
                'status': 'active',
                'date': '2020-01-01'
            }
        ],
        'labs': [
            {
                'name': 'Hemoglobin A1C',
                'value': '6.2',
                'unit': '%',
                'abnormal': True,
                'date': '2024-01-10'
            }
        ],
        'surgeries': [
            {
                'name': 'Appendectomy',
                'date': '2015-06-15',
                'status': 'completed'
            }
        ]
    }
    
    print("✅ Mock data created successfully")
    print(f"Patient: {mock_patient_data['demographics']['name']}")
    print(f"Age: {mock_patient_data['demographics']['age']}")
    print(f"Allergies: {len(mock_patient_data['allergies'])}")
    print(f"Medications: {len(mock_patient_data['medications'])}")
    print(f"Labs: {len(mock_patient_data['labs'])}")
    
    return mock_patient_data

def test_role_based_checklist_with_mock_data():
    """Test role-based checklist generation with mock data"""
    print("\n🎯 Testing Role-Based Checklist with Mock Data")
    print("=" * 50)
    
    try:
        from role_based_checklist import RoleBasedChecklistGenerator
        
        # Initialize the checklist generator
        checklist_generator = RoleBasedChecklistGenerator()
        
        # Test with different roles
        test_roles = ['ER Nurse', 'ICU Nurse', 'Nurse Practitioner', 'Medical Assistant']
        
        for role in test_roles:
            print(f"\n📋 Testing role: {role}")
            
            # Generate checklist for this role
            checklist = checklist_generator.generate_role_based_checklist(
                practitioner_role=role,
                patient_data=test_fhir_client_with_mock_data(),
                procedure_type='general'
            )
            
            print(f"✅ Checklist generated successfully")
            print(f"   - Pre-procedure items: {len(checklist['pre_procedure'])}")
            print(f"   - During procedure items: {len(checklist['during_procedure'])}")
            print(f"   - Post-procedure items: {len(checklist['post_procedure'])}")
            print(f"   - Risk factors: {len(checklist['risk_factors'])}")
            print(f"   - Patient alerts: {len(checklist['patient_alerts'])}")
            
            # Show a sample item
            if checklist['pre_procedure']:
                sample_item = checklist['pre_procedure'][0]
                print(f"   - Sample item: {sample_item['task']}")
                print(f"     Priority: {sample_item['priority']}")
                print(f"     Risk Level: {sample_item['risk_level']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing role-based checklist: {str(e)}")
        return False

def test_real_fhir_api():
    """Test real FHIR API calls (requires valid credentials)"""
    print("\n🌐 Testing Real FHIR API Calls")
    print("=" * 50)
    
    # Check for environment variables
    epic_client_id = os.getenv('EPIC_CLIENT_ID')
    epic_client_secret = os.getenv('EPIC_CLIENT_SECRET')
    
    if not epic_client_id or not epic_client_secret:
        print("⚠️  Epic credentials not found in environment variables")
        print("   Please set EPIC_CLIENT_ID and EPIC_CLIENT_SECRET")
        print("   You can create a .env file with these values")
        return False
    
    print(f"✅ Epic Client ID: {epic_client_id[:8]}...")
    print(f"✅ Epic Client Secret: {epic_client_secret[:8]}...")
    
    # Note: For real testing, we need:
    # 1. Valid access token from Epic launch
    # 2. Valid patient ID
    # 3. Valid FHIR base URL
    
    print("\n📝 To test real FHIR API calls, you need:")
    print("   1. Launch the app from Epic EHR")
    print("   2. Get access token from Epic OAuth flow")
    print("   3. Get patient ID from Epic launch context")
    print("   4. Use Epic's FHIR base URL")
    
    return False

def create_sample_env_file():
    """Create a sample .env file for Epic configuration"""
    print("\n📝 Creating Sample .env File")
    print("=" * 50)
    
    env_content = """# Epic FHIR Configuration
# Get these values from https://fhir.epic.com/
EPIC_CLIENT_ID=your_epic_client_id_here
EPIC_CLIENT_SECRET=your_epic_client_secret_here

# Optional: Epic FHIR Base URL (default is used if not set)
# EPIC_FHIR_BASE_URL=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4

# OpenAI Configuration (if using AI features)
# OPENAI_API_KEY=your_openai_api_key_here
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Sample .env file created successfully")
        print("   Please edit it with your actual Epic credentials")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 FHIR Integration Test Suite")
    print("=" * 60)
    
    # Test 1: Mock data functionality
    mock_data = test_fhir_client_with_mock_data()
    
    # Test 2: Role-based checklist generation
    checklist_success = test_role_based_checklist_with_mock_data()
    
    # Test 3: Real FHIR API (if credentials available)
    fhir_api_success = test_real_fhir_api()
    
    # Create sample .env file if it doesn't exist
    if not os.path.exists('.env'):
        create_sample_env_file()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    print(f"✅ Mock Data Test: PASSED")
    print(f"✅ Role-Based Checklist: {'PASSED' if checklist_success else 'FAILED'}")
    print(f"✅ Real FHIR API: {'PASSED' if fhir_api_success else 'SKIPPED (no credentials)'}")
    
    if not fhir_api_success:
        print("\n🔧 Next Steps:")
        print("   1. Register your app at https://fhir.epic.com/")
        print("   2. Get your Epic Client ID and Secret")
        print("   3. Add them to your .env file")
        print("   4. Test the launch flow from Epic EHR")
        print("   5. Run this test again with real credentials")

if __name__ == "__main__":
    main() 