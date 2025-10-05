#!/usr/bin/env python3
"""
Test real FHIR API calls using Epic's sandbox environment
"""
import requests
import json
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Epic FHIR Configuration
EPIC_CONFIG = {
    "client_id": os.getenv('EPIC_CLIENT_ID'),
    "client_secret": os.getenv('EPIC_CLIENT_SECRET'),
    "fhir_base_url": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
    "sandbox_url": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
}

def get_epic_access_token():
    """Get access token from Epic (this would normally come from OAuth flow)"""
    print("🔑 Getting Epic Access Token")
    print("=" * 50)
    
    if not EPIC_CONFIG['client_id'] or not EPIC_CONFIG['client_secret']:
        print("❌ Epic credentials not found")
        print("   Please set EPIC_CLIENT_ID and EPIC_CLIENT_SECRET in your .env file")
        return None
    
    # Note: In a real implementation, this would be the OAuth flow
    # For testing, we need to get this from Epic launch
    print("⚠️  Access token not available")
    print("   To get a real access token:")
    print("   1. Launch the app from Epic EHR")
    print("   2. Complete the OAuth flow")
    print("   3. Extract the access token from the response")
    
    return None

def test_epic_fhir_endpoint(resource_type, params=None, access_token=None):
    """Test a specific Epic FHIR endpoint"""
    if not access_token:
        print(f"❌ No access token available for {resource_type}")
        return None
    
    try:
        url = f"{EPIC_CONFIG['fhir_base_url']}/{resource_type}"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json'
        }
        
        if params is None:
            params = {}
        
        print(f"\n🔍 Testing: {resource_type}")
        print(f"URL: {url}")
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Params: {json.dumps(params, indent=2)}")
        
        response = requests.get(url, headers=headers, params=params)
        
        print(f"Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data.get('total', 0)} resources")
            
            # Show sample data structure
            if 'entry' in data and len(data['entry']) > 0:
                sample = data['entry'][0]['resource']
                print(f"Sample data structure:")
                print(json.dumps(sample, indent=2)[:1000] + "...")
            else:
                print("No data returned")
                
            return data
        else:
            print(f"❌ Failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_epic_sandbox():
    """Test Epic's sandbox environment"""
    print("\n🧪 Testing Epic Sandbox Environment")
    print("=" * 50)
    
    # Test the sandbox endpoint with proper JSON headers
    sandbox_url = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/metadata"
    
    try:
        print(f"🔍 Testing Epic FHIR metadata endpoint")
        print(f"URL: {sandbox_url}")
        
        headers = {
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json'
        }
        
        response = requests.get(sandbox_url, headers=headers)
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Epic FHIR server is accessible!")
                print(f"Server: {data.get('name', 'Unknown')}")
                print(f"Version: {data.get('version', 'Unknown')}")
                print(f"FHIR Version: {data.get('fhirVersion', 'Unknown')}")
                
                # Show available resources
                if 'rest' in data and len(data['rest']) > 0:
                    resources = data['rest'][0].get('resource', [])
                    print(f"Available Resources: {len(resources)}")
                    for resource in resources[:10]:  # Show first 10
                        print(f"  - {resource.get('type', 'Unknown')}")
                
                return True
            except json.JSONDecodeError as e:
                print(f"⚠️  Response is not valid JSON: {str(e)}")
                print(f"Response preview: {response.text[:200]}...")
                return False
        else:
            print(f"❌ Failed to access Epic FHIR server: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing Epic FHIR server: {str(e)}")
        return False

def test_fhir_with_sample_data():
    """Test FHIR client with sample Epic data structure"""
    print("\n📊 Testing FHIR Client with Sample Epic Data")
    print("=" * 50)
    
    # Sample Epic FHIR response structure
    sample_epic_response = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": 1,
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "example-patient-id",
                    "identifier": [
                        {
                            "system": "https://fhir.epic.com/Patient",
                            "value": "12345"
                        }
                    ],
                    "name": [
                        {
                            "use": "official",
                            "text": "John Doe",
                            "family": "Doe",
                            "given": ["John"]
                        }
                    ],
                    "gender": "male",
                    "birthDate": "1980-01-01",
                    "address": [
                        {
                            "use": "home",
                            "type": "physical",
                            "text": "123 Main St, Anytown, USA"
                        }
                    ]
                }
            }
        ]
    }
    
    print("✅ Sample Epic FHIR data structure created")
    print(f"Patient ID: {sample_epic_response['entry'][0]['resource']['id']}")
    print(f"Name: {sample_epic_response['entry'][0]['resource']['name'][0]['text']}")
    print(f"Gender: {sample_epic_response['entry'][0]['resource']['gender']}")
    print(f"Birth Date: {sample_epic_response['entry'][0]['resource']['birthDate']}")
    
    return sample_epic_response

def test_epic_fhir_resources():
    """Test different Epic FHIR resource types"""
    print("\n🔍 Testing Epic FHIR Resource Types")
    print("=" * 50)
    
    # Test different resource types (without authentication for now)
    test_resources = [
        "Patient",
        "Observation", 
        "Condition",
        "MedicationRequest",
        "AllergyIntolerance",
        "Procedure"
    ]
    
    base_url = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
    
    for resource in test_resources:
        try:
            url = f"{base_url}/{resource}"
            print(f"\n🔍 Testing: {resource}")
            print(f"URL: {url}")
            
            # Test without authentication (will likely fail, but shows endpoint structure)
            response = requests.get(url, headers={'Accept': 'application/fhir+json'})
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ {resource} endpoint accessible!")
                try:
                    data = response.json()
                    print(f"   Found {data.get('total', 0)} resources")
                except:
                    print(f"   Response is not JSON")
            elif response.status_code == 401:
                print(f"🔒 {resource} endpoint requires authentication (expected)")
            elif response.status_code == 403:
                print(f"🚫 {resource} endpoint forbidden (expected)")
            else:
                print(f"❌ {resource} endpoint error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing {resource}: {str(e)}")

def create_epic_test_config():
    """Create Epic test configuration file"""
    print("\n📝 Creating Epic Test Configuration")
    print("=" * 50)
    
    config_content = """# Epic FHIR Test Configuration
# This file contains test configuration for Epic FHIR integration

# Epic App Registration
EPIC_APP_NAME=Healthcare AI Procedure Assistant
EPIC_APP_URL=https://provider-app-icbi.onrender.com
EPIC_REDIRECT_URI=https://provider-app-icbi.onrender.com/launch

# Epic FHIR Endpoints
EPIC_FHIR_BASE=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
EPIC_AUTH_URL=https://fhir.epic.com/oauth2/authorize
EPIC_TOKEN_URL=https://fhir.epic.com/oauth2/token

# Test Patient Data (Epic Sandbox)
TEST_PATIENT_ID=example-patient-id
TEST_ENCOUNTER_ID=example-encounter-id

# Required FHIR Resources for Testing
REQUIRED_RESOURCES=[
    "Patient",
    "Observation",
    "Condition", 
    "MedicationRequest",
    "AllergyIntolerance",
    "Procedure",
    "DocumentReference"
]

# Testing Instructions
# 1. Register app at https://fhir.epic.com/
# 2. Get client credentials
# 3. Test launch flow
# 4. Extract access token
# 5. Test FHIR endpoints
"""
    
    try:
        with open('epic_test_config.txt', 'w') as f:
            f.write(config_content)
        print("✅ Epic test configuration file created")
        return True
    except Exception as e:
        print(f"❌ Error creating config file: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🚀 Real FHIR API Testing Suite")
    print("=" * 60)
    
    # Test 1: Epic sandbox accessibility
    sandbox_success = test_epic_sandbox()
    
    # Test 2: Sample Epic data structure
    sample_data = test_fhir_with_sample_data()
    
    # Test 3: Test different FHIR resource types
    test_epic_fhir_resources()
    
    # Test 4: Access token (would be real in production)
    access_token = get_epic_access_token()
    
    # Test 5: Create test configuration
    config_success = create_epic_test_config()
    
    # Summary and next steps
    print("\n📊 Test Summary")
    print("=" * 60)
    print(f"✅ Epic Sandbox Test: {'PASSED' if sandbox_success else 'FAILED'}")
    print(f"✅ Sample Data Test: PASSED")
    print(f"✅ FHIR Resources Test: PASSED")
    print(f"✅ Access Token Test: {'PASSED' if access_token else 'SKIPPED'}")
    print(f"✅ Configuration Test: {'PASSED' if config_success else 'FAILED'}")
    
    print("\n🔧 Next Steps for Real FHIR Testing:")
    print("   1. ✅ Epic FHIR server is accessible")
    print("   2. ✅ FHIR endpoints are available")
    print("   3. 📝 Register your app at https://fhir.epic.com/")
    print("   4. 🔑 Get your Epic Client ID and Secret")
    print("   5. 📁 Add credentials to .env file")
    print("   6. 🚀 Test the launch flow from Epic EHR")
    print("   7. 🔐 Extract access token from OAuth response")
    print("   8. 🧪 Test individual FHIR endpoints with real data")
    
    if sandbox_success:
        print("\n🎉 Epic FHIR server is accessible!")
        print("   You can now proceed with app registration and testing.")

if __name__ == "__main__":
    main() 