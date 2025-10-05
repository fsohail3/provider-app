#!/usr/bin/env python3
"""
Test Epic App Status and Recognition
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

class EpicAppStatusTester:
    """Test if Epic recognizes your app"""
    
    def __init__(self):
        # Load configuration
        epic_config  # This sets the environment variables
        self.client_id = os.getenv('EPIC_CLIENT_ID')
        self.fhir_base_url = os.getenv('EPIC_FHIR_BASE_URL')
        self.auth_url = os.getenv('EPIC_AUTH_URL')
        self.redirect_uri = 'https://provider-app-icbi.onrender.com'
        
        print(f"🔍 Epic App Status Tester")
        print(f"   Client ID: {self.client_id}")
        print(f"   Auth URL: {self.auth_url}")
        print(f"   Redirect URI: {self.redirect_uri}")
    
    def test_app_recognition(self):
        """Test if Epic recognizes your app"""
        print(f"\n🔍 Testing Epic App Recognition")
        print("=" * 50)
        
        # Test with different client IDs to see if Epic recognizes yours
        test_client_ids = [
            self.client_id,  # Your actual client ID
            "test-client-id",  # Fake client ID for comparison
            "4787c109-971b-4933-9483-27b240bd8361"  # Your client ID again
        ]
        
        for client_id in test_client_ids:
            print(f"\n🔍 Testing Client ID: {client_id[:20]}...")
            
            auth_params = {
                'response_type': 'code',
                'client_id': client_id,
                'redirect_uri': self.redirect_uri,
                'scope': 'launch/patient'
            }
            
            try:
                response = requests.get(
                    self.auth_url, 
                    params=auth_params, 
                    allow_redirects=False
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 302:
                    print(f"✅ SUCCESS! App recognized")
                    location = response.headers.get('location', '')
                    print(f"Redirect to: {location[:100]}...")
                    
                    if "Logoff" in location:
                        print(f"⚠️  Redirecting to login - this is normal")
                    elif "error" in location.lower():
                        print(f"❌ Error in redirect")
                    else:
                        print(f"✅ Successful redirect")
                        
                elif response.status_code == 400:
                    print(f"❌ Bad Request")
                    print(f"Response: {response.text[:200]}...")
                    
                    # Check for specific error messages
                    if "client_id" in response.text.lower():
                        print(f"   🔍 Client ID issue detected")
                    if "redirect_uri" in response.text.lower():
                        print(f"   🔍 Redirect URI issue detected")
                    if "scope" in response.text.lower():
                        print(f"   🔍 Scope issue detected")
                        
                elif response.status_code == 401:
                    print(f"🔒 Unauthorized")
                    print(f"Response: {response.text[:200]}...")
                elif response.status_code == 500:
                    print(f"🚨 Server Error")
                    print(f"Response: {response.text[:200]}...")
                else:
                    print(f"⚠️  Status: {response.status_code}")
                    print(f"Response: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def test_epic_system_status(self):
        """Test Epic system status"""
        print(f"\n🏥 Testing Epic System Status")
        print("=" * 50)
        
        # Test basic Epic endpoints
        test_endpoints = [
            "https://fhir.epic.com/",
            "https://fhir.epic.com/oauth2/authorize",
            "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/metadata"
        ]
        
        for endpoint in test_endpoints:
            try:
                print(f"\n🔍 Testing: {endpoint}")
                response = requests.get(endpoint, timeout=10)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ Endpoint accessible")
                else:
                    print(f"⚠️  Status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def check_epic_requirements(self):
        """Check Epic app requirements"""
        print(f"\n📋 Epic App Requirements Check")
        print("=" * 50)
        
        print("🔍 Based on Epic Developer Guidelines, your app needs:")
        print("1. ✅ App Status: 'Active' or 'Test' (not 'Draft' or 'Pending')")
        print("2. ✅ Epic Approval: App must be approved by Epic")
        print("3. ✅ Required FHIR APIs: Patient, Observation, Condition, etc.")
        print("4. ✅ Redirect URI: Must match exactly")
        print("5. ✅ Client ID: Must be valid and active")
        
        print(f"\n🔧 Immediate Actions Required:")
        print("1. Go to https://fhir.epic.com/")
        print("2. Check your app status (should be 'Active' or 'Test')")
        print("3. If status is 'Draft' or 'Pending', contact Epic support")
        print("4. Verify all required FHIR APIs are selected")
        print("5. Ensure redirect URI is exactly: {self.redirect_uri}")
        
        print(f"\n📞 Epic Support:")
        print("If your app is not approved or active, contact Epic at:")
        print("open.epic.com/Home/Contact")
    
    def test_alternative_oauth_flows(self):
        """Test alternative OAuth flows"""
        print(f"\n🔄 Testing Alternative OAuth Flows")
        print("=" * 50)
        
        # Test different OAuth flows
        test_flows = [
            {
                'name': 'Basic OAuth (no scope)',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri
                }
            },
            {
                'name': 'OAuth with state',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'state': 'test123'
                }
            },
            {
                'name': 'OAuth with minimal scope',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'launch'
                }
            }
        ]
        
        for flow in test_flows:
            print(f"\n🔍 Testing: {flow['name']}")
            
            try:
                response = requests.get(
                    self.auth_url, 
                    params=flow['params'], 
                    allow_redirects=False
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 302:
                    print(f"✅ SUCCESS! This flow works")
                    location = response.headers.get('location', '')
                    print(f"Redirect to: {location[:100]}...")
                    
                    # Build working URL
                    working_url = f"{self.auth_url}?"
                    working_url += "&".join([f"{k}={v}" for k, v in flow['params'].items()])
                    print(f"Working URL: {working_url}")
                    return working_url
                    
                else:
                    print(f"Response: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        return None
    
    def run_complete_test(self):
        """Run complete app status test"""
        print("🚀 Epic App Status Testing Suite")
        print("=" * 60)
        
        # Test 1: Epic system status
        self.test_epic_system_status()
        
        # Test 2: App recognition
        self.test_app_recognition()
        
        # Test 3: Alternative OAuth flows
        working_flow = self.test_alternative_oauth_flows()
        
        # Test 4: Check requirements
        self.check_epic_requirements()
        
        # Summary
        print(f"\n📊 Test Summary")
        print("=" * 60)
        
        if working_flow:
            print(f"✅ Found working OAuth flow!")
            print(f"   Use the working URL above to complete the OAuth flow.")
        else:
            print(f"❌ No working OAuth flows found.")
            print(f"   This strongly suggests an Epic app configuration issue.")
            print(f"   Check your app status and approval in Epic's system.")
        
        print(f"\n🎯 Next Steps:")
        print("1. Check your Epic app status at https://fhir.epic.com/")
        print("2. Ensure app is 'Active' or 'Test' (not 'Draft')")
        print("3. Verify Epic has approved your app")
        print("4. Check that all required FHIR APIs are selected")
        print("5. Contact Epic support if app is not approved")

def main():
    """Main function"""
    tester = EpicAppStatusTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main() 