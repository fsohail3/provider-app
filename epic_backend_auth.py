#!/usr/bin/env python3
"""
Epic Backend Services Authorization (OAuth 2.0 JWT Bearer Flow)
Implements server-to-server authentication for Epic FHIR API
"""
import os
import time
import jwt
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EpicBackendAuth:
    """Handle Epic Backend Services OAuth 2.0 authentication"""
    
    def __init__(
        self,
        client_id: str,
        private_key_path: str,
        token_url: str,
        fhir_base_url: str
    ):
        """
        Initialize Epic Backend Auth
        
        Args:
            client_id: Your Epic app's client ID
            private_key_path: Path to your private key PEM file
            token_url: Epic's token endpoint URL
            fhir_base_url: Epic's FHIR base URL
        """
        self.client_id = client_id
        self.private_key_path = private_key_path
        self.token_url = token_url
        self.fhir_base_url = fhir_base_url
        
        # Load private key
        self.private_key = self._load_private_key()
        
        # Token cache
        self.access_token = None
        self.token_expires_at = None
    
    def _load_private_key(self):
        """Load the RSA private key from ENV (EPIC_PRIVATE_KEY_PEM) or PEM file"""
        pem_env = os.getenv('EPIC_PRIVATE_KEY_PEM')
        try:
            if pem_env:
                private_key = serialization.load_pem_private_key(
                    pem_env.encode('utf-8'),
                    password=None,
                    backend=default_backend()
                )
                logger.info("✅ Private key loaded from environment variable EPIC_PRIVATE_KEY_PEM")
                return private_key
            # Fallback to file path
            with open(self.private_key_path, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,
                    backend=default_backend()
                )
            logger.info("✅ Private key loaded from file path")
            return private_key
        except Exception as e:
            logger.error(f"❌ Error loading private key: {str(e)}")
            raise
    
    def _create_jwt_assertion(self, scopes: list) -> str:
        """
        Create and sign a JWT assertion for Epic authentication
        
        Args:
            scopes: List of requested scopes (e.g., ['system/Patient.read'])
        
        Returns:
            Signed JWT token string
        """
        now = int(time.time())
        
        # JWT claims for Epic Backend Services
        claims = {
            'iss': self.client_id,  # Issuer (your client ID)
            'sub': self.client_id,  # Subject (your client ID)
            'aud': self.token_url,  # Audience (Epic's token URL)
            'jti': f"{self.client_id}-{now}",  # Unique JWT ID
            'exp': now + 240,  # Expiration (4 minutes)
            'nbf': now - 60,  # Not before (1 minute ago)
            'iat': now,  # Issued at
        }
        
        # Sign the JWT with RS384 algorithm (Epic requirement)
        try:
            jwt_token = jwt.encode(
                claims,
                self.private_key,
                algorithm='RS384',
                headers={'kid': self.client_id}  # Epic recommends kid in JWT header
            )
            logger.info("✅ JWT assertion created and signed")
            return jwt_token
        except Exception as e:
            logger.error(f"❌ Error creating JWT: {str(e)}")
            raise
    
    def get_access_token(self, scopes: list = None, force_refresh: bool = False) -> Optional[str]:
        """
        Get an access token from Epic using JWT Bearer flow
        
        Args:
            scopes: List of FHIR scopes (default: system/*.read)
            force_refresh: Force token refresh even if cached token is valid
        
        Returns:
            Access token string or None if failed
        """
        # Check if we have a valid cached token
        if not force_refresh and self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                logger.info("✅ Using cached access token")
                return self.access_token
        
        # Default scopes for backend services
        if scopes is None:
            scopes = [
                'system/Patient.read',
                'system/Observation.read',
                'system/Condition.read',
                'system/MedicationRequest.read',
                'system/AllergyIntolerance.read',
                'system/Procedure.read',
                'system/Encounter.read',
                'system/DiagnosticReport.read',
                'system/DocumentReference.read'
            ]
        
        try:
            # Create JWT assertion
            jwt_assertion = self._create_jwt_assertion(scopes)
            
            # Prepare token request
            token_data = {
                'grant_type': 'client_credentials',
                'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                'client_assertion': jwt_assertion,
                'scope': ' '.join(scopes)
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            logger.info(f"🔄 Requesting access token from Epic...")
            logger.info(f"   Token URL: {self.token_url}")
            logger.info(f"   Scopes: {', '.join(scopes)}")
            
            # Request access token
            response = requests.post(
                self.token_url,
                data=token_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                token_response = response.json()
                
                self.access_token = token_response.get('access_token')
                expires_in = token_response.get('expires_in', 3600)
                
                # Cache token with 5-minute buffer before expiration
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                
                logger.info(f"✅ Access token obtained successfully!")
                logger.info(f"   Token type: {token_response.get('token_type')}")
                logger.info(f"   Expires in: {expires_in} seconds")
                logger.info(f"   Scope: {token_response.get('scope')}")
                
                return self.access_token
            else:
                logger.error(f"❌ Token request failed!")
                logger.error(f"   Status code: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting access token: {str(e)}")
            return None
    
    def get_fhir_resource(self, resource_type: str, resource_id: str = None, params: Dict = None) -> Optional[Dict]:
        """
        Make a FHIR API request with automatic token management
        
        Args:
            resource_type: FHIR resource type (e.g., 'Patient', 'Observation')
            resource_id: Optional resource ID for specific resource
            params: Optional query parameters
        
        Returns:
            FHIR resource as dictionary or None
        """
        # Ensure we have a valid access token
        access_token = self.get_access_token()
        if not access_token:
            logger.error("❌ No valid access token available")
            return None
        
        try:
            # Build URL
            if resource_id:
                url = f"{self.fhir_base_url}/{resource_type}/{resource_id}"
            else:
                url = f"{self.fhir_base_url}/{resource_type}"
            
            # Headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/fhir+json',
                'Content-Type': 'application/fhir+json'
            }
            
            logger.info(f"🔄 FHIR Request: {resource_type}")
            
            # Make request
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ {resource_type}: Success")
                return data
            elif response.status_code == 401:
                # Token expired, retry once with fresh token
                logger.warning("⚠️ Token expired, refreshing...")
                access_token = self.get_access_token(force_refresh=True)
                if access_token:
                    headers['Authorization'] = f'Bearer {access_token}'
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                    if response.status_code == 200:
                        return response.json()
                
                logger.error(f"❌ Authentication failed even after refresh")
                return None
            else:
                logger.error(f"❌ FHIR request failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error making FHIR request: {str(e)}")
            return None
    
    def search_patients(self, family_name: str = None, given_name: str = None, 
                       birthdate: str = None, identifier: str = None) -> Optional[Dict]:
        """
        Search for patients
        
        Args:
            family_name: Patient's family name
            given_name: Patient's given name
            birthdate: Patient's birthdate (YYYY-MM-DD)
            identifier: Patient identifier
        
        Returns:
            FHIR Bundle with search results
        """
        params = {}
        if family_name:
            params['family'] = family_name
        if given_name:
            params['given'] = given_name
        if birthdate:
            params['birthdate'] = birthdate
        if identifier:
            params['identifier'] = identifier
        
        return self.get_fhir_resource('Patient', params=params)
    
    def get_patient_observations(self, patient_id: str, category: str = None) -> Optional[Dict]:
        """
        Get observations for a patient
        
        Args:
            patient_id: Patient FHIR ID
            category: Observation category (e.g., 'vital-signs', 'laboratory')
        
        Returns:
            FHIR Bundle with observations
        """
        params = {'patient': patient_id}
        if category:
            params['category'] = category
        
        return self.get_fhir_resource('Observation', params=params)


# Convenience function to create auth client from environment variables
def create_epic_backend_client() -> EpicBackendAuth:
    """
    Create Epic Backend Auth client from environment variables
    
    Required environment variables:
        EPIC_BACKEND_CLIENT_ID
        EPIC_TOKEN_URL
        EPIC_FHIR_BASE_URL
        EPIC_PRIVATE_KEY_PATH (optional, defaults to epic_backend_private_key.pem)
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    client_id = os.getenv('EPIC_BACKEND_CLIENT_ID')
    token_url = os.getenv('EPIC_TOKEN_URL')
    fhir_base_url = os.getenv('EPIC_FHIR_BASE_URL')
    private_key_path = os.getenv('EPIC_PRIVATE_KEY_PATH', 'epic_backend_private_key.pem')
    
    if not all([client_id, token_url, fhir_base_url]):
        raise ValueError("Missing required environment variables. Check your .env file.")
    
    return EpicBackendAuth(
        client_id=client_id,
        private_key_path=private_key_path,
        token_url=token_url,
        fhir_base_url=fhir_base_url
    )


