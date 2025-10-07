# Epic Backend Services OAuth 2.0 Package

## 📦 Package Contents

This package contains a complete, production-ready implementation of Epic Backend Services OAuth 2.0 authentication.

### Files Included:

1. **`epic_backend_auth.py`** - Main OAuth implementation (320 lines)
2. **`test_epic_backend_auth.py`** - Test suite (204 lines)
3. **`epic_backend_public_cert.pem`** - Sample X.509 certificate (you'll generate your own)
4. **`requirements.txt`** - Python dependencies
5. **`BACKEND_AUTH_SETUP.md`** - Complete setup instructions
6. **`ENV_SETUP.md`** - Environment configuration guide
7. **`QUICK_START.md`** - Quick reference guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Your Keys
```bash
# Generate private key
openssl genrsa -out epic_backend_private_key.pem 2048

# Generate X.509 certificate
openssl req -new -x509 -key epic_backend_private_key.pem -out epic_backend_public_cert.pem -days 3650 -subj "/CN=your-app-name"
```

### 3. Configure Environment
Create a `.env` file:
```bash
EPIC_BACKEND_CLIENT_ID=your_client_id_from_epic
EPIC_TOKEN_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
EPIC_FHIR_BASE_URL=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
EPIC_PRIVATE_KEY_PATH=epic_backend_private_key.pem
```

### 4. Upload Certificate to Epic
1. Copy your certificate: `cat epic_backend_public_cert.pem`
2. Go to https://fhir.epic.com/
3. Paste into "JWT Signing Public Key" field
4. Save

### 5. Test
```bash
python test_epic_backend_auth.py
```

## 📖 Documentation

- **BACKEND_AUTH_SETUP.md** - Detailed setup instructions
- **ENV_SETUP.md** - Environment variables
- **QUICK_START.md** - Quick reference

## ✨ Features

- ✅ OAuth 2.0 JWT Bearer flow
- ✅ Automatic token caching & refresh
- ✅ RS384 signing (Epic requirement)
- ✅ Comprehensive error handling
- ✅ Production-ready code
- ✅ Full test suite

## 🔧 Usage Example

```python
from epic_backend_auth import create_epic_backend_client

# Create authenticated client
auth = create_epic_backend_client()

# Get access token (automatically cached)
token = auth.get_access_token()

# Make FHIR API calls
patient = auth.get_fhir_resource('Patient', resource_id='patient-123')
metadata = auth.get_fhir_resource('metadata')
observations = auth.get_patient_observations('patient-123', category='vital-signs')
```

## 📊 Tested & Working

- ✅ Epic Sandbox Environment
- ✅ FHIR R4 (4.0.1)
- ✅ Token acquisition successful
- ✅ API calls working
- ✅ Token caching functional

## 🔒 Security Notes

⚠️ **IMPORTANT:**
- Keep `epic_backend_private_key.pem` secure
- Never commit private keys to git
- Add to `.gitignore`: `epic_backend_private_key.pem`
- Rotate keys periodically

## 📞 Support

For questions about this implementation, refer to:
- Epic Documentation: https://fhir.epic.com/
- SMART Backend Services: https://docs.intraconnects.com/docs/ehr-basics/epic/Auth/jwt/

## 🎯 Technical Details

- **Algorithm:** RS384
- **Key Size:** 2048-bit RSA
- **Token Lifetime:** 3600 seconds (1 hour)
- **JWT Claims:** iss, sub, aud, jti, exp, nbf, iat, kid
- **Python Version:** 3.7+

---

**Package Date:** October 2, 2025  
**Status:** Production Ready ✅
