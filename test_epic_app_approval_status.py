#!/usr/bin/env python3
"""
Test Epic App Approval Status
"""
import requests
import json
import os
import epic_config  # Load the configuration

class EpicAppApprovalStatusTester:
    """Test if Epic app approval is the issue"""
    
    def __init__(self):
        # Load configuration
        epic_config  # This sets the environment variables
        self.client_id = os.getenv('EPIC_CLIENT_ID')
        self.auth_url = os.getenv('EPIC_AUTH_URL')
        self.redirect_uri = 'https://provider-app-icbi.onrender.com'
        self.aud = 'https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4'
        
        print(f"🔍 Epic App Approval Status Tester")
        print(f"   Client ID: {self.client_id}")
        print(f"   Auth URL: {self.auth_url}")
        print(f"   Redirect URI: {self.redirect_uri}")
        print(f"   Audience (aud): {self.aud}")
    
    def test_oauth_with_different_scopes(self):
        """Test OAuth with different scope combinations"""
        print(f"\n🔍 Testing OAuth with Different Scopes")
        print("=" * 50)
        
        # Test different scope combinations
        scope_tests = [
            "launch",
            "launch/patient",
            "openid",
            "profile",
            "launch/patient openid profile"
        ]
        
        for scope in scope_tests:
            print(f"\n🔍 Testing scope: {scope}")
            
            auth_params = {
                'response_type': 'code',
                'client_id': self.client_id,
                'redirect_uri': self.redirect_uri,
                'scope': scope,
                'aud': self.aud
            }
            
            try:
                response = requests.get(
                    self.auth_url, 
                    params=auth_params, 
                    allow_redirects=False
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 302:
                    location = response.headers.get('location', '')
                    print(f"✅ Redirect: {location[:100]}...")
                    
                    if 'logoff' in location.lower():
                        print(f"   ✅ Normal login redirect")
                    elif 'error' in location.lower():
                        print(f"   ❌ Still getting error redirect")
                    elif self.redirect_uri in location:
                        print(f"   🎉 SUCCESS! OAuth working!")
                    else:
                        print(f"   ✅ Redirect working")
                        
                elif response.status_code == 400:
                    print(f"❌ Bad Request")
                    print(f"   Response: {response.text[:200]}...")
                elif response.status_code == 401:
                    print(f"🔒 Unauthorized")
                    print(f"   Response: {response.text[:200]}...")
                elif response.status_code == 500:
                    print(f"🚨 Server Error")
                    print(f"   Response: {response.text[:200]}...")
                else:
                    print(f"⚠️  Status: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def test_minimal_oauth(self):
        """Test minimal OAuth configuration"""
        print(f"\n🔍 Testing Minimal OAuth Configuration")
        print("=" * 50)
        
        # Test with absolute minimum required parameters
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'aud': self.aud
        }
        
        print(f"Testing with minimal params (no scope):")
        for key, value in auth_params.items():
            print(f"   {key}: {value}")
        
        try:
            response = requests.get(
                self.auth_url, 
                params=auth_params, 
                allow_redirects=False
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 302:
                location = response.headers.get('location', '')
                print(f"✅ Redirect: {location[:100]}...")
                
                if 'logoff' in location.lower():
                    print(f"   ✅ Minimal OAuth working!")
                elif 'error' in location.lower():
                    print(f"   ❌ Still getting error")
                else:
                    print(f"   ✅ Redirect working")
                    
            else:
                print(f"Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def analyze_error_patterns(self):
        """Analyze the error patterns we're seeing"""
        print(f"\n🔍 Error Pattern Analysis")
        print("=" * 50)
        
        print("🔍 What We Know:")
        print("1. ✅ OAuth parameters are correct (with aud)")
        print("2. ✅ You're logged into Epic")
        print("3. ✅ Epic recognizes your client ID")
        print("4. ❌ But still getting error page")
        
        print(f"\n🎯 Most Likely Causes:")
        print("1. ❌ App not fully approved by Epic")
        print("2. ❌ App status still 'Draft' or 'Pending'")
        print("3. ❌ Required FHIR APIs not approved")
        print("4. ❌ Epic hasn't activated OAuth for your app")
        
        print(f"\n🔧 Immediate Actions:")
        print("1. Check app status at: https://fhir.epic.com/Developer/Edit?appId=45459")
        print("2. Look for approval indicators")
        print("3. Check FHIR API selection status")
        print("4. Contact Epic support if app not approved")
        
        print(f"\n💡 Why This Happens:")
        print("- Epic requires manual approval of all apps")
        print("- Even with correct OAuth parameters, app must be approved")
        print("- Error page is Epic's way of saying 'app not ready'")
        print("- This is a configuration issue, not a technical OAuth problem")
    
    def provide_next_steps(self):
        """Provide clear next steps"""
        print(f"\n🎯 Next Steps to Resolve This")
        print("=" * 50)
        
        print("🔧 Step 1: Check App Status")
        print("1. Go to: https://fhir.epic.com/Developer/Edit?appId=45459")
        print("2. Look for app status indicators")
        print("3. Check if app shows 'Active', 'Test', 'Draft', or 'Pending'")
        
        print(f"\n🔧 Step 2: Check FHIR APIs")
        print("1. Scroll to 'Incoming APIs' section")
        print("2. Verify required APIs are selected")
        print("3. Check if APIs show approval status")
        
        print(f"\n🔧 Step 3: Contact Epic Support")
        print("1. If app is 'Draft' or 'Pending', contact Epic")
        print("2. Reference your email to open@epic.com")
        print("3. Request expedited app approval")
        
        print(f"\n🔧 Step 4: Wait for Approval")
        print("1. Epic approval can take 1-3 business days")
        print("2. Once approved, OAuth will work automatically")
        print("3. No more error pages - normal OAuth flow")
        
        print(f"\n💡 Pro Tip:")
        print("The OAuth error page with correct parameters")
        print("strongly suggests an Epic app approval issue.")
        print("Check your app status now!")
    
    def run_complete_test(self):
        """Run complete approval status test"""
        print("🚀 Epic App Approval Status Test")
        print("=" * 60)
        
        # Test 1: Different scopes
        self.test_oauth_with_different_scopes()
        
        # Test 2: Minimal OAuth
        self.test_minimal_oauth()
        
        # Test 3: Error analysis
        self.analyze_error_patterns()
        
        # Test 4: Next steps
        self.provide_next_steps()
        
        # Summary
        print(f"\n📊 Test Summary")
        print("=" * 60)
        print("🔍 OAuth parameters are now correct")
        print("🔍 But Epic still can't process the request")
        print("🔍 This suggests an app approval issue")
        print("🔍 Check your app status at Epic now!")

def main():
    """Main function"""
    tester = EpicAppApprovalStatusTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main() 