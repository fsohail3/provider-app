from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import json

class MedicalKnowledgeBase:
    def __init__(self):
        self.sources = {
            "uptodate": "databases/uptodate/",
            "pubmed": "databases/pubmed/",
            "aap": "databases/american_academy_pediatrics/",
            "nejm": "databases/nejm/"
        }
        
        # Trusted medical sources and their citations
        self.citations = {
            "AAP": "American Academy of Pediatrics Clinical Guidelines",
            "NEJM": "New England Journal of Medicine",
            "JAMA": "Journal of the American Medical Association",
            "CDC": "Centers for Disease Control and Prevention",
            "WHO": "World Health Organization"
        }
        
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None

    def load_medical_data(self):
        documents = []
        for source, path in self.sources.items():
            loader = DirectoryLoader(
                path,
                glob="**/*.pdf",
                loader_cls=PyPDFLoader
            )
            documents.extend(loader.load())

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        texts = text_splitter.split_documents(documents)
        
        # Create vector store
        self.vector_store = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )