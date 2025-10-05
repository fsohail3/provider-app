#!/usr/bin/env python3
"""
Test OAuth After Epic Approval
"""
import requests
import json
import os
import epic_config  # Load the configuration

class OAuthPostApprovalTester:
    """Test OAuth once Epic approves the app"""
    
    def __init__(self):
        # Load configuration
        epic_config  # This sets the environment variables
        self.client_id = os.getenv('EPIC_CLIENT_ID')
        self.auth_url = os.getenv('EPIC_AUTH_URL')
        self.redirect_uri = 'https://provider-app-icbi.onrender.com'
        
        print(f"🚀 OAuth Post-Approval Tester")
        print(f"   Client ID: {self.client_id}")
        print(f"   Auth URL: {self.auth_url}")
        print(f"   Redirect URI: {self.redirect_uri}")
    
    def test_oauth_flow(self):
        """Test the complete OAuth flow"""
        print(f"\n🔍 Testing OAuth Flow After Approval")
        print("=" * 50)
        
        # Test OAuth with minimal parameters
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'launch/patient'
        }
        
        print(f"Testing OAuth with parameters:")
        for key, value in auth_params.items():
            print(f"   {key}: {value}")
        
        try:
            print(f"\n🔍 Making OAuth request...")
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
                    print(f"   ✅ Normal login redirect - app needs login")
                    print(f"   ✅ This means OAuth is working correctly!")
                    
                    # Build working URL
                    working_url = f"{self.auth_url}?"
                    working_url += "&".join([f"{k}={v}" for k, v in auth_params.items()])
                    print(f"\n🔗 Use this URL in your browser:")
                    print(f"   {working_url}")
                    
                elif 'error' in location.lower():
                    print(f"   ❌ Still getting error - app may not be approved yet")
                    print(f"   🔍 Check Epic support response")
                    
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
    
    def test_fhir_access(self):
        """Test FHIR access after approval"""
        print(f"\n🏥 Testing FHIR Access After Approval")
        print("=" * 50)
        
        # Test FHIR metadata
        try:
            print(f"Testing FHIR metadata...")
            response = requests.get(
                "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/metadata",
                headers={'Accept': 'application/fhir+json'},
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ FHIR metadata accessible")
                try:
                    data = response.json()
                    print(f"   FHIR Version: {data.get('fhirVersion', 'Unknown')}")
                    print(f"   Software: {data.get('software', {}).get('name', 'Unknown')}")
                except:
                    print("   Could not parse JSON response")
            else:
                print(f"❌ FHIR metadata not accessible: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error accessing FHIR: {str(e)}")
    
    def provide_next_steps(self):
        """Provide next steps based on test results"""
        print(f"\n🎯 Next Steps After Epic Approval")
        print("=" * 50)
        
        print("🔧 Step 1: Test OAuth")
        print("1. Use the OAuth URL provided above")
        print("2. Epic should redirect to login (not error page)")
        print("3. After login, you should see authorization page")
        print("4. Grant permissions to your app")
        
        print(f"\n🔧 Step 2: Get Authorization Code")
        print("1. Epic will redirect to: {self.redirect_uri}?code=AUTHORIZATION_CODE")
        print("2. Copy the authorization code from the URL")
        print("3. Use it to get an access token")
        
        print(f"\n🔧 Step 3: Test FHIR API Calls")
        print("1. Use access token to make FHIR API calls")
        print("2. Test Patient, Observation, Condition endpoints")
        print("3. Verify data integration with your app")
        
        print(f"\n💡 Pro Tip:")
        print("Once Epic approves your app, OAuth will work automatically.")
        print("The error page will disappear and you'll see the normal OAuth flow.")
    
    def run_complete_test(self):
        """Run complete post-approval test"""
        print("🚀 OAuth Post-Approval Testing Suite")
        print("=" * 60)
        
        # Test 1: OAuth flow
        self.test_oauth_flow()
        
        # Test 2: FHIR access
        self.test_fhir_access()
        
        # Test 3: Next steps
        self.provide_next_steps()
        
        # Summary
        print(f"\n📊 Test Summary")
        print("=" * 60)
        print("🔍 This script will help you test OAuth once Epic approves your app")
        print("🔍 Run it after you get approval email from Epic")
        print("🔍 OAuth should work automatically once approved")

def main():
    """Main function"""
    tester = OAuthPostApprovalTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main() 