#!/usr/bin/env python3
"""
Enhanced Epic FHIR Client for Healthcare AI Procedure Assistant
Handles all Epic FHIR API calls, data processing, and role-based logic
"""
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EpicFHIRClient:
    """Enhanced Epic FHIR client with comprehensive API support"""
    
    def __init__(self, access_token: str, patient_id: str, fhir_base_url: str):
        self.access_token = access_token
        self.patient_id = patient_id
        self.fhir_base_url = fhir_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/fhir+json',
            'Content-Type': 'application/fhir+json'
        })
        
        # Cache for API responses
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        
    def _make_request(self, resource_type: str, params: Dict = None) -> Optional[Dict]:
        """Make a FHIR API request with error handling"""
        try:
            url = f"{self.fhir_base_url}/{resource_type}"
            
            if params is None:
                params = {}
            
            # Add patient filter if not already present
            if 'patient' not in params:
                params['patient'] = self.patient_id
                
            logger.info(f"Making FHIR request: {resource_type} with params: {params}")
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ {resource_type}: Found {data.get('total', 0)} resources")
                return data
            else:
                logger.warning(f"⚠️ {resource_type}: Status {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error in {resource_type}: {str(e)}")
            return None
    
    def get_patient_demographics(self) -> Dict:
        """Get patient demographics"""
        logger.info("📋 Fetching patient demographics")
        data = self._make_request("Patient")
        
        if data and 'entry' in data and len(data['entry']) > 0:
            patient = data['entry'][0]['resource']
            return {
                'id': patient.get('id'),
                'name': self._extract_name(patient.get('name', [])),
                'gender': patient.get('gender'),
                'birth_date': patient.get('birthDate'),
                'age': self._calculate_age(patient.get('birthDate')),
                'address': self._extract_address(patient.get('address', [])),
                'phone': self._extract_phone(patient.get('telecom', [])),
                'marital_status': patient.get('maritalStatus', {}).get('text'),
                'race': self._extract_race(patient.get('extension', [])),
                'ethnicity': self._extract_ethnicity(patient.get('extension', []))
            }
        return {}
    
    def get_vital_signs(self) -> List[Dict]:
        """Get patient vital signs"""
        logger.info("💓 Fetching vital signs")
        data = self._make_request("Observation", {"category": "vital-signs"})
        
        vitals = []
        if data and 'entry' in data:
            for entry in data['entry']:
                obs = entry['resource']
                vital = {
                    'type': self._extract_vital_type(obs.get('code', {})),
                    'value': self._extract_value(obs),
                    'unit': self._extract_unit(obs),
                    'date': obs.get('effectiveDateTime'),
                    'status': obs.get('status')
                }
                if vital['value']:
                    vitals.append(vital)
        
        return vitals
    
    def get_medical_history(self) -> List[Dict]:
        """Get patient medical history (conditions)"""
        logger.info("📚 Fetching medical history")
        data = self._make_request("Condition", {"category": "problem-list-item"})
        
        conditions = []
        if data and 'entry' in data:
            for entry in data['entry']:
                condition = entry['resource']
                conditions.append({
                    'id': condition.get('id'),
                    'code': self._extract_code_text(condition.get('code', {})),
                    'status': condition.get('clinicalStatus', {}).get('text'),
                    'severity': condition.get('severity', {}).get('text'),
                    'onset_date': condition.get('onsetDateTime'),
                    'category': condition.get('category', [{}])[0].get('text'),
                    'notes': self._extract_notes(condition.get('note', []))
                })
        
        return conditions
    
    def get_reason_for_visit(self) -> List[Dict]:
        """Get reason for visit (encounter diagnoses)"""
        logger.info("🏥 Fetching reason for visit")
        data = self._make_request("Condition", {"category": "encounter-diagnosis"})
        
        reasons = []
        if data and 'entry' in data:
            for entry in data['entry']:
                condition = entry['resource']
                reasons.append({
                    'id': condition.get('id'),
                    'code': self._extract_code_text(condition.get('code', {})),
                    'status': condition.get('clinicalStatus', {}).get('text'),
                    'onset_date': condition.get('onsetDateTime'),
                    'notes': self._extract_notes(condition.get('note', []))
                })
        
        return reasons
    
    def get_medications(self) -> List[Dict]:
        """Get patient medications"""
        logger.info("💊 Fetching medications")
        data = self._make_request("MedicationRequest")
        
        medications = []
        if data and 'entry' in data:
            for entry in data['entry']:
                med = entry['resource']
                medications.append({
                    'id': med.get('id'),
                    'name': self._extract_medication_name(med.get('medicationCodeableConcept', {})),
                    'status': med.get('status'),
                    'intent': med.get('intent'),
                    'dosage': self._extract_dosage(med.get('dosageInstruction', [])),
                    'frequency': self._extract_frequency(med.get('dosageInstruction', [])),
                    'start_date': med.get('authoredOn'),
                    'prescriber': self._extract_prescriber(med.get('requester', {})),
                    'notes': self._extract_notes(med.get('note', []))
                })
        
        return medications
    
    def get_labs(self) -> List[Dict]:
        """Get laboratory results"""
        logger.info("🔬 Fetching laboratory results")
        data = self._make_request("Observation", {"category": "laboratory"})
        
        labs = []
        if data and 'entry' in data:
            for entry in data['entry']:
                lab = entry['resource']
                labs.append({
                    'id': lab.get('id'),
                    'name': self._extract_code_text(lab.get('code', {})),
                    'value': self._extract_value(lab),
                    'unit': self._extract_unit(lab),
                    'reference_range': self._extract_reference_range(lab),
                    'status': lab.get('status'),
                    'date': lab.get('effectiveDateTime'),
                    'abnormal': self._is_abnormal(lab)
                })
        
        return labs
    
    def get_surgical_history(self) -> List[Dict]:
        """Get patient reported surgical history"""
        logger.info("🔪 Fetching surgical history")
        data = self._make_request("Procedure", {"category": "patient-reported-surgical-history"})
        
        surgeries = []
        if data and 'entry' in data:
            for entry in data['entry']:
                surgery = entry['resource']
                surgeries.append({
                    'id': surgery.get('id'),
                    'name': self._extract_code_text(surgery.get('code', {})),
                    'status': surgery.get('status'),
                    'date': surgery.get('performedDateTime'),
                    'performer': self._extract_performer(surgery.get('performer', [])),
                    'location': surgery.get('location', {}).get('display'),
                    'notes': self._extract_notes(surgery.get('note', []))
                })
        
        return surgeries
    
    def get_surgeries(self) -> List[Dict]:
        """Get documented surgeries"""
        logger.info("🏥 Fetching documented surgeries")
        data = self._make_request("Procedure", {"category": "surgery"})
        
        surgeries = []
        if data and 'entry' in data:
            for entry in data['entry']:
                surgery = entry['resource']
                surgeries.append({
                    'id': surgery.get('id'),
                    'name': self._extract_code_text(surgery.get('code', {})),
                    'status': surgery.get('status'),
                    'date': surgery.get('performedDateTime'),
                    'performer': self._extract_performer(surgery.get('performer', [])),
                    'location': surgery.get('location', {}).get('display'),
                    'outcome': surgery.get('outcome', {}).get('text'),
                    'notes': self._extract_notes(surgery.get('note', []))
                })
        
        return surgeries
    
    def get_allergies(self) -> List[Dict]:
        """Get patient allergies"""
        logger.info("⚠️ Fetching allergies")
        data = self._make_request("AllergyIntolerance")
        
        allergies = []
        if data and 'entry' in data:
            for entry in data['entry']:
                allergy = entry['resource']
                allergies.append({
                    'id': allergy.get('id'),
                    'substance': self._extract_code_text(allergy.get('code', {})),
                    'severity': allergy.get('criticality'),
                    'reaction': self._extract_reactions(allergy.get('reaction', [])),
                    'onset_date': allergy.get('onsetDateTime'),
                    'status': allergy.get('clinicalStatus', {}).get('text'),
                    'notes': self._extract_notes(allergy.get('note', []))
                })
        
        return allergies
    
    def get_practitioner_role(self) -> Dict:
        """Get practitioner role information"""
        logger.info("👨‍⚕️ Fetching practitioner role")
        data = self._make_request("PractitionerRole")
        
        if data and 'entry' in data and len(data['entry']) > 0:
            role = data['entry'][0]['resource']
            return {
                'id': role.get('id'),
                'role': self._extract_code_text(role.get('code', {})),
                'specialty': [self._extract_code_text(spec) for spec in role.get('specialty', [])],
                'organization': role.get('organization', {}).get('display'),
                'practitioner': self._extract_practitioner_name(role.get('practitioner', {})),
                'active': role.get('active', True)
            }
        return {}
    
    def get_clinical_notes(self) -> List[Dict]:
        """Get clinical notes"""
        logger.info("📝 Fetching clinical notes")
        data = self._make_request("DocumentReference", {"type": "clinical-notes"})
        
        notes = []
        if data and 'entry' in data:
            for entry in data['entry']:
                doc = entry['resource']
                notes.append({
                    'id': doc.get('id'),
                    'type': self._extract_code_text(doc.get('type', {})),
                    'title': doc.get('title'),
                    'date': doc.get('date'),
                    'author': self._extract_author(doc.get('author', [])),
                    'content': self._extract_content(doc.get('content', [])),
                    'status': doc.get('status')
                })
        
        return notes
    
    def get_appointments(self) -> List[Dict]:
        """Get patient appointments"""
        logger.info("📅 Fetching appointments")
        data = self._make_request("Appointment")
        
        appointments = []
        if data and 'entry' in data:
            for entry in data['entry']:
                apt = entry['resource']
                appointments.append({
                    'id': apt.get('id'),
                    'type': self._extract_code_text(apt.get('serviceType', [{}])[0]),
                    'status': apt.get('status'),
                    'start_time': apt.get('start'),
                    'end_time': apt.get('end'),
                    'participant': self._extract_participants(apt.get('participant', [])),
                    'description': apt.get('description'),
                    'location': apt.get('location', [{}])[0].get('display')
                })
        
        return appointments
    
    def get_social_determinants(self) -> List[Dict]:
        """Get social determinants of health"""
        logger.info("🏠 Fetching social determinants")
        data = self._make_request("Observation", {"category": "social-history"})
        
        sdoh = []
        if data and 'entry' in data:
            for entry in data['entry']:
                obs = entry['resource']
                sdoh.append({
                    'id': obs.get('id'),
                    'type': self._extract_code_text(obs.get('code', {})),
                    'value': self._extract_value(obs),
                    'date': obs.get('effectiveDateTime'),
                    'status': obs.get('status')
                })
        
        return sdoh
    
    def get_comprehensive_patient_data(self) -> Dict:
        """Get all patient data in one comprehensive call"""
        logger.info("🔄 Fetching comprehensive patient data")
        
        start_time = datetime.now()
        
        # Fetch all data in parallel (simplified for now)
        patient_data = {
            'demographics': self.get_patient_demographics(),
            'vital_signs': self.get_vital_signs(),
            'medical_history': self.get_medical_history(),
            'reason_for_visit': self.get_reason_for_visit(),
            'medications': self.get_medications(),
            'labs': self.get_labs(),
            'surgical_history': self.get_surgical_history(),
            'surgeries': self.get_surgeries(),
            'allergies': self.get_allergies(),
            'practitioner_role': self.get_practitioner_role(),
            'clinical_notes': self.get_clinical_notes(),
            'appointments': self.get_appointments(),
            'social_determinants': self.get_social_determinants(),
            'fetch_time': datetime.now().isoformat(),
            'total_fetch_time_seconds': (datetime.now() - start_time).total_seconds()
        }
        
        logger.info(f"✅ Comprehensive data fetch completed in {patient_data['total_fetch_time_seconds']:.2f} seconds")
        
        return patient_data
    
    # Helper methods for data extraction
    def _extract_name(self, names: List) -> str:
        """Extract patient name from FHIR name array"""
        if names and len(names) > 0:
            name = names[0]
            parts = []
            if name.get('prefix'):
                parts.extend(name['prefix'])
            if name.get('given'):
                parts.extend(name['given'])
            if name.get('family'):
                parts.append(name['family'])
            if name.get('suffix'):
                parts.extend(name['suffix'])
            return ' '.join(parts)
        return "Unknown"
    
    def _extract_address(self, addresses: List) -> str:
        """Extract address from FHIR address array"""
        if addresses and len(addresses) > 0:
            addr = addresses[0]
            parts = []
            if addr.get('line'):
                parts.extend(addr['line'])
            if addr.get('city'):
                parts.append(addr['city'])
            if addr.get('state'):
                parts.append(addr['state'])
            if addr.get('postalCode'):
                parts.append(addr['postalCode'])
            return ', '.join(parts)
        return "Unknown"
    
    def _extract_phone(self, telecom: List) -> str:
        """Extract phone from FHIR telecom array"""
        for contact in telecom:
            if contact.get('system') == 'phone':
                return contact.get('value', 'Unknown')
        return "Unknown"
    
    def _extract_race(self, extensions: List) -> str:
        """Extract race from FHIR extensions"""
        for ext in extensions:
            if ext.get('url') == 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-race':
                return ext.get('valueCodeableConcept', {}).get('text', 'Unknown')
        return "Unknown"
    
    def _extract_ethnicity(self, extensions: List) -> str:
        """Extract ethnicity from FHIR extensions"""
        for ext in extensions:
            if ext.get('url') == 'http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity':
                return ext.get('valueCodeableConcept', {}).get('text', 'Unknown')
        return "Unknown"
    
    def _calculate_age(self, birth_date: str) -> int:
        """Calculate age from birth date"""
        if birth_date:
            try:
                birth = datetime.strptime(birth_date, '%Y-%m-%d')
                today = datetime.now()
                return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            except:
                return 0
        return 0
    
    def _extract_vital_type(self, code: Dict) -> str:
        """Extract vital sign type from code"""
        return code.get('text', code.get('coding', [{}])[0].get('display', 'Unknown'))
    
    def _extract_value(self, obs: Dict) -> str:
        """Extract value from observation"""
        if 'valueQuantity' in obs:
            return str(obs['valueQuantity'].get('value', ''))
        elif 'valueString' in obs:
            return obs['valueString']
        elif 'valueCodeableConcept' in obs:
            return self._extract_code_text(obs['valueCodeableConcept'])
        return ""
    
    def _extract_unit(self, obs: Dict) -> str:
        """Extract unit from observation"""
        if 'valueQuantity' in obs:
            return obs['valueQuantity'].get('unit', '')
        return ""
    
    def _extract_code_text(self, code: Dict) -> str:
        """Extract text from codeable concept"""
        return code.get('text', code.get('coding', [{}])[0].get('display', 'Unknown'))
    
    def _extract_notes(self, notes: List) -> str:
        """Extract notes text"""
        if notes and len(notes) > 0:
            return notes[0].get('text', '')
        return ""
    
    def _extract_medication_name(self, med: Dict) -> str:
        """Extract medication name"""
        return self._extract_code_text(med)
    
    def _extract_dosage(self, dosage: List) -> str:
        """Extract dosage information"""
        if dosage and len(dosage) > 0:
            dose = dosage[0]
            if 'doseAndRate' in dose and len(dose['doseAndRate']) > 0:
                return str(dose['doseAndRate'][0].get('doseQuantity', {}).get('value', ''))
        return ""
    
    def _extract_frequency(self, dosage: List) -> str:
        """Extract frequency information"""
        if dosage and len(dosage) > 0:
            dose = dosage[0]
            if 'timing' in dose:
                return dose['timing'].get('repeat', {}).get('frequency', '')
        return ""
    
    def _extract_prescriber(self, requester: Dict) -> str:
        """Extract prescriber information"""
        return requester.get('display', 'Unknown')
    
    def _extract_reference_range(self, obs: Dict) -> str:
        """Extract reference range"""
        if 'referenceRange' in obs and len(obs['referenceRange']) > 0:
            ref = obs['referenceRange'][0]
            low = ref.get('low', {}).get('value', '')
            high = ref.get('high', {}).get('value', '')
            return f"{low}-{high}"
        return ""
    
    def _is_abnormal(self, obs: Dict) -> bool:
        """Check if observation is abnormal"""
        if 'interpretation' in obs and len(obs['interpretation']) > 0:
            interpretation = obs['interpretation'][0].get('text', '').lower()
            return 'abnormal' in interpretation or 'high' in interpretation or 'low' in interpretation
        return False
    
    def _extract_performer(self, performers: List) -> str:
        """Extract performer information"""
        if performers and len(performers) > 0:
            return performers[0].get('display', 'Unknown')
        return "Unknown"
    
    def _extract_practitioner_name(self, practitioner: Dict) -> str:
        """Extract practitioner name"""
        return practitioner.get('display', 'Unknown')
    
    def _extract_author(self, authors: List) -> str:
        """Extract document author"""
        if authors and len(authors) > 0:
            return authors[0].get('display', 'Unknown')
        return "Unknown"
    
    def _extract_content(self, content: List) -> str:
        """Extract document content"""
        if content and len(content) > 0:
            return content[0].get('attachment', {}).get('title', '')
        return ""
    
    def _extract_participants(self, participants: List) -> str:
        """Extract appointment participants"""
        if participants and len(participants) > 0:
            return participants[0].get('display', 'Unknown')
        return "Unknown"
    
    def _extract_reactions(self, reactions: List) -> List[str]:
        """Extract allergy reactions"""
        reaction_list = []
        for reaction in reactions:
            if 'manifestation' in reaction:
                for manifestation in reaction['manifestation']:
                    reaction_list.append(self._extract_code_text(manifestation))
        return reaction_list 