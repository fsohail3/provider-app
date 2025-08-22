# Epic FHIR Integration Documentation

## Overview

This application now supports Epic FHIR integration through SMART-on-FHIR, allowing healthcare providers to launch the app directly from Epic with patient context.

## Features

- **SMART App Launch**: Seamless integration with Epic EHR
- **Patient Data Integration**: Auto-population of patient information
- **JWK Authentication**: Secure OAuth 2.0 with JSON Web Keys
- **FHIR R4 Support**: Latest FHIR standard compliance

## Endpoints

### JWK Endpoint
- **URL**: `/.well-known/jwks.json`
- **Method**: GET
- **Purpose**: Provides public keys for Epic authentication
- **Response**: JSON Web Key Set (JWKS) format

### Launch Endpoint
- **URL**: `/launch`
- **Method**: GET
- **Purpose**: Handles Epic SMART App Launch
- **Parameters**: 
  - `iss`: Epic FHIR server URL
  - `launch`: Launch token
  - `state`: State parameter

### App Endpoint
- **URL**: `/app`
- **Method**: GET
- **Purpose**: Main application with Epic patient context
- **Parameters**: `epic_patient`: Patient ID from Epic

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Epic FHIR Configuration
EPIC_CLIENT_ID=your_epic_client_id
EPIC_CLIENT_SECRET=your_epic_client_secret
```

### Epic App Registration

1. **Register at Epic on FHIR**: [fhir.epic.com](https://fhir.epic.com/)
2. **App Configuration**:
   - Application Name: `Healthcare AI Procedure Assistant`
   - Application Audience: `Clinicians or Administrative Users`
   - Public Documentation URL: `https://provider-app-icbi.onrender.com`
   - Redirect URI: `https://provider-app-icbi.onrender.com/launch`
   - Is Confidential Client: ✅ **Selected**
   - Requires Persistent Access: ✅ **Selected**

3. **Required FHIR APIs (R4)**:
   - `Patient.Read (R4)`
   - `Observation.Read (Vital Signs) (R4)`
   - `AllergyIntolerance.Read (R4)`
   - `MedicationRequest.Read (R4)`
   - `Condition.Read (R4)`
   - `Procedure.Read (R4)`

4. **JWK Configuration**:
   - Non-Production JWK Set URL: `https://provider-app-icbi.onrender.com/.well-known/jwks.json`
   - Production JWK Set URL: `https://provider-app-icbi.onrender.com/.well-known/jwks.json`

## Security

### Key Management
- RSA 2048-bit key pair generated automatically
- Private key stored securely in `epic_private_key.pem`
- Public key exposed via JWK endpoint
- Keys excluded from version control

### Authentication Flow
1. Epic launches app with launch token
2. App exchanges launch token for access token
3. App fetches patient data using access token
4. Patient context integrated into app workflow

## Testing

### Local Testing
```bash
python test_jwk.py
```

### Epic Sandbox Testing
1. Complete Epic app registration
2. Test launch flow with Epic sandbox
3. Verify patient data integration
4. Test procedure guidance with real Epic data

## Deployment

### Render Deployment
The app is automatically deployed to Render with:
- HTTPS enabled
- JWK endpoint accessible
- Launch endpoint configured
- Epic integration ready

### Production Considerations
- Ensure SSL certificates are valid
- Monitor JWK endpoint availability
- Log Epic integration events
- Handle Epic API rate limits

## Troubleshooting

### Common Issues

1. **JWK Endpoint Not Accessible**
   - Verify HTTPS is enabled
   - Check firewall settings
   - Ensure endpoint is publicly accessible

2. **Launch Token Exchange Fails**
   - Verify client credentials
   - Check redirect URI configuration
   - Ensure Epic app is approved

3. **Patient Data Not Loading**
   - Verify FHIR API permissions
   - Check access token validity
   - Review Epic FHIR server configuration

### Logs
Check application logs for detailed error information:
```bash
tail -f logs/healthcare.log
```

## Support

For Epic integration support:
- Email: privacy@provider.com
- Epic Developer Documentation: [fhir.epic.com](https://fhir.epic.com/)
- SMART-on-FHIR Documentation: [docs.smarthealthit.org](https://docs.smarthealthit.org/) 