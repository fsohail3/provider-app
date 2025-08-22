#!/usr/bin/env python3
"""
Test script for Epic JWK endpoint
"""
import requests
import json

def test_jwk_endpoint():
    """Test the JWK endpoint"""
    try:
        # Test the JWK endpoint
        url = "https://provider-app-icbi.onrender.com/.well-known/jwks.json"
        print(f"Testing JWK endpoint: {url}")
        
        response = requests.get(url)
        
        if response.status_code == 200:
            jwks = response.json()
            print("✅ JWK endpoint is working!")
            print(f"Response: {json.dumps(jwks, indent=2)}")
            
            # Validate JWK structure
            if 'keys' in jwks and len(jwks['keys']) > 0:
                key = jwks['keys'][0]
                required_fields = ['kty', 'use', 'kid', 'n', 'e', 'alg']
                
                if all(field in key for field in required_fields):
                    print("✅ JWK structure is valid!")
                    print(f"Key ID: {key['kid']}")
                    print(f"Algorithm: {key['alg']}")
                    print(f"Key Type: {key['kty']}")
                else:
                    print("❌ JWK structure is missing required fields")
            else:
                print("❌ JWK response missing keys array")
        else:
            print(f"❌ JWK endpoint failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing JWK endpoint: {str(e)}")

def test_launch_endpoint():
    """Test the launch endpoint (should redirect)"""
    try:
        url = "https://provider-app-icbi.onrender.com/launch"
        print(f"\nTesting launch endpoint: {url}")
        
        response = requests.get(url, allow_redirects=False)
        
        if response.status_code in [302, 400, 500]:
            print("✅ Launch endpoint is responding (expected behavior without Epic parameters)")
            print(f"Status code: {response.status_code}")
        else:
            print(f"❌ Unexpected response from launch endpoint: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing launch endpoint: {str(e)}")

if __name__ == "__main__":
    print("Testing Epic FHIR Integration Endpoints")
    print("=" * 50)
    
    test_jwk_endpoint()
    test_launch_endpoint()
    
    print("\n" + "=" * 50)
    print("Test completed!") 