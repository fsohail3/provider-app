# Epic Backend Services - Quick Start Guide

## ✅ What's Been Created

### 1. Keys & Certificates
- ✅ `epic_backend_private_key.pem` - Your private RSA key (2048-bit)
- ✅ `epic_backend_public_cert.pem` - Your X.509 certificate for Epic

### 2. Python Implementation
- ✅ `epic_backend_auth.py` - Complete OAuth 2.0 JWT Bearer flow
- ✅ `test_epic_backend_auth.py` - Test suite for authentication

### 3. Documentation
- ✅ `BACKEND_AUTH_SETUP.md` - Detailed setup instructions
- ✅ `ENV_SETUP.md` - Environment variables guide
- ✅ `QUICK_START.md` - This file!

## 🚀 Quick Start (3 Steps)

### Step 1: Upload Certificate to Epic
```bash
# Display your certificate
cat epic_backend_public_cert.pem
```

Copy the output and:
1. Go to https://fhir.epic.com/
2. Select your Backend Services app
3. Paste into "JWT Signing Public Key" field
4. Save

### Step 2: Configure Environment
Create/update `.env` file:
```bash
EPIC_BACKEND_CLIENT_ID=<your_client_id_from_epic>
EPIC_TOKEN_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
EPIC_FHIR_BASE_URL=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
EPIC_PRIVATE_KEY_PATH=epic_backend_private_key.pem
```

### Step 3: Test Authentication
```bash
python test_epic_backend_auth.py
```

## 📝 Usage Example

```python
from epic_backend_auth import create_epic_backend_client

# Create authenticated client
auth = create_epic_backend_client()

# Get access token
token = auth.get_access_token()

# Make FHIR API calls
patient = auth.get_fhir_resource('Patient', resource_id='patient-123')
observations = auth.get_patient_observations(
    patient_id='patient-123',
    category='vital-signs'
)
```

## 🔍 How It Works

1. **Your App** creates a JWT token with your client ID
2. **Signs JWT** with your private key (RS384 algorithm)
3. **Sends JWT** to Epic's token endpoint
4. **Epic verifies** JWT with your public certificate
5. **Epic returns** access token (valid ~1 hour)
6. **Your App** uses access token for FHIR API calls

## 🎯 Key Features

- ✅ Automatic token caching (saves API calls)
- ✅ Automatic token refresh on expiry
- ✅ Retry logic for expired tokens
- ✅ Built-in FHIR helper methods
- ✅ Comprehensive error logging

## 📚 Available Scopes

```python
# Default scopes (auto-included):
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
```

## 🆘 Troubleshooting

### "Invalid JWT" Error
- ✅ Check certificate uploaded correctly to Epic
- ✅ Verify client ID matches in .env and Epic
- ✅ Ensure RS384 algorithm is accepted

### "Token Request Failed"
- ✅ Check token URL is correct
- ✅ Verify Epic app is approved
- ✅ Check network connectivity

### "FHIR Request Failed"
- ✅ Verify FHIR base URL
- ✅ Check requested scopes are approved
- ✅ Ensure resource/patient exists

## 📖 More Help

- `BACKEND_AUTH_SETUP.md` - Detailed setup guide
- `ENV_SETUP.md` - Environment configuration
- Epic Docs: https://fhir.epic.com/Documentation

## 🔒 Security Notes

⚠️ **NEVER commit `epic_backend_private_key.pem` to git!**

The private key is already in `.gitignore` for protection.
