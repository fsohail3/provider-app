from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import requests
import json
import os
from datetime import datetime
from rate_limiter import RateLimiter

class MedicalKnowledgeBase:
    def __init__(self):
        self.api_keys = {
            "pubmed": os.getenv("PUBMED_API_KEY"),
            "uptodate": os.getenv("UPTODATE_API_KEY"),
            "medscape": os.getenv("MEDSCAPE_API_KEY"),
            "clinicaltrials": os.getenv("CLINICALTRIALS_API_KEY")
        }
        
        self.api_endpoints = {
            "pubmed": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
            "uptodate": "https://api.uptodate.com/rest/",
            "medscape": "https://api.medscape.com/api/",
            "clinicaltrials": "https://clinicaltrials.gov/api/"
        }
        
        self.embeddings = OpenAIEmbeddings()
        self.cache_duration = 3600  # Cache duration in seconds (1 hour)
        self.cache_dir = "./cache"
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        self.rate_limiter = RateLimiter()

        # Add procedure-specific endpoints
        self.procedure_endpoints = {
            "protocols": f"{self.api_endpoints['uptodate']}protocols",
            "guidelines": f"{self.api_endpoints['uptodate']}guidelines",
            "procedures": f"{self.api_endpoints['uptodate']}procedures"
        }

    async def search_pubmed(self, query, max_results=10):
        """Search PubMed for medical literature"""
        try:
            # Check cache first
            cache_key = f"pubmed_{hash(query)}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

            # Wait if we need to respect rate limits
            await self.rate_limiter.wait_if_needed("pubmed")

            # Make API request
            base_url = f"{self.api_endpoints['pubmed']}esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "format": "json",
                "api_key": self.api_keys["pubmed"]
            }
            
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            # Get article details
            article_ids = response.json()["esearchresult"]["idlist"]
            
            # Wait again for the second API call
            await self.rate_limiter.wait_if_needed("pubmed")
            articles = await self._fetch_pubmed_articles(article_ids)
            
            # Cache the results
            self._save_to_cache(cache_key, articles)
            
            return articles
            
        except Exception as e:
            print(f"PubMed search error: {str(e)}")
            return []

    async def search_uptodate(self, query):
        """Search UpToDate for clinical guidelines and recommendations"""
        try:
            cache_key = f"uptodate_{hash(query)}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

            # Wait if needed
            await self.rate_limiter.wait_if_needed("uptodate")

            headers = {
                "Authorization": f"Bearer {self.api_keys['uptodate']}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_endpoints['uptodate']}search",
                headers=headers,
                params={"query": query}
            )
            response.raise_for_status()
            
            results = response.json()
            self._save_to_cache(cache_key, results)
            return results
            
        except Exception as e:
            print(f"UpToDate search error: {str(e)}")
            return []

    async def get_clinical_trials(self, condition):
        """Search ClinicalTrials.gov for relevant trials"""
        try:
            cache_key = f"trials_{hash(condition)}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

            # Wait if needed
            await self.rate_limiter.wait_if_needed("clinicaltrials")

            response = requests.get(
                f"{self.api_endpoints['clinicaltrials']}query/study_fields",
                params={
                    "expr": condition,
                    "fields": "NCTId,BriefTitle,Condition,Phase,Status",
                    "fmt": "json"
                }
            )
            response.raise_for_status()
            
            trials = response.json()
            self._save_to_cache(cache_key, trials)
            return trials
            
        except Exception as e:
            print(f"ClinicalTrials.gov search error: {str(e)}")
            return []

    def _get_from_cache(self, key):
        """Retrieve data from cache if it exists and is not expired"""
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                if datetime.now().timestamp() - cached_data['timestamp'] < self.cache_duration:
                    return cached_data['data']
        return None

    def _save_to_cache(self, key, data):
        """Save data to cache with timestamp"""
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        cache_data = {
            'timestamp': datetime.now().timestamp(),
            'data': data
        }
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)

    async def _fetch_pubmed_articles(self, article_ids):
        """Fetch detailed information for PubMed articles"""
        try:
            base_url = f"{self.api_endpoints['pubmed']}esummary.fcgi"
            params = {
                "db": "pubmed",
                "id": ",".join(article_ids),
                "format": "json",
                "api_key": self.api_keys["pubmed"]
            }
            
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            return response.json()["result"]
            
        except Exception as e:
            print(f"Error fetching PubMed articles: {str(e)}")
            return []

    def update_rate_limits(self, new_limits):
        """Update rate limits for APIs"""
        for api_name, limits in new_limits.items():
            if api_name in self.api_endpoints:
                self.rate_limiter.update_rate_limit(
                    api_name,
                    calls=limits.get("calls"),
                    period=limits.get("period")
                )

    async def get_procedure_guidance(self, procedure_type, patient_data):
        """Get comprehensive guidance for a medical procedure"""
        try:
            # Check cache first
            cache_key = f"procedure_{procedure_type}_{hash(str(patient_data))}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

            # Wait for rate limiting
            await self.rate_limiter.wait_if_needed("uptodate")

            # Get procedure protocols
            headers = {
                "Authorization": f"Bearer {self.api_keys['uptodate']}",
                "Content-Type": "application/json"
            }
            
            response = await self._make_api_request(
                f"{self.procedure_endpoints['protocols']}/search",
                params={"query": procedure_type},
                headers=headers
            )

            # Get relevant medical literature
            pubmed_results = await self.search_pubmed(
                f"{procedure_type} procedure guidelines safety"
            )

            # Combine and process results
            guidance = {
                'procedure_info': response.json(),
                'literature': pubmed_results,
                'checklist': self._generate_procedure_checklist(procedure_type),
                'risks': await self._analyze_procedure_risks(procedure_type, patient_data),
                'monitoring': self._get_monitoring_requirements(procedure_type)
            }

            # Cache the results
            self._save_to_cache(cache_key, guidance)
            return guidance

        except Exception as e:
            print(f"Error getting procedure guidance: {str(e)}")
            return None

    async def _analyze_procedure_risks(self, procedure_type, patient_data):
        """Analyze risks based on procedure and patient factors"""
        try:
            risks = {
                'procedure_specific': [],
                'patient_specific': [],
                'interactions': [],
                'contraindications': [],
                'mitigation_strategies': []
            }

            # Get procedure-specific risks
            await self.rate_limiter.wait_if_needed("uptodate")
            proc_risks = await self._make_api_request(
                f"{self.procedure_endpoints['procedures']}/risks",
                params={"procedure": procedure_type}
            )
            risks['procedure_specific'] = proc_risks.json()

            # Analyze patient-specific factors
            patient_risks = self._analyze_patient_factors(patient_data)
            risks['patient_specific'] = patient_risks

            # Check for contraindications
            contraindications = self._check_contraindications(
                procedure_type, 
                patient_data
            )
            risks['contraindications'] = contraindications

            # Generate mitigation strategies
            risks['mitigation_strategies'] = self._generate_mitigation_strategies(
                risks['procedure_specific'] + risks['patient_specific'],
                contraindications
            )

            return risks

        except Exception as e:
            print(f"Error analyzing procedure risks: {str(e)}")
            return None

    def _analyze_patient_factors(self, patient_data):
        """Analyze patient-specific risk factors"""
        risks = []

        # Age-related risks
        if 'age' in patient_data:
            age_risks = self._check_age_related_risks(patient_data['age'])
            risks.extend(age_risks)

        # Weight-related risks
        if 'weight' in patient_data:
            weight_risks = self._check_weight_related_risks(patient_data['weight'])
            risks.extend(weight_risks)

        # Medication interactions
        if 'currentMedications' in patient_data:
            med_risks = self._check_medication_risks(patient_data['currentMedications'])
            risks.extend(med_risks)

        # Medical history risks
        if 'medicalHistory' in patient_data:
            history_risks = self._check_history_risks(patient_data['medicalHistory'])
            risks.extend(history_risks)

        # Allergy risks
        if 'allergies' in patient_data:
            allergy_risks = self._check_allergy_risks(patient_data['allergies'])
            risks.extend(allergy_risks)

        return risks

    def _generate_procedure_checklist(self, procedure_type):
        """Generate a comprehensive procedure checklist"""
        return {
            'preparation': self._get_preparation_steps(procedure_type),
            'equipment': self._get_required_equipment(procedure_type),
            'steps': self._get_procedure_steps(procedure_type),
            'monitoring': self._get_monitoring_points(procedure_type),
            'documentation': self._get_documentation_requirements(procedure_type)
        }

    def _get_monitoring_requirements(self, procedure_type):
        """Get monitoring requirements for a procedure"""
        return {
            'vital_signs': self._get_vital_sign_requirements(procedure_type),
            'intervals': self._get_monitoring_intervals(procedure_type),
            'parameters': self._get_monitoring_parameters(procedure_type),
            'thresholds': self._get_alert_thresholds(procedure_type)
        }

    # Helper methods for specific checks
    def _check_age_related_risks(self, age):
        # Implementation for age-related risk analysis
        pass

    def _check_weight_related_risks(self, weight):
        # Implementation for weight-related risk analysis
        pass

    def _check_medication_risks(self, medications):
        # Implementation for medication interaction analysis
        pass

    def _check_history_risks(self, history):
        # Implementation for medical history risk analysis
        pass

    def _check_allergy_risks(self, allergies):
        # Implementation for allergy risk analysis
        pass

    async def _make_api_request(self, endpoint, method="GET", **kwargs):
        """Make an API request with rate limiting and error handling"""
        try:
            response = requests.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"API request error: {str(e)}")
            raise

    def _check_contraindications(self, procedure_type, patient_data):
        """Check for procedure contraindications"""
        contraindications = []
        
        # Age contraindications
        age_contras = self._check_age_contraindications(procedure_type, patient_data.get('age'))
        if age_contras:
            contraindications.extend(age_contras)
        
        # Weight contraindications
        weight_contras = self._check_weight_contraindications(procedure_type, patient_data.get('weight'))
        if weight_contras:
            contraindications.extend(weight_contras)
        
        # Medication contraindications
        med_contras = self._check_medication_contraindications(
            procedure_type, 
            patient_data.get('currentMedications', [])
        )
        if med_contras:
            contraindications.extend(med_contras)
        
        # Medical history contraindications
        history_contras = self._check_history_contraindications(
            procedure_type,
            patient_data.get('medicalHistory', '')
        )
        if history_contras:
            contraindications.extend(history_contras)
        
        return contraindications

    def _generate_mitigation_strategies(self, risks, contraindications):
        """Generate strategies to mitigate identified risks"""
        strategies = []
        
        for risk in risks:
            strategies.extend(self._get_mitigation_for_risk(risk))
        
        for contra in contraindications:
            strategies.extend(self._get_mitigation_for_contraindication(contra))
        
        return strategies

    def _get_preparation_steps(self, procedure_type):
        """Get preparation steps for a procedure"""
        # This would typically come from a medical database
        # For now, returning placeholder data
        return [
            "Verify patient identity and procedure",
            "Check for allergies and contraindications",
            "Obtain informed consent",
            "Prepare sterile field if required",
            "Gather necessary equipment"
        ]

    def _get_required_equipment(self, procedure_type):
        """Get required equipment for a procedure"""
        # Placeholder implementation
        return [
            "Personal protective equipment",
            "Sterile supplies if needed",
            "Procedure-specific equipment",
            "Emergency equipment"
        ]

    def _get_procedure_steps(self, procedure_type):
        """Get step-by-step procedure instructions"""
        # Placeholder implementation
        return [
            "Verify patient and procedure",
            "Perform time-out",
            "Follow sterile technique if required",
            "Complete procedure steps",
            "Document procedure"
        ]

    def _get_monitoring_points(self, procedure_type):
        """Get monitoring points for the procedure"""
        return [
            "Vital signs",
            "Pain level",
            "Procedure site",
            "Patient response",
            "Complications"
        ]

    def _get_documentation_requirements(self, procedure_type):
        """Get documentation requirements"""
        return [
            "Procedure details",
            "Patient response",
            "Complications if any",
            "Follow-up instructions",
            "Patient education provided"
        ]

    def _get_vital_sign_requirements(self, procedure_type):
        """Get required vital sign monitoring"""
        return {
            "blood_pressure": "Every 15 minutes",
            "heart_rate": "Continuous",
            "respiratory_rate": "Every 15 minutes",
            "oxygen_saturation": "Continuous",
            "temperature": "Every hour"
        }

    def _get_monitoring_intervals(self, procedure_type):
        """Get monitoring intervals"""
        return {
            "vital_signs": "15 minutes",
            "site_check": "30 minutes",
            "pain_assessment": "1 hour",
            "neurological_checks": "2 hours"
        }

    def _get_monitoring_parameters(self, procedure_type):
        """Get parameters to monitor"""
        return {
            "vital_signs": ["BP", "HR", "RR", "SpO2", "Temp"],
            "pain": "0-10 scale",
            "consciousness": "AVPU scale",
            "site_assessment": ["color", "sensation", "movement"]
        }

    def _get_alert_thresholds(self, procedure_type):
        """Get alert thresholds for monitoring"""
        return {
            "systolic_bp": {"low": 90, "high": 160},
            "heart_rate": {"low": 50, "high": 120},
            "respiratory_rate": {"low": 12, "high": 24},
            "spo2": {"low": 92, "high": 100},
            "temperature": {"low": 36.0, "high": 38.5}
        }