#!/usr/bin/env python3
"""
Diagnose Epic App Configuration Issues
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

class EpicAppDiagnostic:
    """Diagnose Epic app configuration issues"""
    
    def __init__(self):
        # Load configuration
        epic_config  # This sets the environment variables
        self.client_id = os.getenv('EPIC_CLIENT_ID')
        self.fhir_base_url = os.getenv('EPIC_FHIR_BASE_URL')
        self.auth_url = os.getenv('EPIC_AUTH_URL')
        self.redirect_uri = 'https://provider-app-icbi.onrender.com'
        
        print(f"🔍 Epic App Diagnostic Tool")
        print(f"   Client ID: {self.client_id}")
        print(f"   Auth URL: {self.auth_url}")
        print(f"   Redirect URI: {self.redirect_uri}")
    
    def test_basic_epic_access(self):
        """Test basic Epic access"""
        print(f"\n🏥 Testing Basic Epic Access")
        print("=" * 50)
        
        # Test basic Epic endpoints
        test_urls = [
            "https://fhir.epic.com/",
            "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/metadata",
            "https://fhir.epic.com/oauth2/authorize"
        ]
        
        for url in test_urls:
            try:
                print(f"\n🔍 Testing: {url}")
                response = requests.get(url, timeout=10)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"✅ Accessible")
                else:
                    print(f"⚠️  Status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def test_oauth_with_different_scopes(self):
        """Test OAuth with different scope formats"""
        print(f"\n🔐 Testing OAuth with Different Scopes")
        print("=" * 50)
        
        # Test different scope formats
        scope_tests = [
            "launch/patient",
            "launch",
            "patient/*.read",
            "openid",
            "profile"
        ]
        
        for scope in scope_tests:
            print(f"\n🔍 Testing scope: {scope}")
            
            auth_params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'scope': scope
            }
            
            try:
                response = requests.get(
                    self.auth_url, 
                    params=auth_params, 
                    allow_redirects=False
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 302:
                    print(f"✅ SUCCESS! Redirect working with scope: {scope}")
                    location = response.headers.get('location', '')
                    print(f"Redirect to: {location[:100]}...")
                    
                    # Build working URL
                    working_url = f"{self.auth_url}?"
                    working_url += "&".join([f"{k}={v}" for k, v in auth_params.items()])
                    print(f"Working URL: {working_url}")
                    return working_url
                    
                elif response.status_code == 400:
                    print(f"❌ Bad Request")
                    print(f"Response: {response.text[:200]}...")
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
        
        return None
    
    def test_minimal_oauth(self):
        """Test minimal OAuth configuration"""
        print(f"\n🔐 Testing Minimal OAuth")
        print("=" * 50)
        
        # Test with absolute minimum parameters
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri
        }
        
        print(f"Testing with minimal params: {json.dumps(auth_params, indent=2)}")
        
        try:
            response = requests.get(
                self.auth_url, 
                params=auth_params, 
                allow_redirects=False
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 302:
                print(f"✅ SUCCESS! Minimal OAuth working!")
                location = response.headers.get('location', '')
                print(f"Redirect to: {location[:100]}...")
                
                # Build working URL
                working_url = f"{self.auth_url}?"
                working_url += "&".join([f"{k}={v}" for k, v in auth_params.items()])
                print(f"Working URL: {working_url}")
                return working_url
                
            else:
                print(f"Response: {response.text[:300]}...")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        return None
    
    def check_epic_app_registration_issues(self):
        """Check for common Epic app registration issues"""
        print(f"\n📋 Epic App Registration Issues Check")
        print("=" * 50)
        
        print("🔍 Common Issues to Check:")
        print("1. ❌ App Status: Is your app 'Active' or 'Approved'?")
        print("2. ❌ Client ID: Is the client ID exactly correct?")
        print("3. ❌ Redirect URI: Does it match exactly?")
        print("4. ❌ App Permissions: Are the required FHIR APIs selected?")
        print("5. ❌ App Approval: Has Epic approved your app?")
        print("6. ❌ Environment: Are you using the right Epic environment?")
        
        print(f"\n🔧 Troubleshooting Steps:")
        print("1. Go to https://fhir.epic.com/")
        print("2. Check your app status (should be 'Active' or 'Test')")
        print("3. Verify the client ID matches exactly")
        print("4. Check that redirect URI is exactly: https://provider-app-icbi.onrender.com")
        print("5. Ensure required FHIR APIs are selected")
        print("6. Contact Epic support if app is not approved")
    
    def run_diagnostic(self):
        """Run complete diagnostic"""
        print("🚀 Epic App Diagnostic Suite")
        print("=" * 60)
        
        # Test 1: Basic Epic access
        self.test_basic_epic_access()
        
        # Test 2: OAuth with different scopes
        working_scope = self.test_oauth_with_different_scopes()
        
        # Test 3: Minimal OAuth
        if not working_scope:
            working_minimal = self.test_minimal_oauth()
        
        # Test 4: Check app registration issues
        self.check_epic_app_registration_issues()
        
        # Summary
        print(f"\n📊 Diagnostic Summary")
        print("=" * 60)
        
        if working_scope:
            print(f"✅ Found working OAuth configuration!")
            print(f"   Use the working URL above to complete the OAuth flow.")
        elif working_minimal:
            print(f"✅ Found working minimal OAuth configuration!")
            print(f"   Use the minimal URL above to complete the OAuth flow.")
        else:
            print(f"❌ No working OAuth configuration found.")
            print(f"   This suggests an Epic app registration or configuration issue.")
            print(f"   Check the troubleshooting steps above.")

def main():
    """Main function"""
    diagnostic = EpicAppDiagnostic()
    diagnostic.run_diagnostic()

if __name__ == "__main__":
    main() 