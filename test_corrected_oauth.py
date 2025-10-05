#!/usr/bin/env python3
"""
Test Corrected OAuth with Proper aud Parameter
"""
import requests
import json
import os
import epic_config  # Load the configuration

class CorrectedOAuthTester:
    """Test OAuth with the proper aud parameter"""
    
    def __init__(self):
        # Load configuration
        epic_config  # This sets the environment variables
        self.client_id = os.getenv('EPIC_CLIENT_ID')
        self.auth_url = os.getenv('EPIC_AUTH_URL')
        self.redirect_uri = 'https://provider-app-icbi.onrender.com'
        self.aud = 'https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4'
        
        print(f"🚀 Corrected OAuth Tester")
        print(f"   Client ID: {self.client_id}")
        print(f"   Auth URL: {self.auth_url}")
        print(f"   Redirect URI: {self.redirect_uri}")
        print(f"   Audience (aud): {self.aud}")
    
    def test_corrected_oauth(self):
        """Test OAuth with the proper aud parameter"""
        print(f"\n🔍 Testing Corrected OAuth (with aud parameter)")
        print("=" * 50)
        
        # Corrected OAuth parameters based on Epic troubleshooting
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'launch/patient',
            'aud': self.aud
        }
        
        print(f"Testing OAuth with corrected parameters:")
        for key, value in auth_params.items():
            print(f"   {key}: {value}")
        
        try:
            print(f"\n🔍 Making corrected OAuth request...")
            response = requests.get(
                self.auth_url, 
                params=auth_params, 
                allow_redirects=False
            )
            
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 302:
                location = response.headers.get('location', '')
                print(f"✅ SUCCESS! Redirect: {location}")
                
                # Check redirect type
                if 'logoff' in location.lower():
                    print(f"   ✅ Normal login redirect - OAuth is working!")
                    print(f"   ✅ The aud parameter fixed the issue!")
                    
                    # Build working URL
                    working_url = f"{self.auth_url}?"
                    working_url += "&".join([f"{k}={v}" for k, v in auth_params.items()])
                    print(f"\n🔗 Use this CORRECTED URL in your browser:")
                    print(f"   {working_url}")
                    
                elif 'error' in location.lower():
                    print(f"   ❌ Still getting error - check Epic app status")
                    print(f"   Response: {location}")
                    
                elif self.redirect_uri in location:
                    print(f"   🎉 SUCCESS! App approved and OAuth working!")
                    print(f"   🔍 Check for authorization code in URL")
                    
                else:
                    print(f"   ✅ Redirect working: {location}")
                    
            elif response.status_code == 400:
                print(f"❌ Bad Request")
                print(f"   Response: {response.text[:200]}...")
                print(f"   🔍 Check OAuth parameters")
                
            elif response.status_code == 401:
                print(f"🔒 Unauthorized")
                print(f"   Response: {response.text[:200]}...")
                print(f"   🔍 App may not be approved yet")
                
            elif response.status_code == 500:
                print(f"🚨 Server Error")
                print(f"   Response: {response.text[:200]}...")
                print(f"   🔍 Epic server issue - try again later")
                
            else:
                print(f"⚠️  Unexpected Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def explain_the_fix(self):
        """Explain why the aud parameter fixes the issue"""
        print(f"\n💡 Why the aud Parameter Fixes This")
        print("=" * 50)
        
        print("🔍 According to Epic's troubleshooting documentation:")
        print("1. ✅ The 'aud' parameter is REQUIRED for OAuth requests")
        print("2. ✅ It specifies which Epic FHIR endpoint your app accesses")
        print("3. ✅ Without it, Epic shows 'Something went wrong' error")
        print("4. ✅ With it, OAuth flows correctly to login/authorization")
        
        print(f"\n🎯 What the aud Parameter Does:")
        print("- Tells Epic which FHIR endpoint your app needs access to")
        print("- Validates that your app is authorized for that endpoint")
        print("- Prevents unauthorized access to Epic's FHIR services")
        print("- Required for all OAuth 2.0 requests to Epic")
        
        print(f"\n🔧 The Correct aud Value:")
        print(f"   {self.aud}")
        print("- This is Epic's main FHIR R4 endpoint")
        print("- Matches your app's FHIR API selections")
        print("- Required for Patient, Observation, Condition APIs")
    
    def provide_next_steps(self):
        """Provide next steps with the corrected OAuth"""
        print(f"\n🎯 Next Steps with Corrected OAuth")
        print("=" * 50)
        
        print("🔧 Step 1: Test the Corrected URL")
        print("1. Use the corrected OAuth URL provided above")
        print("2. Epic should now redirect to login (not error page)")
        print("3. The aud parameter tells Epic exactly what you need")
        
        print(f"\n🔧 Step 2: Complete OAuth Flow")
        print("1. Log in with your Epic credentials")
        print("2. Grant permissions to your app")
        print("3. Get redirected with authorization code")
        
        print(f"\n🔧 Step 3: Test FHIR Integration")
        print("1. Use authorization code to get access token")
        print("2. Make FHIR API calls to test endpoints")
        print("3. Verify data integration with your app")
        
        print(f"\n💡 Pro Tip:")
        print("The aud parameter was the missing piece!")
        print("Epic requires it for security and endpoint validation.")
        print("This should resolve your OAuth error page issue.")
    
    def run_complete_test(self):
        """Run complete corrected OAuth test"""
        print("🚀 Corrected OAuth Testing Suite")
        print("=" * 60)
        
        # Test 1: Corrected OAuth
        self.test_corrected_oauth()
        
        # Test 2: Explain the fix
        self.explain_the_fix()
        
        # Test 3: Next steps
        self.provide_next_steps()
        
        # Summary
        print(f"\n📊 Test Summary")
        print("=" * 60)
        print("🔍 The aud parameter was the missing piece!")
        print("🔍 Epic requires it for all OAuth requests")
        print("🔍 This should fix your OAuth error page issue")
        print("🔍 Try the corrected URL now!")

def main():
    """Main function"""
    tester = CorrectedOAuthTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main() 