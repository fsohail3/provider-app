#!/usr/bin/env python3
"""
Test OAuth Authorization Code
Use this script to test the authorization code you receive from Epic
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

class OAuthCodeTester:
    """Test the OAuth authorization code"""
    
    def __init__(self):
        # Load configuration
        epic_config  # This sets the environment variables
        self.client_id = os.getenv('EPIC_CLIENT_ID')
        self.fhir_base_url = os.getenv('EPIC_FHIR_BASE_URL')
        self.token_url = os.getenv('EPIC_TOKEN_URL')
        self.redirect_uri = 'https://provider-app-icbi.onrender.com/launch'
        
        print(f"🚀 OAuth Code Tester Initialized")
        print(f"   Client ID: {self.client_id}")
        print(f"   Token URL: {self.token_url}")
        print(f"   Redirect URI: {self.redirect_uri}")
    
    def test_authorization_code(self, auth_code):
        """Test the authorization code by attempting token exchange"""
        print(f"\n🔍 Testing Authorization Code")
        print("=" * 50)
        print(f"Code: {auth_code[:20]}...")
        
        # Prepare token exchange request
        token_data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id
        }
        
        print(f"\n📋 Token Exchange Request:")
        print(f"URL: {self.token_url}")
        print(f"Data: {json.dumps(token_data, indent=2)}")
        
        try:
            # Make the token exchange request
            response = requests.post(
                self.token_url,
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            print(f"\n📊 Response:")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                token_response = response.json()
                print(f"✅ SUCCESS! Token exchange successful!")
                print(f"Access Token: {token_response.get('access_token', '')[:50]}...")
                print(f"Token Type: {token_response.get('token_type', 'Unknown')}")
                print(f"Expires In: {token_response.get('expires_in', 'Unknown')} seconds")
                print(f"Scope: {token_response.get('scope', 'Unknown')}")
                
                # Test the access token with FHIR calls
                access_token = token_response.get('access_token')
                if access_token:
                    self.test_access_token(access_token)
                
                return token_response
                
            else:
                print(f"❌ Token exchange failed:")
                print(f"Error: {response.text}")
                
                # Try to parse error response
                try:
                    error_data = response.json()
                    print(f"Error Details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Raw Error: {response.text}")
                
                return None
                
        except Exception as e:
            print(f"❌ Error during token exchange: {str(e)}")
            return None
    
    def test_access_token(self, access_token):
        """Test the access token with real FHIR API calls"""
        print(f"\n🧪 Testing Access Token with FHIR APIs")
        print("=" * 60)
        
        # Test different FHIR resources
        test_resources = [
            ("Patient", "Get patient demographics"),
            ("Observation", "Get vital signs (limit 5)"),
            ("Condition", "Get medical conditions (limit 5)")
        ]
        
        for resource_type, description in test_resources:
            print(f"\n🔍 {description}")
            print("-" * 40)
            
            url = f"{self.fhir_base_url}/{resource_type}"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/fhir+json',
                'Content-Type': 'application/fhir+json'
            }
            
            params = {}
            if resource_type != "Patient":
                params['_count'] = '5'  # Limit results for testing
            
            print(f"URL: {url}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Params: {json.dumps(params, indent=2)}")
            
            try:
                response = requests.get(url, headers=headers, params=params)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Found {data.get('total', 0)} resources")
                    
                    # Show sample data
                    if 'entry' in data and len(data['entry']) > 0:
                        sample = data['entry'][0]['resource']
                        print(f"Sample data:")
                        print(json.dumps(sample, indent=2)[:800] + "...")
                        
                        # Save the data to a file for inspection
                        filename = f"epic_fhir_{resource_type.lower()}_data.json"
                        with open(filename, 'w') as f:
                            json.dump(data, f, indent=2)
                        print(f"💾 Full data saved to: {filename}")
                    else:
                        print("No data returned")
                        
                elif response.status_code == 401:
                    print("🔒 Unauthorized - Token may be expired or invalid")
                elif response.status_code == 403:
                    print("🚫 Forbidden - Insufficient permissions")
                else:
                    print(f"⚠️  Unexpected status: {response.status_code}")
                    print(f"Response: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def interactive_test(self):
        """Interactive testing of authorization code"""
        print(f"\n🎯 Interactive OAuth Code Testing")
        print("=" * 50)
        
        print("📱 To get your authorization code:")
        print("1. Visit this URL in your browser:")
        auth_url = f"https://fhir.epic.com/oauth2/authorize?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope=launch/patient patient/*.read&state=test-state-123&aud={self.fhir_base_url}"
        print(f"   {auth_url}")
        
        print("\n2. Complete the Epic authorization")
        print("3. Copy the authorization code from the redirect URL")
        print("4. Paste it below:")
        
        # Get authorization code from user
        auth_code = input("\n🔑 Enter your authorization code: ").strip()
        
        if auth_code:
            print(f"\n🚀 Testing authorization code: {auth_code[:20]}...")
            result = self.test_authorization_code(auth_code)
            
            if result:
                print(f"\n🎉 SUCCESS! You now have a working Epic FHIR integration!")
                print(f"   Access Token: {result.get('access_token', '')[:50]}...")
                print(f"   You can now make real FHIR API calls!")
            else:
                print(f"\n❌ Token exchange failed. Check the error details above.")
        else:
            print("❌ No authorization code provided.")

def main():
    """Main function"""
    tester = OAuthCodeTester()
    
    print("🚀 Epic FHIR OAuth Code Tester")
    print("=" * 50)
    
    # Check if authorization code is provided as command line argument
    import sys
    if len(sys.argv) > 1:
        auth_code = sys.argv[1]
        print(f"🔑 Testing provided authorization code: {auth_code[:20]}...")
        tester.test_authorization_code(auth_code)
    else:
        # Interactive mode
        tester.interactive_test()

if __name__ == "__main__":
    main() 