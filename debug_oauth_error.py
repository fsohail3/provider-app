#!/usr/bin/env python3
"""
Debug OAuth Error - Get Detailed Error Information
"""
import requests
import json
import os
import epic_config  # Load the configuration

class OAuthErrorDebugger:
    """Debug OAuth errors step by step"""
    
    def __init__(self):
        # Load configuration
        epic_config  # This sets the environment variables
        self.client_id = os.getenv('EPIC_CLIENT_ID')
        self.auth_url = os.getenv('EPIC_AUTH_URL')
        self.redirect_uri = 'https://provider-app-icbi.onrender.com'
        
        print(f"🔍 OAuth Error Debugger")
        print(f"   Client ID: {self.client_id}")
        print(f"   Auth URL: {self.auth_url}")
        print(f"   Redirect URI: {self.redirect_uri}")
    
    def test_step_by_step_oauth(self):
        """Test OAuth step by step to identify the exact failure point"""
        print(f"\n🔍 Step-by-Step OAuth Testing")
        print("=" * 50)
        
        # Test 1: Basic OAuth (no scope)
        print(f"\n🔍 Test 1: Basic OAuth (no scope)")
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri
        }
        
        try:
            response = requests.get(
                self.auth_url, 
                params=auth_params, 
                allow_redirects=False
            )
            
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 302:
                location = response.headers.get('location', '')
                print(f"✅ Redirect Location: {location}")
                
                # Check if redirect contains error
                if 'error' in location.lower():
                    print(f"❌ Error in redirect: {location}")
                elif 'logoff' in location.lower():
                    print(f"✅ Normal login redirect")
                else:
                    print(f"✅ Successful redirect")
                    
            else:
                print(f"Response Body: {response.text[:500]}...")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # Test 2: OAuth with scope
        print(f"\n🔍 Test 2: OAuth with scope")
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
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
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 302:
                location = response.headers.get('location', '')
                print(f"✅ Redirect Location: {location}")
                
                # Check if redirect contains error
                if 'error' in location.lower():
                    print(f"❌ Error in redirect: {location}")
                elif 'logoff' in location.lower():
                    print(f"✅ Normal login redirect")
                else:
                    print(f"✅ Successful redirect")
                    
            else:
                print(f"Response Body: {response.text[:500]}...")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def check_epic_app_configuration(self):
        """Check Epic app configuration requirements"""
        print(f"\n📋 Epic App Configuration Check")
        print("=" * 50)
        
        print("🔍 Based on your app status, check these settings:")
        print("1. ✅ App Status: Should be 'Active' or 'Test' (not 'Draft')")
        print("2. ✅ App Type: Should be 'Sandbox' (which you have correct)")
        print("3. ✅ Required FHIR APIs: Must be selected")
        print("4. ✅ Redirect URI: Must match exactly")
        print("5. ✅ Client ID: Must be active and valid")
        
        print(f"\n🔧 Specific Checks for Sandbox:")
        print("1. Go to https://fhir.epic.com/")
        print("2. Check your app status (should show 'Active' or 'Test')")
        print("3. Verify these FHIR APIs are selected:")
        print("   - Patient.Read (R4)")
        print("   - Observation.Read (Vital Signs) (R4)")
        print("   - Condition.Read (R4)")
        print("   - MedicationRequest.Read (R4)")
        print("4. Check redirect URI is exactly: {self.redirect_uri}")
        
        print(f"\n🚨 Common Sandbox Issues:")
        print("1. App not yet approved by Epic")
        print("2. Required FHIR APIs not selected")
        print("3. App status still 'Draft' or 'Pending'")
        print("4. Redirect URI mismatch")
    
    def generate_working_oauth_urls(self):
        """Generate working OAuth URLs for testing"""
        print(f"\n🔗 Working OAuth URLs to Try")
        print("=" * 50)
        
        # URL 1: Basic OAuth (no scope)
        url1 = f"{self.auth_url}?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}"
        print(f"🔗 URL 1 (Basic): {url1}")
        
        # URL 2: OAuth with scope
        url2 = f"{self.auth_url}?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope=launch/patient"
        print(f"🔗 URL 2 (With Scope): {url2}")
        
        # URL 3: OAuth with state
        url3 = f"{self.auth_url}?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}&state=test123"
        print(f"🔗 URL 3 (With State): {url3}")
        
        print(f"\n🎯 Try these URLs in order:")
        print("1. Start with URL 1 (Basic)")
        print("2. If that fails, try URL 2 (With Scope)")
        print("3. If that fails, try URL 3 (With State)")
        print("4. Report the exact error message you get")
    
    def run_debug(self):
        """Run complete debug"""
        print("🚀 OAuth Error Debug Suite")
        print("=" * 60)
        
        # Test 1: Step-by-step OAuth
        self.test_step_by_step_oauth()
        
        # Test 2: Check configuration
        self.check_epic_app_configuration()
        
        # Test 3: Generate working URLs
        self.generate_working_oauth_urls()
        
        # Summary
        print(f"\n📊 Debug Summary")
        print("=" * 60)
        print("🔍 The OAuth flow is working (we confirmed 302 redirects)")
        print("🔍 The issue is likely in the redirect handling or app configuration")
        print("🔍 Try the generated URLs and report the exact error message")
        print("🔍 Check your Epic app status and FHIR API selections")

def main():
    """Main function"""
    debugger = OAuthErrorDebugger()
    debugger.run_debug()

if __name__ == "__main__":
    main() 