# Environment Variables Setup

Create a `.env` file in the project root with these variables:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Epic Backend Services Configuration
EPIC_BACKEND_CLIENT_ID=your_client_id_from_epic
EPIC_TOKEN_URL=https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token
EPIC_FHIR_BASE_URL=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
EPIC_PRIVATE_KEY_PATH=epic_backend_private_key.pem

# Optional: Test Patient ID (from Epic sandbox)
EPIC_TEST_PATIENT_ID=

# Database Encryption
ENCRYPTION_KEY=generate_with_fernet.generate_key()
```

## How to Get Epic Configuration:

### 1. EPIC_BACKEND_CLIENT_ID
- Go to https://fhir.epic.com/
- Select your Backend Services app
- Copy the **Client ID** shown in the app details

### 2. EPIC_TOKEN_URL
- For non-production: `https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token`
- For production: Check your Epic configuration

### 3. EPIC_FHIR_BASE_URL
- For non-production: `https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4`
- For production: Check your Epic configuration

### 4. EPIC_TEST_PATIENT_ID (Optional)
- Epic provides test patients in their sandbox
- Common test patient IDs: `Tbt3KuCY0B5PSrJvCu2j-PlK.aiHsu2xUjUM8bWpetXoB`
- Check Epic's documentation for more test patients
