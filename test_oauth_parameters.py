#!/usr/bin/env python3
"""
Test Different OAuth Parameter Combinations
Find the right parameters that work with Epic
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

class OAuthParameterTester:
    """Test different OAuth parameter combinations"""
    
    def __init__(self):
        # Load configuration
        epic_config  # This sets the environment variables
        self.client_id = os.getenv('EPIC_CLIENT_ID')
        self.fhir_base_url = os.getenv('EPIC_FHIR_BASE_URL')
        self.auth_url = os.getenv('EPIC_AUTH_URL')
        self.redirect_uri = 'https://provider-app-icbi.onrender.com'
        
        print(f"🔍 OAuth Parameter Tester")
        print(f"   Client ID: {self.client_id}")
        print(f"   Auth URL: {self.auth_url}")
        print(f"   Redirect URI: {self.redirect_uri}")
    
    def test_parameter_combinations(self):
        """Test different OAuth parameter combinations"""
        print(f"\n🧪 Testing OAuth Parameter Combinations")
        print("=" * 60)
        
        # Test different parameter combinations
        test_configs = [
            {
                'name': 'Basic OAuth (minimal)',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri
                }
            },
            {
                'name': 'With scope (no space)',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'launch/patient'
                }
            },
            {
                'name': 'With scope (encoded space)',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'launch/patient%20patient/*.read'
                }
            },
            {
                'name': 'With scope (plus sign)',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'launch/patient+patient/*.read'
                }
            },
            {
                'name': 'With state parameter',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'launch/patient',
                    'state': 'test-state-123'
                }
            },
            {
                'name': 'With aud parameter',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'launch/patient',
                    'state': 'test-state-123',
                    'aud': self.fhir_base_url
                }
            },
            {
                'name': 'Full configuration (original)',
                'params': {
                    'response_type': 'code',
                    'client_id': self.client_id,
                    'redirect_uri': self.redirect_uri,
                    'scope': 'launch/patient patient/*.read',
                    'state': 'test-state-123',
                    'aud': self.fhir_base_url
                }
            }
        ]
        
        working_configs = []
        
        for config in test_configs:
            print(f"\n🔍 Testing: {config['name']}")
            print("-" * 40)
            
            try:
                response = requests.get(
                    self.auth_url, 
                    params=config['params'], 
                    allow_redirects=False
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 302:
                    print(f"✅ SUCCESS! Redirect working")
                    location = response.headers.get('location', '')
                    print(f"Location: {location[:100]}...")
                    working_configs.append(config)
                    
                    # Build the working URL
                    working_url = f"{self.auth_url}?"
                    working_url += "&".join([f"{k}={v}" for k, v in config['params'].items()])
                    print(f"Working URL: {working_url}")
                    
                elif response.status_code == 400:
                    print(f"❌ Bad Request")
                    print(f"Response: {response.text[:200]}...")
                elif response.status_code == 401:
                    print(f"🔒 Unauthorized")
                    print(f"Response: {response.text[:200]}...")
                elif response.status_code == 500:
                    print(f"🚨 Server Error (Epic issue)")
                    print(f"Response: {response.text[:200]}...")
                else:
                    print(f"⚠️  Status: {response.status_code}")
                    print(f"Response: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        return working_configs
    
    def test_epic_server_health(self):
        """Test if Epic servers are healthy"""
        print(f"\n🏥 Testing Epic Server Health")
        print("=" * 50)
        
        # Test basic endpoints
        test_endpoints = [
            f"{self.fhir_base_url}/metadata",
            f"{self.auth_url}",
            "https://fhir.epic.com/"
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
    
    def generate_working_urls(self, working_configs):
        """Generate working OAuth URLs"""
        print(f"\n🔗 Working OAuth URLs")
        print("=" * 50)
        
        if not working_configs:
            print("❌ No working configurations found")
            return
        
        for i, config in enumerate(working_configs, 1):
            print(f"\n{i}. {config['name']}")
            print("-" * 30)
            
            # Build the working URL
            working_url = f"{self.auth_url}?"
            working_url += "&".join([f"{k}={v}" for k, v in config['params'].items()])
            
            print(f"URL: {working_url}")
            print(f"Parameters: {json.dumps(config['params'], indent=2)}")
    
    def run_complete_test(self):
        """Run complete parameter testing"""
        print("🚀 Epic OAuth Parameter Testing Suite")
        print("=" * 60)
        
        # Test 1: Epic server health
        self.test_epic_server_health()
        
        # Test 2: OAuth parameter combinations
        working_configs = self.test_parameter_combinations()
        
        # Test 3: Generate working URLs
        self.generate_working_urls(working_configs)
        
        # Summary
        print(f"\n📊 Test Summary")
        print("=" * 60)
        print(f"Total configurations tested: 7")
        print(f"Working configurations: {len(working_configs)}")
        
        if working_configs:
            print(f"\n🎉 SUCCESS! Found working OAuth configurations!")
            print(f"   Use one of the working URLs above to complete the OAuth flow.")
        else:
            print(f"\n❌ No working configurations found.")
            print(f"   This suggests an Epic server issue or configuration problem.")
            print(f"   Try again later or contact Epic support.")

def main():
    """Main function"""
    tester = OAuthParameterTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main() 