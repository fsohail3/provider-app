class ChecklistGenerator:
    def __init__(self, medical_db, risk_assessor):
        self.medical_db = medical_db
        self.risk_assessor = risk_assessor

    async def generate_checklist(self, procedure_type, patient_data):
        """Generate a comprehensive procedure checklist"""
        # Get base checklist from medical database
        base_checklist = self.medical_db._generate_procedure_checklist(procedure_type)
        
        # Get patient-specific risks
        risks = await self.risk_assessor.assess_risks(patient_data, procedure_type)
        
        # Add risk-specific items to checklist
        risk_items = self._generate_risk_specific_items(risks)
        
        # Combine everything into final checklist
        final_checklist = {
            **base_checklist,
            'patient_specific_considerations': risk_items,
            'identified_risks': risks
        }
        
        return final_checklist

    def _generate_risk_specific_items(self, risks):
        """Generate checklist items based on identified risks"""
        items = []
        
        for risk in risks:
            if risk['type'] == 'age':
                items.append("Verify appropriate monitoring frequency for age")
            elif risk['type'] == 'medical_history':
                items.append(f"Review management plan for {risk['description']}")
            elif risk['type'] == 'medication':
                items.append(f"Check medication timing and interactions")
            elif risk['type'] == 'procedure':
                items.append(f"Address contraindication: {risk['description']}")
        
        return items 