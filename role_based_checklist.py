#!/usr/bin/env python3
"""
Role-Based Checklist Generator for Healthcare AI Procedure Assistant
Customizes checklists and instructions based on practitioner roles and patient data
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoleBasedChecklistGenerator:
    """Generates role-specific checklists based on practitioner role and patient data"""
    
    def __init__(self):
        # Define all supported practitioner roles
        self.supported_roles = {
            'ER Nurse': {
                'display_name': 'Emergency Room Nurse',
                'icon': '🚨',
                'priority': 1,
                'specialties': ['emergency', 'triage', 'acute care']
            },
            'ICU Nurse': {
                'display_name': 'Intensive Care Unit Nurse',
                'icon': '🏥',
                'priority': 2,
                'specialties': ['critical care', 'ventilation', 'monitoring']
            },
            'Nurse Practitioner': {
                'display_name': 'Nurse Practitioner',
                'icon': '👩‍⚕️',
                'priority': 3,
                'specialties': ['primary care', 'diagnosis', 'treatment']
            },
            'Medical Assistant': {
                'display_name': 'Medical Assistant',
                'icon': '💉',
                'priority': 4,
                'specialties': ['vitals', 'preparation', 'support']
            },
            'Surgical Technologist': {
                'display_name': 'Surgical Technologist',
                'icon': '🔪',
                'priority': 5,
                'specialties': ['surgery', 'sterilization', 'equipment']
            },
            'Emergency Medical Technician': {
                'display_name': 'Emergency Medical Technician',
                'icon': '🚑',
                'priority': 6,
                'specialties': ['emergency', 'transport', 'basic life support']
            },
            'Paramedic': {
                'display_name': 'Paramedic',
                'icon': '🚑',
                'priority': 7,
                'specialties': ['emergency', 'advanced life support', 'transport']
            },
            'Phlebotomist': {
                'display_name': 'Phlebotomist',
                'icon': '🩸',
                'priority': 8,
                'specialties': ['blood collection', 'lab work', 'venipuncture']
            },
            'Occupational Therapist': {
                'display_name': 'Occupational Therapist',
                'icon': '🦾',
                'priority': 9,
                'specialties': ['rehabilitation', 'therapy', 'mobility']
            },
            'Lab Technologist': {
                'display_name': 'Laboratory Technologist',
                'icon': '🔬',
                'priority': 10,
                'specialties': ['laboratory', 'testing', 'analysis']
            },
            'Lab Technician': {
                'display_name': 'Laboratory Technician',
                'icon': '🔬',
                'priority': 11,
                'specialties': ['laboratory', 'testing', 'analysis']
            },
            'Patient Care Technician': {
                'display_name': 'Patient Care Technician',
                'icon': '👨‍⚕️',
                'priority': 12,
                'specialties': ['patient care', 'vitals', 'support']
            },
            'Charge Nurse': {
                'display_name': 'Charge Nurse',
                'icon': '👩‍⚕️',
                'priority': 13,
                'specialties': ['supervision', 'coordination', 'management']
            },
            'Nurse Aide': {
                'display_name': 'Nurse Aide',
                'icon': '👨‍⚕️',
                'priority': 14,
                'specialties': ['basic care', 'support', 'assistance']
            },
            'Nursing Assistant': {
                'display_name': 'Nursing Assistant',
                'icon': '👨‍⚕️',
                'priority': 15,
                'specialties': ['basic care', 'support', 'assistance']
            },
            'CNA': {
                'display_name': 'Certified Nursing Assistant',
                'icon': '👨‍⚕️',
                'priority': 16,
                'specialties': ['basic care', 'support', 'assistance']
            }
        }
        
        # Role-specific checklist templates
        self.role_templates = self._initialize_role_templates()
        
    def _initialize_role_templates(self) -> Dict:
        """Initialize role-specific checklist templates"""
        return {
            'ER Nurse': {
                'pre_procedure': [
                    'Rapid patient assessment and triage',
                    'Vital signs assessment (BP, HR, RR, Temp, O2 Sat)',
                    'Allergy check and medication reconciliation',
                    'Emergency equipment verification',
                    'Patient consent and family notification',
                    'Time-critical intervention prioritization'
                ],
                'during_procedure': [
                    'Continuous vital signs monitoring',
                    'Emergency response readiness',
                    'Patient safety and positioning',
                    'Equipment and medication availability',
                    'Communication with emergency team',
                    'Documentation of interventions'
                ],
                'post_procedure': [
                    'Post-procedure vital signs',
                    'Patient stability assessment',
                    'Discharge readiness evaluation',
                    'Follow-up care coordination',
                    'Patient education and instructions',
                    'Emergency department handoff'
                ],
                'risk_factors': [
                    'Unstable vital signs',
                    'Allergic reactions',
                    'Medication interactions',
                    'Patient agitation or confusion',
                    'Equipment malfunction',
                    'Time delays in care'
                ]
            },
            'ICU Nurse': {
                'pre_procedure': [
                    'Comprehensive patient assessment',
                    'Ventilator settings verification',
                    'Hemodynamic monitoring setup',
                    'Medication reconciliation and allergy check',
                    'Equipment calibration and testing',
                    'Family communication and consent'
                ],
                'during_procedure': [
                    'Continuous hemodynamic monitoring',
                    'Ventilator parameter monitoring',
                    'Medication administration and titration',
                    'Patient positioning and safety',
                    'Real-time documentation',
                    'Team communication and coordination'
                ],
                'post_procedure': [
                    'Post-procedure hemodynamic assessment',
                    'Ventilator weaning evaluation',
                    'Medication effectiveness monitoring',
                    'Complication surveillance',
                    'Family update and education',
                    'Care plan adjustment'
                ],
                'risk_factors': [
                    'Hemodynamic instability',
                    'Ventilator complications',
                    'Medication side effects',
                    'Infection risk',
                    'Pressure injuries',
                    'Delirium development'
                ]
            },
            'Nurse Practitioner': {
                'pre_procedure': [
                    'Comprehensive health assessment',
                    'Diagnostic test review and interpretation',
                    'Medication reconciliation and optimization',
                    'Patient education and informed consent',
                    'Risk factor identification and mitigation',
                    'Care coordination with specialists'
                ],
                'during_procedure': [
                    'Clinical decision making and intervention',
                    'Patient monitoring and assessment',
                    'Medication administration and management',
                    'Documentation and progress notes',
                    'Patient communication and reassurance',
                    'Quality and safety oversight'
                ],
                'post_procedure': [
                    'Post-procedure assessment and evaluation',
                    'Medication adjustment and management',
                    'Follow-up care planning',
                    'Patient education and discharge instructions',
                    'Care coordination and referrals',
                    'Outcome evaluation and documentation'
                ],
                'risk_factors': [
                    'Medication interactions and side effects',
                    'Diagnostic accuracy and interpretation',
                    'Patient compliance and understanding',
                    'Care coordination gaps',
                    'Follow-up adherence',
                    'Documentation completeness'
                ]
            },
            'Medical Assistant': {
                'pre_procedure': [
                    'Patient vital signs measurement',
                    'Medical history review and documentation',
                    'Medication list verification',
                    'Allergy assessment and documentation',
                    'Equipment preparation and sterilization',
                    'Patient preparation and positioning'
                ],
                'during_procedure': [
                    'Assistance with procedure setup',
                    'Patient monitoring and comfort',
                    'Equipment and supply management',
                    'Documentation support',
                    'Infection control maintenance',
                    'Emergency response assistance'
                ],
                'post_procedure': [
                    'Post-procedure vital signs',
                    'Patient comfort and safety check',
                    'Equipment cleanup and sterilization',
                    'Documentation completion',
                    'Patient education support',
                    'Follow-up scheduling assistance'
                ],
                'risk_factors': [
                    'Incomplete vital signs',
                    'Medication documentation errors',
                    'Allergy documentation gaps',
                    'Equipment sterilization issues',
                    'Infection control breaches',
                    'Documentation inaccuracies'
                ]
            },
            'Surgical Technologist': {
                'pre_procedure': [
                    'Surgical equipment verification and setup',
                    'Sterilization confirmation and documentation',
                    'Surgical instrument count and preparation',
                    'Operating room setup and safety check',
                    'Patient positioning equipment preparation',
                    'Emergency equipment availability verification'
                ],
                'during_procedure': [
                    'Surgical instrument and equipment management',
                    'Sterile field maintenance and monitoring',
                    'Surgical count verification and documentation',
                    'Equipment troubleshooting and support',
                    'Infection control compliance monitoring',
                    'Emergency response equipment readiness'
                ],
                'post_procedure': [
                    'Surgical instrument count verification',
                    'Equipment cleanup and sterilization',
                    'Specimen handling and documentation',
                    'Operating room cleanup and preparation',
                    'Equipment maintenance and restocking',
                    'Documentation completion and verification'
                ],
                'risk_factors': [
                    'Surgical instrument count discrepancies',
                    'Sterilization failures',
                    'Equipment malfunction',
                    'Infection control breaches',
                    'Specimen handling errors',
                    'Documentation inaccuracies'
                ]
            },
            'Emergency Medical Technician': {
                'pre_procedure': [
                    'Scene safety assessment and management',
                    'Patient rapid assessment and triage',
                    'Vital signs measurement and documentation',
                    'Allergy and medication history check',
                    'Equipment readiness and verification',
                    'Transport preparation and planning'
                ],
                'during_procedure': [
                    'Patient monitoring and assessment',
                    'Basic life support interventions',
                    'Equipment operation and management',
                    'Communication with medical control',
                    'Patient comfort and safety maintenance',
                    'Documentation and reporting'
                ],
                'post_procedure': [
                    'Patient handoff to receiving facility',
                    'Equipment cleanup and restocking',
                    'Documentation completion',
                    'Vehicle and equipment maintenance',
                    'Quality improvement review',
                    'Continuing education needs assessment'
                ],
                'risk_factors': [
                    'Scene safety hazards',
                    'Patient deterioration during transport',
                    'Equipment malfunction',
                    'Communication failures',
                    'Documentation errors',
                    'Vehicle and traffic safety'
                ]
            },
            'Paramedic': {
                'pre_procedure': [
                    'Advanced patient assessment and triage',
                    'Vital signs and cardiac monitoring',
                    'Medication reconciliation and allergy check',
                    'Advanced life support equipment setup',
                    'Medical control communication',
                    'Transport planning and coordination'
                ],
                'during_procedure': [
                    'Advanced life support interventions',
                    'Cardiac monitoring and interpretation',
                    'Medication administration and titration',
                    'Patient stabilization and management',
                    'Medical control consultation',
                    'Real-time documentation and reporting'
                ],
                'post_procedure': [
                    'Patient handoff and report to receiving facility',
                    'Equipment cleanup and restocking',
                    'Documentation completion and quality review',
                    'Vehicle and equipment maintenance',
                    'Quality improvement and case review',
                    'Continuing education and skill maintenance'
                ],
                'risk_factors': [
                    'Patient deterioration requiring advanced interventions',
                    'Medication administration errors',
                    'Equipment malfunction during critical care',
                    'Communication failures with medical control',
                    'Documentation errors in critical situations',
                    'Vehicle and traffic safety during emergency response'
                ]
            },
            'Phlebotomist': {
                'pre_procedure': [
                    'Patient identification verification',
                    'Test requisition review and confirmation',
                    'Equipment preparation and sterilization',
                    'Patient preparation and positioning',
                    'Infection control measures implementation',
                    'Quality control verification'
                ],
                'during_procedure': [
                    'Venipuncture technique and execution',
                    'Specimen collection and labeling',
                    'Patient comfort and safety maintenance',
                    'Infection control compliance',
                    'Quality control monitoring',
                    'Documentation and record keeping'
                ],
                'post_procedure': [
                    'Specimen processing and preparation',
                    'Equipment cleanup and sterilization',
                    'Patient care and monitoring',
                    'Documentation completion',
                    'Quality control verification',
                    'Follow-up scheduling if needed'
                ],
                'risk_factors': [
                    'Patient identification errors',
                    'Specimen labeling mistakes',
                    'Infection control breaches',
                    'Equipment contamination',
                    'Documentation errors',
                    'Quality control failures'
                ]
            },
            'Occupational Therapist': {
                'pre_procedure': [
                    'Patient functional assessment',
                    'Treatment plan review and modification',
                    'Equipment and adaptive device evaluation',
                    'Patient goals and expectations clarification',
                    'Safety assessment and risk evaluation',
                    'Care coordination with interdisciplinary team'
                ],
                'during_procedure': [
                    'Therapeutic intervention implementation',
                    'Patient progress monitoring and assessment',
                    'Equipment and adaptive device training',
                    'Safety monitoring and risk management',
                    'Patient education and instruction',
                    'Documentation and progress notes'
                ],
                'post_procedure': [
                    'Treatment outcome evaluation',
                    'Patient progress assessment',
                    'Equipment and adaptive device adjustment',
                    'Home program development and instruction',
                    'Follow-up care planning',
                    'Care coordination and communication'
                ],
                'risk_factors': [
                    'Patient safety during therapy',
                    'Equipment malfunction or misuse',
                    'Treatment plan adherence issues',
                    'Progress documentation gaps',
                    'Care coordination failures',
                    'Patient education comprehension'
                ]
            },
            'Lab Technologist': {
                'pre_procedure': [
                    'Test requisition verification and validation',
                    'Specimen quality assessment and acceptance',
                    'Equipment calibration and quality control',
                    'Test methodology verification',
                    'Safety protocols implementation',
                    'Documentation and record keeping'
                ],
                'during_procedure': [
                    'Test execution and monitoring',
                    'Quality control testing and verification',
                    'Equipment operation and maintenance',
                    'Safety protocol compliance',
                    'Real-time documentation and reporting',
                    'Problem identification and resolution'
                ],
                'post_procedure': [
                    'Test result validation and verification',
                    'Quality control review and documentation',
                    'Equipment maintenance and calibration',
                    'Result reporting and communication',
                    'Documentation completion and archiving',
                    'Quality improvement and continuing education'
                ],
                'risk_factors': [
                    'Specimen quality issues',
                    'Equipment malfunction or calibration errors',
                    'Quality control failures',
                    'Test methodology errors',
                    'Documentation and reporting errors',
                    'Safety protocol breaches'
                ]
            },
            'Lab Technician': {
                'pre_procedure': [
                    'Test requisition review and preparation',
                    'Specimen processing and preparation',
                    'Equipment setup and calibration',
                    'Quality control preparation',
                    'Safety protocol implementation',
                    'Documentation and record keeping'
                ],
                'during_procedure': [
                    'Test execution and monitoring',
                    'Quality control testing',
                    'Equipment operation and maintenance',
                    'Safety protocol compliance',
                    'Documentation and reporting',
                    'Problem identification and escalation'
                ],
                'post_procedure': [
                    'Test result review and validation',
                    'Quality control documentation',
                    'Equipment cleanup and maintenance',
                    'Result reporting and communication',
                    'Documentation completion',
                    'Quality improvement participation'
                ],
                'risk_factors': [
                    'Specimen processing errors',
                    'Equipment operation mistakes',
                    'Quality control failures',
                    'Documentation errors',
                    'Safety protocol breaches',
                    'Result reporting delays'
                ]
            },
            'Patient Care Technician': {
                'pre_procedure': [
                    'Patient vital signs measurement',
                    'Medical history review and documentation',
                    'Patient preparation and positioning',
                    'Equipment setup and verification',
                    'Infection control measures',
                    'Patient comfort and safety assessment'
                ],
                'during_procedure': [
                    'Patient monitoring and support',
                    'Equipment operation and management',
                    'Patient comfort and safety maintenance',
                    'Infection control compliance',
                    'Documentation and reporting',
                    'Emergency response assistance'
                ],
                'post_procedure': [
                    'Post-procedure patient care',
                    'Equipment cleanup and maintenance',
                    'Patient comfort and safety check',
                    'Documentation completion',
                    'Follow-up care coordination',
                    'Quality improvement participation'
                ],
                'risk_factors': [
                    'Incomplete patient assessment',
                    'Equipment operation errors',
                    'Infection control breaches',
                    'Documentation inaccuracies',
                    'Patient safety issues',
                    'Communication failures'
                ]
            },
            'Charge Nurse': {
                'pre_procedure': [
                    'Staff assignment and coordination',
                    'Resource allocation and management',
                    'Patient care planning and coordination',
                    'Quality and safety oversight',
                    'Communication and handoff management',
                    'Emergency response preparation'
                ],
                'during_procedure': [
                    'Staff supervision and support',
                    'Resource management and coordination',
                    'Quality and safety monitoring',
                    'Communication and escalation management',
                    'Patient care coordination',
                    'Documentation and reporting oversight'
                ],
                'post_procedure': [
                    'Staff debriefing and support',
                    'Resource evaluation and planning',
                    'Quality and safety review',
                    'Communication and handoff completion',
                    'Documentation and reporting review',
                    'Quality improvement and continuing education'
                ],
                'risk_factors': [
                    'Staffing shortages or skill gaps',
                    'Resource allocation issues',
                    'Communication failures',
                    'Quality and safety breaches',
                    'Documentation and reporting errors',
                    'Emergency response coordination failures'
                ]
            },
            'Nurse Aide': {
                'pre_procedure': [
                    'Patient basic care and comfort',
                    'Vital signs measurement and documentation',
                    'Patient preparation and positioning',
                    'Equipment setup and verification',
                    'Infection control measures',
                    'Patient safety assessment'
                ],
                'during_procedure': [
                    'Patient monitoring and support',
                    'Basic care and comfort maintenance',
                    'Equipment operation and management',
                    'Infection control compliance',
                    'Documentation and reporting',
                    'Emergency response assistance'
                ],
                'post_procedure': [
                    'Post-procedure patient care',
                    'Equipment cleanup and maintenance',
                    'Patient comfort and safety check',
                    'Documentation completion',
                    'Follow-up care coordination',
                    'Quality improvement participation'
                ],
                'risk_factors': [
                    'Incomplete patient assessment',
                    'Equipment operation errors',
                    'Infection control breaches',
                    'Documentation inaccuracies',
                    'Patient safety issues',
                    'Communication failures'
                ]
            },
            'Nursing Assistant': {
                'pre_procedure': [
                    'Patient basic care and comfort',
                    'Vital signs measurement and documentation',
                    'Patient preparation and positioning',
                    'Equipment setup and verification',
                    'Infection control measures',
                    'Patient safety assessment'
                ],
                'during_procedure': [
                    'Patient monitoring and support',
                    'Basic care and comfort maintenance',
                    'Equipment operation and management',
                    'Infection control compliance',
                    'Documentation and reporting',
                    'Emergency response assistance'
                ],
                'post_procedure': [
                    'Post-procedure patient care',
                    'Equipment cleanup and maintenance',
                    'Patient comfort and safety check',
                    'Documentation completion',
                    'Follow-up care coordination',
                    'Quality improvement participation'
                ],
                'risk_factors': [
                    'Incomplete patient assessment',
                    'Equipment operation errors',
                    'Infection control breaches',
                    'Documentation inaccuracies',
                    'Patient safety issues',
                    'Communication failures'
                ]
            },
            'CNA': {
                'pre_procedure': [
                    'Patient basic care and comfort',
                    'Vital signs measurement and documentation',
                    'Patient preparation and positioning',
                    'Equipment setup and verification',
                    'Infection control measures',
                    'Patient safety assessment'
                ],
                'during_procedure': [
                    'Patient monitoring and support',
                    'Basic care and comfort maintenance',
                    'Equipment operation and management',
                    'Infection control compliance',
                    'Documentation and reporting',
                    'Emergency response assistance'
                ],
                'post_procedure': [
                    'Post-procedure patient care',
                    'Equipment cleanup and maintenance',
                    'Patient comfort and safety check',
                    'Documentation completion',
                    'Follow-up care coordination',
                    'Quality improvement participation'
                ],
                'risk_factors': [
                    'Incomplete patient assessment',
                    'Equipment operation errors',
                    'Infection control breaches',
                    'Documentation inaccuracies',
                    'Patient safety issues',
                    'Communication failures'
                ]
            }
        }
    
    def detect_practitioner_role(self, practitioner_data: Dict) -> str:
        """Detect practitioner role from Epic data"""
        if not practitioner_data:
            return 'Unknown'
        
        role_text = practitioner_data.get('role', '').lower()
        specialty_text = ' '.join(practitioner_data.get('specialty', [])).lower()
        
        # Role detection logic
        if 'emergency' in role_text or 'er' in role_text:
            return 'ER Nurse'
        elif 'icu' in role_text or 'intensive care' in role_text or 'critical care' in role_text:
            return 'ICU Nurse'
        elif 'nurse practitioner' in role_text or 'np' in role_text:
            return 'Nurse Practitioner'
        elif 'medical assistant' in role_text or 'ma' in role_text:
            return 'Medical Assistant'
        elif 'surgical technologist' in role_text or 'surg tech' in role_text:
            return 'Surgical Technologist'
        elif 'emergency medical technician' in role_text or 'emt' in role_text:
            return 'Emergency Medical Technician'
        elif 'paramedic' in role_text:
            return 'Paramedic'
        elif 'phlebotomist' in role_text:
            return 'Phlebotomist'
        elif 'occupational therapist' in role_text or 'ot' in role_text:
            return 'Occupational Therapist'
        elif 'lab technologist' in role_text:
            return 'Lab Technologist'
        elif 'lab technician' in role_text:
            return 'Lab Technician'
        elif 'patient care technician' in role_text or 'pct' in role_text:
            return 'Patient Care Technician'
        elif 'charge nurse' in role_text:
            return 'Charge Nurse'
        elif 'nurse aide' in role_text or 'nursing assistant' in role_text or 'cna' in role_text:
            return 'CNA'
        else:
            # Fallback based on specialty
            if 'emergency' in specialty_text:
                return 'ER Nurse'
            elif 'critical care' in specialty_text or 'icu' in specialty_text:
                return 'ICU Nurse'
            elif 'surgery' in specialty_text:
                return 'Surgical Technologist'
            elif 'laboratory' in specialty_text or 'lab' in specialty_text:
                return 'Lab Technologist'
            else:
                return 'Nurse Practitioner'  # Default fallback
    
    def generate_role_based_checklist(self, practitioner_role: str, patient_data: Dict, procedure_type: str = 'general') -> Dict:
        """Generate role-specific checklist based on practitioner role and patient data"""
        logger.info(f"🎯 Generating checklist for role: {practitioner_role}")
        
        # Get role template
        role_info = self.supported_roles.get(practitioner_role, {})
        template = self.role_templates.get(practitioner_role, self.role_templates['Nurse Practitioner'])
        
        # Generate base checklist
        checklist = {
            'role': practitioner_role,
            'role_display_name': role_info.get('display_name', practitioner_role),
            'role_icon': role_info.get('icon', '👨‍⚕️'),
            'procedure_type': procedure_type,
            'generated_at': datetime.now().isoformat(),
            'patient_context': self._extract_patient_context(patient_data),
            'pre_procedure': self._customize_checklist_items(template['pre_procedure'], patient_data, practitioner_role),
            'during_procedure': self._customize_checklist_items(template['during_procedure'], patient_data, practitioner_role),
            'post_procedure': self._customize_checklist_items(template['post_procedure'], patient_data, practitioner_role),
            'risk_factors': self._identify_risk_factors(template['risk_factors'], patient_data, practitioner_role),
            'patient_alerts': self._generate_patient_alerts(patient_data),
            'role_specific_notes': self._generate_role_specific_notes(practitioner_role, patient_data)
        }
        
        return checklist
    
    def _extract_patient_context(self, patient_data: Dict) -> Dict:
        """Extract relevant patient context for checklist customization"""
        context = {
            'demographics': {},
            'vital_signs': [],
            'allergies': [],
            'medications': [],
            'conditions': [],
            'labs': [],
            'surgeries': []
        }
        
        # Demographics
        if patient_data.get('demographics'):
            context['demographics'] = {
                'name': patient_data['demographics'].get('name', 'Unknown'),
                'age': patient_data['demographics'].get('age', 0),
                'gender': patient_data['demographics'].get('gender', 'Unknown')
            }
        
        # Vital signs (most recent)
        if patient_data.get('vital_signs'):
            context['vital_signs'] = patient_data['vital_signs'][:5]  # Most recent 5
        
        # Allergies (active)
        if patient_data.get('allergies'):
            context['allergies'] = [
                allergy for allergy in patient_data['allergies']
                if allergy.get('status', '').lower() != 'inactive'
            ]
        
        # Medications (active)
        if patient_data.get('medications'):
            context['medications'] = [
                med for med in patient_data['medications']
                if med.get('status', '').lower() in ['active', 'active']
            ]
        
        # Conditions (active)
        if patient_data.get('medical_history'):
            context['conditions'] = [
                condition for condition in patient_data['medical_history']
                if condition.get('status', '').lower() in ['active', 'recurrence', 'relapse']
            ]
        
        # Labs (abnormal)
        if patient_data.get('labs'):
            context['labs'] = [
                lab for lab in patient_data['labs']
                if lab.get('abnormal', False)
            ]
        
        # Surgeries (recent)
        if patient_data.get('surgeries'):
            context['surgeries'] = patient_data['surgeries'][:3]  # Most recent 3
        
        return context
    
    def _customize_checklist_items(self, base_items: List[str], patient_data: Dict, role: str) -> List[Dict]:
        """Customize checklist items based on patient data and role"""
        customized_items = []
        
        for item in base_items:
            customized_item = {
                'task': item,
                'priority': 'normal',
                'risk_level': 'low',
                'patient_specific_notes': '',
                'role_specific_notes': ''
            }
            
            # Add patient-specific customization
            if 'allergy' in item.lower() and patient_data.get('allergies'):
                customized_item['priority'] = 'high'
                customized_item['risk_level'] = 'high'
                customized_item['patient_specific_notes'] = f"Patient has {len(patient_data['allergies'])} active allergies"
            
            elif 'vital' in item.lower() and patient_data.get('vital_signs'):
                customized_item['priority'] = 'high'
                customized_item['patient_specific_notes'] = f"Recent vitals available: {len(patient_data['vital_signs'])} readings"
            
            elif 'medication' in item.lower() and patient_data.get('medications'):
                customized_item['priority'] = 'high'
                customized_item['patient_specific_notes'] = f"Patient on {len(patient_data['medications'])} active medications"
            
            elif 'surgery' in item.lower() and patient_data.get('surgeries'):
                customized_item['priority'] = 'medium'
                customized_item['patient_specific_notes'] = f"Patient has {len(patient_data['surgeries'])} documented surgeries"
            
            # Add role-specific customization
            if role == 'ER Nurse':
                if 'emergency' in item.lower() or 'rapid' in item.lower():
                    customized_item['priority'] = 'high'
                    customized_item['role_specific_notes'] = "Time-critical in emergency setting"
            
            elif role == 'ICU Nurse':
                if 'monitoring' in item.lower() or 'hemodynamic' in item.lower():
                    customized_item['priority'] = 'high'
                    customized_item['role_specific_notes'] = "Critical for ICU patient stability"
            
            elif role == 'Surgical Technologist':
                if 'sterilization' in item.lower() or 'equipment' in item.lower():
                    customized_item['priority'] = 'high'
                    customized_item['role_specific_notes'] = "Critical for surgical safety"
            
            customized_items.append(customized_item)
        
        return customized_items
    
    def _identify_risk_factors(self, base_risks: List[str], patient_data: Dict, role: str) -> List[Dict]:
        """Identify specific risk factors based on patient data and role"""
        risk_factors = []
        
        for risk in base_risks:
            risk_factor = {
                'risk': risk,
                'severity': 'medium',
                'patient_specific': False,
                'notes': ''
            }
            
            # Patient-specific risk assessment
            if 'allergy' in risk.lower() and patient_data.get('allergies'):
                risk_factor['severity'] = 'high'
                risk_factor['patient_specific'] = True
                risk_factor['notes'] = f"Patient has {len(patient_data['allergies'])} active allergies"
            
            elif 'vital' in risk.lower() and patient_data.get('vital_signs'):
                abnormal_vitals = [v for v in patient_data['vital_signs'] if v.get('value')]
                if abnormal_vitals:
                    risk_factor['severity'] = 'high'
                    risk_factor['patient_specific'] = True
                    risk_factor['notes'] = f"Patient has {len(abnormal_vitals)} abnormal vital signs"
            
            elif 'medication' in risk.lower() and patient_data.get('medications'):
                risk_factor['severity'] = 'medium'
                risk_factor['patient_specific'] = True
                risk_factor['notes'] = f"Patient on {len(patient_data['medications'])} medications - check interactions"
            
            risk_factors.append(risk_factor)
        
        return risk_factors
    
    def _generate_patient_alerts(self, patient_data: Dict) -> List[Dict]:
        """Generate patient-specific alerts"""
        alerts = []
        
        # Allergy alerts
        if patient_data.get('allergies'):
            for allergy in patient_data['allergies']:
                if allergy.get('severity') == 'high':
                    alerts.append({
                        'type': 'allergy',
                        'severity': 'high',
                        'message': f"SEVERE ALLERGY: {allergy.get('substance', 'Unknown substance')}",
                        'details': allergy.get('reaction', [])
                    })
        
        # Abnormal lab alerts
        if patient_data.get('labs'):
            abnormal_labs = [lab for lab in patient_data['labs'] if lab.get('abnormal', False)]
            if abnormal_labs:
                alerts.append({
                    'type': 'lab',
                    'severity': 'medium',
                    'message': f"ABNORMAL LABS: {len(abnormal_labs)} abnormal results",
                    'details': [f"{lab.get('name', 'Unknown')}: {lab.get('value', 'N/A')}" for lab in abnormal_labs[:3]]
                })
        
        # Recent surgery alerts
        if patient_data.get('surgeries'):
            recent_surgeries = patient_data['surgeries'][:2]  # Most recent 2
            if recent_surgeries:
                alerts.append({
                    'type': 'surgery',
                    'severity': 'medium',
                    'message': f"RECENT SURGERIES: {len(recent_surgeries)} recent procedures",
                    'details': [f"{surgery.get('name', 'Unknown')} - {surgery.get('date', 'Unknown date')}" for surgery in recent_surgeries]
                })
        
        return alerts
    
    def _generate_role_specific_notes(self, role: str, patient_data: Dict) -> List[str]:
        """Generate role-specific notes and recommendations"""
        notes = []
        
        if role == 'ER Nurse':
            if patient_data.get('vital_signs'):
                notes.append("Focus on rapid assessment and stabilization")
                notes.append("Prioritize time-critical interventions")
            
        elif role == 'ICU Nurse':
            if patient_data.get('vital_signs'):
                notes.append("Maintain continuous monitoring and documentation")
                notes.append("Be prepared for rapid intervention if needed")
            
        elif role == 'Surgical Technologist':
            if patient_data.get('surgeries'):
                notes.append("Review surgical history for equipment needs")
                notes.append("Ensure proper sterilization protocols")
            
        elif role == 'Phlebotomist':
            if patient_data.get('allergies'):
                notes.append("Verify no latex allergies before procedure")
                notes.append("Check for specific medication allergies")
            
        return notes
    
    def get_supported_roles(self) -> List[Dict]:
        """Get list of all supported roles"""
        return [
            {
                'role': role,
                'display_name': info['display_name'],
                'icon': info['icon'],
                'priority': info['priority'],
                'specialties': info['specialties']
            }
            for role, info in self.supported_roles.items()
        ] 