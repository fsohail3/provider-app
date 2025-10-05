#!/usr/bin/env python3
"""
Test Epic Configuration and Troubleshoot OAuth Issues
"""
import requests
import json
import os
import logging
from datetime import datetime
import epic_config  # Load the configuration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EpicConfigTester:
    """Test Epic configuration and troubleshoot OAuth issues"""
    
    def __init__(self):
        # Load configuration
        epic_config  # This sets the environment variables
        self.client_id = os.getenv('EPIC_CLIENT_ID')
        self.fhir_base_url = os.getenv('EPIC_FHIR_BASE_URL')
        self.auth_url = os.getenv('EPIC_AUTH_URL')
        self.token_url = os.getenv('EPIC_TOKEN_URL')
        
        print(f"🔍 Epic Configuration Troubleshooter")
        print(f"   Client ID: {self.client_id}")
        print(f"   Auth URL: {self.auth_url}")
        print(f"   FHIR Base: {self.fhir_base_url}")
    
    def test_epic_app_registration(self):
        """Test if Epic can find your app"""
        print(f"\n🔍 Testing Epic App Registration")
        print("=" * 50)
        
        # Test different redirect URI variations
        test_redirects = [
            "https://provider-app-icbi.onrender.com/launch",
            "https://provider-app-icbi.onrender.com/launch/",
            "https://provider-app-icbi.onrender.com",
            "http://provider-app-icbi.onrender.com/launch",
            "https://provider-app-icbi.onrender.com/oauth/launch"
        ]
        
        for redirect_uri in test_redirects:
            print(f"\n🔗 Testing redirect URI: {redirect_uri}")
            
            auth_params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': redirect_uri,
                'scope': 'launch/patient patient/*.read',
                'state': 'test-state-123',
                'aud': self.fhir_base_url
            }
            
            try:
                response = requests.get(
                    self.auth_url, 
                    params=auth_params, 
                    allow_redirects=False
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 302:
                    print(f"   ✅ Redirect successful - this URI might work!")
                    location = response.headers.get('location', '')
                    print(f"   Location: {location[:100]}...")
                elif response.status_code == 400:
                    print(f"   ❌ Bad Request - check parameters")
                    print(f"   Response: {response.text[:200]}...")
                elif response.status_code == 401:
                    print(f"   🔒 Unauthorized - client ID or redirect URI issue")
                    print(f"   Response: {response.text[:200]}...")
                elif response.status_code == 404:
                    print(f"   🚫 Not Found - endpoint doesn't exist")
                else:
                    print(f"   ⚠️  Unexpected status: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
    
    def test_epic_metadata(self):
        """Test Epic FHIR metadata endpoint"""
        print(f"\n🔍 Testing Epic FHIR Metadata")
        print("=" * 50)
        
        try:
            url = f"{self.fhir_base_url}/metadata"
            headers = {
                'Accept': 'application/fhir+json',
                'Content-Type': 'application/fhir+json'
            }
            
            response = requests.get(url, headers=headers)
            
            print(f"URL: {url}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Epic FHIR server is accessible!")
                try:
                    data = response.json()
                    print(f"FHIR Version: {data.get('fhirVersion', 'Unknown')}")
                    print(f"Available Resources: {len(data.get('rest', [{}])[0].get('resource', []))}")
                except:
                    print("Response is not valid JSON")
            else:
                print(f"❌ Failed: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def test_client_id_validity(self):
        """Test if the client ID is valid"""
        print(f"\n🔍 Testing Client ID Validity")
        print("=" * 50)
        
        # Test with minimal parameters
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': 'https://provider-app-icbi.onrender.com/launch'
        }
        
        try:
            response = requests.get(
                self.auth_url, 
                params=auth_params, 
                allow_redirects=False
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:300]}...")
            
            if response.status_code == 400:
                print(f"\n🔍 Error Analysis:")
                if "client_id" in response.text.lower():
                    print("   ❌ Client ID issue detected")
                if "redirect_uri" in response.text.lower():
                    print("   ❌ Redirect URI issue detected")
                if "scope" in response.text.lower():
                    print("   ❌ Scope issue detected")
                    
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def generate_correct_auth_url(self):
        """Generate the correct authorization URL"""
        print(f"\n🔗 Generating Correct Authorization URL")
        print("=" * 50)
        
        # Use the most likely working redirect URI
        redirect_uri = "https://provider-app-icbi.onrender.com/launch"
        
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': 'launch/patient patient/*.read',
            'state': 'test-state-123',
            'aud': self.fhir_base_url
        }
        
        auth_url = f"{self.auth_url}?"
        auth_url += "&".join([f"{k}={v}" for k, v in auth_params.items()])
        
        print(f"📱 Try this authorization URL:")
        print("=" * 60)
        print(auth_url)
        print("=" * 60)
        
        return auth_url
    
    def run_troubleshooting(self):
        """Run complete troubleshooting"""
        print("🚀 Epic OAuth Troubleshooting Suite")
        print("=" * 60)
        
        # Test 1: Epic FHIR metadata
        self.test_epic_metadata()
        
        # Test 2: Client ID validity
        self.test_client_id_validity()
        
        # Test 3: App registration with different redirects
        self.test_epic_app_registration()
        
        # Test 4: Generate correct auth URL
        self.generate_correct_auth_url()
        
        # Summary and recommendations
        print(f"\n📋 Troubleshooting Summary")
        print("=" * 60)
        print("🔍 Common Issues and Solutions:")
        print("1. ❌ Invalid redirect URI - Check Epic app configuration")
        print("2. ❌ Client ID not found - Verify app registration")
        print("3. ❌ Wrong scope - Use 'launch/patient patient/*.read'")
        print("4. ❌ App not approved - Contact Epic support")
        
        print(f"\n🔧 Next Steps:")
        print("1. Check your Epic app registration at https://fhir.epic.com/")
        print("2. Verify the redirect URI matches exactly")
        print("3. Ensure the app is approved and active")
        print("4. Try the generated authorization URL above")

def main():
    """Main function"""
    tester = EpicConfigTester()
    tester.run_troubleshooting()

if __name__ == "__main__":
    main() 