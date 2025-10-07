# Epic Backend Services Authorization Setup

## Step 1: Generate RSA Key Pair with OpenSSL ✅ COMPLETED

Keys have been generated! Run these commands if you need to regenerate:

```bash
# Generate private key (2048-bit RSA)
openssl genrsa -out epic_backend_private_key.pem 2048

# Create X.509 certificate (this is what Epic needs)
openssl req -new -x509 -key epic_backend_private_key.pem -out epic_backend_public_cert.pem -days 3650 -subj "/CN=provider-app/O=Healthcare/C=US"

# View the certificate (this is what you'll upload to Epic)
cat epic_backend_public_cert.pem
```

## Step 2: Upload X.509 Certificate to Epic

1. Go to: https://fhir.epic.com/
2. Log in and select your **Backend Services** app
3. Find the **"JWT Signing Public Key"** field
4. Copy your certificate:
   ```bash
   cat epic_backend_public_cert.pem
   ```
5. Paste the ENTIRE content (including BEGIN CERTIFICATE/END CERTIFICATE lines) into Epic
6. The algorithm will be automatically detected (RS384)
7. Save your app configuration

## Step 3: Get Your Epic App Credentials

You'll need from Epic:
- **Client ID**: Your app's unique identifier
- **Token Endpoint**: Usually `https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token`
- **FHIR Base URL**: Usually `https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4`

## Step 4: Update .env File

Create/update your `.env` file (see `ENV_SETUP.md` for details):

```bash
# Epic Backend Services Configuration
EPIC_BACKEND_CLIENT_ID=your_client_id_here
EPIC_TOKEN_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
EPIC_FHIR_BASE_URL=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
EPIC_PRIVATE_KEY_PATH=epic_backend_private_key.pem
```

## Step 5: Test the Setup

Use the provided Python script to test authentication:
```bash
python test_epic_backend_auth.py
```

This will:
- ✅ Test JWT creation and signing
- ✅ Test access token retrieval
- ✅ Test FHIR API connectivity
- ✅ Display helpful error messages if something fails

## Security Notes

⚠️ **IMPORTANT:**
- `epic_backend_private_key.pem` - **NEVER SHARE OR COMMIT THIS!**
- `epic_backend_public_key.pem` - Safe to share, uploaded to Epic
- Keys are already in `.gitignore`

## Scopes for Backend Services

Request these system-level scopes in your Epic app:
- `system/Patient.read`
- `system/Observation.read`
- `system/Condition.read`
- `system/MedicationRequest.read`
- `system/AllergyIntolerance.read`
- `system/Procedure.read`

## Token Lifetime

- Backend service tokens typically last 1 hour
- The `EpicBackendAuth` class automatically caches tokens
- Tokens are refreshed automatically when expired

## Usage in Your Application

```python
from epic_backend_auth import create_epic_backend_client

# Create auth client from .env configuration
auth = create_epic_backend_client()

# Get access token (automatically cached)
token = auth.get_access_token()

# Search for patients
patients = auth.search_patients(family_name="Smith")

# Get patient by ID
patient = auth.get_fhir_resource('Patient', resource_id='patient-123')

# Get patient observations
observations = auth.get_patient_observations(
    patient_id='patient-123',
    category='vital-signs'
)
```

## Files Created

- ✅ `epic_backend_private_key.pem` - Private key (KEEP SECRET!)
- ✅ `epic_backend_public_cert.pem` - X.509 certificate
- ✅ `epic_backend_auth.py` - OAuth implementation
- ✅ `test_epic_backend_auth.py` - Test suite
- ✅ `ENV_SETUP.md` - Environment variables guide
