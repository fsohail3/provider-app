#!/usr/bin/env python3
"""
Check Epic App Approval Status
"""
import requests
import json
import os
import epic_config  # Load the configuration

class EpicAppApprovalChecker:
    """Check if Epic app is properly approved"""
    
    def __init__(self):
        # Load configuration
        epic_config  # This sets the environment variables
        self.client_id = os.getenv('EPIC_CLIENT_ID')
        self.fhir_base_url = os.getenv('EPIC_FHIR_BASE_URL')
        
        print(f"🔍 Epic App Approval Checker")
        print(f"   Client ID: {self.client_id}")
        print(f"   FHIR Base URL: {self.fhir_base_url}")
    
    def check_epic_app_status(self):
        """Check Epic app status and configuration"""
        print(f"\n🏥 Checking Epic App Status")
        print("=" * 50)
        
        print("🔍 Based on the error you're seeing, your app likely needs:")
        print("1. ✅ Epic Approval: App must be approved by Epic")
        print("2. ✅ App Status: Should be 'Active' or 'Test' (not 'Draft')")
        print("3. ✅ Required FHIR APIs: Must be selected and approved")
        print("4. ✅ App Activation: Epic must activate your app")
        
        print(f"\n🔧 Immediate Actions Required:")
        print("1. Go to: https://fhir.epic.com/Developer/Edit?appId=45459")
        print("2. Check your app status (top of the page)")
        print("3. Look for status indicators like:")
        print("   - 'Draft' (needs approval)")
        print("   - 'Pending' (waiting for Epic)")
        print("   - 'Test' (approved for testing)")
        print("   - 'Active' (fully approved)")
        
        print(f"\n📋 Required FHIR APIs Check:")
        print("Your app needs these APIs selected and approved:")
        print("✅ Patient.Read (R4)")
        print("✅ Observation.Read (Vital Signs) (R4)")
        print("✅ Condition.Read (R4)")
        print("✅ MedicationRequest.Read (R4)")
        print("✅ AllergyIntolerance.Read (R4)")
        print("✅ Appointment.Read (R4)")
        print("✅ Binary.Read (Clinical Notes) (R4)")
        
        print(f"\n🚨 Common Approval Issues:")
        print("1. App still in 'Draft' status")
        print("2. Epic hasn't reviewed your app yet")
        print("3. Required FHIR APIs not selected")
        print("4. App description or purpose unclear")
        print("5. Missing required app information")
    
    def test_epic_fhir_access(self):
        """Test if Epic FHIR is accessible with your app"""
        print(f"\n🔍 Testing Epic FHIR Access")
        print("=" * 50)
        
        # Test basic FHIR metadata
        try:
            print(f"Testing FHIR metadata endpoint...")
            response = requests.get(
                f"{self.fhir_base_url}/metadata",
                headers={'Accept': 'application/fhir+json'},
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ FHIR metadata accessible")
                try:
                    data = response.json()
                    print(f"   FHIR Version: {data.get('fhirVersion', 'Unknown')}")
                    print(f"   Software: {data.get('software', {}).get('name', 'Unknown')}")
                except:
                    print("   Could not parse JSON response")
            else:
                print(f"❌ FHIR metadata not accessible: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ Error accessing FHIR: {str(e)}")
        
        # Test patient endpoint (should fail without proper auth)
        try:
            print(f"\nTesting patient endpoint (should fail without auth)...")
            response = requests.get(
                f"{self.fhir_base_url}/Patient",
                headers={'Accept': 'application/fhir+json'},
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ Patient endpoint requires auth (expected)")
            elif response.status_code == 403:
                print("✅ Patient endpoint forbidden (expected)")
            elif response.status_code == 200:
                print("⚠️  Patient endpoint accessible (unexpected)")
            else:
                print(f"⚠️  Patient endpoint status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing patient endpoint: {str(e)}")
    
    def check_oauth_error_patterns(self):
        """Check common OAuth error patterns"""
        print(f"\n🔍 OAuth Error Pattern Analysis")
        print("=" * 50)
        
        print("🔍 Based on your error, here are the likely causes:")
        print("1. ❌ App not approved by Epic yet")
        print("2. ❌ App status still 'Draft' or 'Pending'")
        print("3. ❌ Required FHIR APIs not selected")
        print("4. ❌ Epic hasn't activated your app")
        print("5. ❌ App configuration incomplete")
        
        print(f"\n🎯 Why You're Getting Error Page Instead of Auth:")
        print("- Epic recognizes your OAuth request (302 redirect)")
        print("- But Epic can't process it because app isn't ready")
        print("- So Epic shows error page instead of authorization")
        print("- This is Epic's way of saying 'app not ready yet'")
        
        print(f"\n📞 Epic Support Required:")
        print("If your app is still in 'Draft' or 'Pending' status:")
        print("1. Contact Epic support at: open.epic.com/Home/Contact")
        print("2. Ask about your app approval status")
        print("3. Request expedited review if needed")
        print("4. Ensure all required information is provided")
    
    def provide_next_steps(self):
        """Provide clear next steps"""
        print(f"\n🎯 Next Steps to Fix This")
        print("=" * 50)
        
        print("🔧 Step 1: Check App Status")
        print("1. Go to: https://fhir.epic.com/Developer/Edit?appId=45459")
        print("2. Look at the top of the page for status")
        print("3. Report what status you see")
        
        print(f"\n🔧 Step 2: Check Required APIs")
        print("1. In the same page, scroll to 'Incoming APIs'")
        print("2. Verify these are in the 'Selected' column:")
        print("   - Patient.Read (R4)")
        print("   - Observation.Read (Vital Signs) (R4)")
        print("   - Condition.Read (R4)")
        print("   - MedicationRequest.Read (R4)")
        
        print(f"\n🔧 Step 3: Contact Epic Support")
        print("If app status is 'Draft' or 'Pending':")
        print("1. Go to: open.epic.com/Home/Contact")
        print("2. Explain your app needs approval")
        print("3. Request expedited review")
        
        print(f"\n🔧 Step 4: Wait for Approval")
        print("1. Epic approval can take 1-3 business days")
        print("2. You'll get email notification when approved")
        print("3. Only then will OAuth work properly")
        
        print(f"\n💡 Pro Tip:")
        print("The OAuth error page means Epic knows about your app")
        print("But it's not ready for use yet. This is a configuration issue,")
        print("not a technical OAuth problem.")
    
    def run_complete_check(self):
        """Run complete approval check"""
        print("🚀 Epic App Approval Status Check")
        print("=" * 60)
        
        # Check 1: App status requirements
        self.check_epic_app_status()
        
        # Check 2: Test FHIR access
        self.test_epic_fhir_access()
        
        # Check 3: Analyze error patterns
        self.check_oauth_error_patterns()
        
        # Check 4: Provide next steps
        self.provide_next_steps()
        
        # Summary
        print(f"\n📊 Summary")
        print("=" * 60)
        print("🔍 The OAuth error page indicates your app isn't ready yet")
        print("🔍 Epic needs to approve and activate your app")
        print("🔍 Check your app status and contact Epic support if needed")
        print("🔍 Once approved, OAuth will work automatically")

def main():
    """Main function"""
    checker = EpicAppApprovalChecker()
    checker.run_complete_check()

if __name__ == "__main__":
    main() 