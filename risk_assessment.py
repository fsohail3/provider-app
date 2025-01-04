class RiskAssessment:
    def __init__(self, medical_db):
        self.medical_db = medical_db

    async def assess_risks(self, patient_data, procedure_type=None):
        """Assess patient risks based on their data"""
        risks = []
        
        # Age-related risks
        if 'age' in patient_data:
            age_risks = self._assess_age_risks(patient_data['age'])
            risks.extend(age_risks)
        
        # Medical history risks
        if 'medicalHistory' in patient_data:
            history_risks = self._assess_medical_history(patient_data['medicalHistory'])
            risks.extend(history_risks)
        
        # Medication risks
        if 'medications' in patient_data:
            med_risks = self._assess_medication_risks(patient_data['medications'])
            risks.extend(med_risks)
        
        # Procedure-specific risks
        if procedure_type:
            proc_risks = self._assess_procedure_risks(procedure_type, patient_data)
            risks.extend(proc_risks)
        
        return risks

    def _assess_age_risks(self, age):
        """Assess risks based on patient age"""
        risks = []
        try:
            age = int(age)
            if age >= 65:
                risks.append({
                    "type": "age",
                    "severity": "moderate",
                    "description": "Elderly patient may have increased risk of complications"
                })
            if age >= 80:
                risks.append({
                    "type": "age",
                    "severity": "high",
                    "description": "Advanced age significantly increases risk of complications"
                })
        except ValueError:
            pass
        return risks

    def _assess_medical_history(self, history):
        """Assess risks based on medical history"""
        risks = []
        high_risk_conditions = [
            "diabetes", "hypertension", "heart disease", "copd",
            "kidney disease", "liver disease", "cancer"
        ]
        
        history_lower = history.lower()
        for condition in high_risk_conditions:
            if condition in history_lower:
                risks.append({
                    "type": "medical_history",
                    "severity": "high",
                    "description": f"Patient has history of {condition}"
                })
        
        return risks

    def _assess_medication_risks(self, medications):
        """Assess risks based on current medications"""
        risks = []
        high_risk_meds = [
            "warfarin", "heparin", "plavix", "aspirin",
            "metformin", "insulin"
        ]
        
        for med in medications:
            med_lower = med.lower()
            if med_lower in high_risk_meds:
                risks.append({
                    "type": "medication",
                    "severity": "moderate",
                    "description": f"Patient is taking {med}"
                })
        
        return risks

    def _assess_procedure_risks(self, procedure_type, patient_data):
        """Assess procedure-specific risks"""
        risks = []
        
        # Get contraindications from medical database
        contraindications = self.medical_db._check_contraindications(procedure_type, patient_data)
        
        for contra in contraindications:
            risks.append({
                "type": "procedure",
                "severity": "high",
                "description": f"Contraindication: {contra}"
            })
        
        return risks 