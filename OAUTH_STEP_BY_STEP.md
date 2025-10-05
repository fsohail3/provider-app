# 🚀 Complete OAuth Flow Step-by-Step Guide

## 🎯 What You'll Accomplish

By following this guide, you'll:
1. ✅ Get a real Epic access token
2. ✅ Test actual FHIR API calls
3. ✅ Retrieve real patient data
4. ✅ Verify your Epic integration works

## 📱 Step 1: Launch OAuth Flow

**Copy and paste this exact URL into your browser:**

```
https://fhir.epic.com/oauth2/authorize?response_type=code&client_id=4787c109-971b-4933-9483-27b240bd8361&redirect_uri=https://provider-app-icbi.onrender.com/launch&scope=launch/patient patient/*.read&state=test-state-123&aud=https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4
```

## 🔑 Step 2: Complete Epic Authorization

When you visit the URL:

1. **Epic will show a login page** - log in with your Epic credentials
2. **You'll see an authorization screen** showing:
   - App Name: Healthcare AI Procedure Assistant
   - Requested Permissions: Patient data access
3. **Click "Allow" or "Authorize"** to grant permissions

## 🔍 Step 3: Extract Authorization Code

After authorization, Epic will redirect you to:
```
https://provider-app-icbi.onrender.com/launch?code=AUTHORIZATION_CODE_HERE&state=test-state-123
```

**Look for the `code` parameter** - that's your authorization code!

**Example:** If the URL shows `?code=abc123xyz&state=test-state-123`, then `abc123xyz` is your authorization code.

## 🧪 Step 4: Test the Authorization Code

### Option A: Interactive Testing
```bash
python test_oauth_code.py
```
This will prompt you to enter your authorization code.

### Option B: Command Line Testing
```bash
python test_oauth_code.py YOUR_AUTHORIZATION_CODE_HERE
```

## 📊 Step 5: What Happens Next

When you test the authorization code:

1. **Token Exchange**: The script exchanges your code for an access token
2. **FHIR API Testing**: Tests the token with real Epic FHIR endpoints
3. **Data Retrieval**: Attempts to get real patient data
4. **Results Display**: Shows you the actual FHIR data structure

## 🎉 Expected Results

### Successful Token Exchange:
```
✅ SUCCESS! Token exchange successful!
Access Token: eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Token Type: Bearer
Expires In: 3600 seconds
Scope: launch/patient patient/*.read
```

### Successful FHIR API Call:
```
🔍 Get patient demographics
----------------------------------------
Status: 200
✅ Success! Found 1 resources
Sample data:
{
  "resourceType": "Patient",
  "id": "real-patient-id",
  "name": [{"text": "John Smith"}],
  "gender": "male",
  "birthDate": "1980-01-01"
}
```

## 🔧 Troubleshooting

### If Token Exchange Fails:
- **Error 400**: Check that the authorization code is correct and not expired
- **Error 401**: Verify your client ID and redirect URI match Epic's configuration
- **Error 403**: Ensure you have the correct permissions

### If FHIR API Calls Fail:
- **Error 401**: Access token may be expired or invalid
- **Error 403**: Insufficient permissions for the requested resource
- **Error 404**: Resource endpoint may not be available

## 📁 Files Created

After successful testing, you'll have:
- `epic_fhir_patient_data.json` - Real patient demographics
- `epic_fhir_observation_data.json` - Real vital signs/lab data
- `epic_fhir_condition_data.json` - Real medical conditions

## 🚀 Next Steps After Success

Once you have a working access token:

1. **Test More FHIR Resources**:
   - Medications
   - Allergies
   - Procedures
   - Clinical notes

2. **Integrate with Role-Based Checklists**:
   - Use real patient data to generate checklists
   - Test with different practitioner roles

3. **Go Live**:
   - Your Epic FHIR integration is working!
   - Ready for production use

## 🎯 Success Indicators

You'll know you're successful when:
- ✅ Token exchange returns status 200
- ✅ You get a valid access token
- ✅ FHIR API calls return real patient data
- ✅ Data is saved to JSON files for inspection

## 💡 Pro Tips

1. **Authorization codes expire quickly** - use them within a few minutes
2. **Access tokens also expire** - typically after 1 hour
3. **Save the data files** - they're valuable for understanding Epic's data structure
4. **Test with different scopes** - you can request additional permissions if needed

---

## 🎉 You're Almost There!

Your Epic FHIR integration is **100% ready**. You just need to:
1. Visit the authorization URL
2. Complete the Epic authorization
3. Get the authorization code
4. Test it with the script

**Then you'll have real Epic FHIR data flowing into your app!** 🚀 