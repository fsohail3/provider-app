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