#!/usr/bin/env python3
"""
Test All Possible OAuth Configurations
"""
import requests
import json
import os
import epic_config  # Load the configuration

class OAuthConfigurationTester:
    """Test all possible OAuth configurations"""
    
    def __init__(self):
        # Load configuration
        epic_config  # This sets the environment variables
        self.client_id = os.getenv('EPIC_CLIENT_ID')
        self.auth_url = os.getenv('EPIC_AUTH_URL')
        self.redirect_uri = 'https://provider-app-icbi.onrender.com'
        
        print(f"🔍 OAuth Configuration Tester")
        print(f"   Client ID: {self.client_id}")
        print(f"   Auth URL: {self.auth_url}")
        print(f"   Redirect URI: {self.redirect_uri}")
    
    def test_all_oauth_combinations(self):
        """Test all possible OAuth parameter combinations"""
        print(f"\n🔍 Testing All OAuth Combinations")
        print("=" * 50)
        
        # Test different parameter combinations
        test_configs = [
            {
                'name': 'Minimal OAuth',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri
                }
            },
            {
                'name': 'OAuth with launch scope',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'launch'
                }
            },
            {
                'name': 'OAuth with launch/patient scope',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'launch/patient'
                }
            },
            {
                'name': 'OAuth with openid scope',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'openid'
                }
            },
            {
                'name': 'OAuth with profile scope',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'profile'
                }
            },
            {
                'name': 'OAuth with state parameter',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'state': 'test123'
                }
            },
            {
                'name': 'OAuth with aud parameter',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'aud': 'https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4'
                }
            },
            {
                'name': 'OAuth with multiple scopes',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'launch/patient openid profile'
                }
            }
        ]
        
        working_configs = []
        
        for config in test_configs:
            print(f"\n🔍 Testing: {config['name']}")
            
            try:
                response = requests.get(
                    self.auth_url, 
                    params=config['params'], 
                    allow_redirects=False
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 302:
                    location = response.headers.get('location', '')
                    print(f"✅ SUCCESS! Redirect: {location[:100]}...")
                    
                    # Check if this is a working redirect
                    if 'logoff' in location.lower():
                        print(f"   ✅ Normal login redirect - this should work!")
                        working_configs.append(config)
                        
                        # Build working URL
                        working_url = f"{self.auth_url}?"
                        working_url += "&".join([f"{k}={v}" for k, v in config['params'].items()])
                        print(f"   🔗 Working URL: {working_url}")
                        
                    elif 'error' in location.lower():
                        print(f"   ❌ Error in redirect: {location}")
                    else:
                        print(f"   ✅ Successful redirect: {location}")
                        
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
        
        return working_configs
    
    def test_epic_app_status(self):
        """Test if Epic app is properly configured"""
        print(f"\n🏥 Testing Epic App Status")
        print("=" * 50)
        
        # Test basic Epic access
        try:
            response = requests.get("https://fhir.epic.com/", timeout=10)
            print(f"Epic Homepage: Status {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Epic is accessible")
            else:
                print("❌ Epic may have issues")
                
        except Exception as e:
            print(f"❌ Error accessing Epic: {str(e)}")
        
        # Test OAuth endpoint
        try:
            response = requests.get("https://fhir.epic.com/oauth2/authorize", timeout=10)
            print(f"OAuth Endpoint: Status {response.status_code}")
            
            if response.status_code == 200:
                print("✅ OAuth endpoint is accessible")
            else:
                print("❌ OAuth endpoint may have issues")
                
        except Exception as e:
            print(f"❌ Error accessing OAuth: {str(e)}")
    
    def check_epic_app_requirements(self):
        """Check Epic app requirements"""
        print(f"\n📋 Epic App Requirements Check")
        print("=" * 50)
        
        print("🔍 Based on your app configuration, verify:")
        print("1. ✅ App Status: Should be 'Active' or 'Test'")
        print("2. ✅ App Stage: You're in 'Test' stage (correct)")
        print("3. ✅ Required FHIR APIs: Must be selected")
        print("4. ✅ Redirect URI: Must match exactly")
        print("5. ✅ Client ID: Must be active")
        
        print(f"\n🔧 Immediate Actions:")
        print("1. Go to https://fhir.epic.com/Developer/Edit?appId=45459")
        print("2. Check app status (should be 'Active' or 'Test')")
        print("3. Verify redirect URI is exactly: {self.redirect_uri}")
        print("4. Ensure required FHIR APIs are selected")
        print("5. Check if app needs Epic approval")
        
        print(f"\n🚨 Common Issues:")
        print("1. App not yet approved by Epic")
        print("2. App status still 'Draft' or 'Pending'")
        print("3. Required FHIR APIs not selected")
        print("4. Redirect URI mismatch")
        print("5. App not activated yet")
    
    def run_complete_test(self):
        """Run complete configuration test"""
        print("🚀 Complete OAuth Configuration Test")
        print("=" * 60)
        
        # Test 1: Epic app status
        self.test_epic_app_status()
        
        # Test 2: All OAuth combinations
        working_configs = self.test_all_oauth_combinations()
        
        # Test 3: Check requirements
        self.check_epic_app_requirements()
        
        # Summary
        print(f"\n📊 Test Summary")
        print("=" * 60)
        
        if working_configs:
            print(f"✅ Found {len(working_configs)} working OAuth configurations!")
            print(f"   Use any of the working URLs above.")
        else:
            print(f"❌ No working OAuth configurations found.")
            print(f"   This suggests an Epic app configuration issue.")
        
        print(f"\n🎯 Next Steps:")
        print("1. Check your Epic app status and approval")
        print("2. Verify all required FHIR APIs are selected")
        print("3. Ensure app is 'Active' or 'Test' (not 'Draft')")
        print("4. Contact Epic support if app is not approved")

def main():
    """Main function"""
    tester = OAuthConfigurationTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main() 