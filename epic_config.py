#!/usr/bin/env python3
"""
Epic FHIR Configuration for Real Testing
"""
import os

# Epic FHIR Configuration
EPIC_CONFIG = {
    "client_id": "4787c109-971b-4933-9483-27b240bd8361",  # Non-Production Client ID
    "fhir_base_url": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4",
    "auth_url": "https://fhir.epic.com/oauth2/authorize",
    "token_url": "https://fhir.epic.com/oauth2/token",
    "app_url": "https://provider-app-icbi.onrender.com",
    "redirect_uri": "https://provider-app-icbi.onrender.com/launch"
}

# Set environment variables for the session
os.environ['EPIC_CLIENT_ID'] = EPIC_CONFIG['client_id']
os.environ['EPIC_FHIR_BASE_URL'] = EPIC_CONFIG['fhir_base_url']
os.environ['EPIC_AUTH_URL'] = EPIC_CONFIG['auth_url']
os.environ['EPIC_TOKEN_URL'] = EPIC_CONFIG['token_url']

print("✅ Epic FHIR Configuration loaded:")
print(f"   Client ID: {EPIC_CONFIG['client_id'][:8]}...")
print(f"   FHIR Base URL: {EPIC_CONFIG['fhir_base_url']}")
print(f"   Auth URL: {EPIC_CONFIG['auth_url']}")
print(f"   App URL: {EPIC_CONFIG['app_url']}")
print(f"   Redirect URI: {EPIC_CONFIG['redirect_uri']}") 