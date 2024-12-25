# medical_rag.py
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
import json

class MedicalRAG:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.llm = ChatOpenAI(model_name="gpt-4")
        
        self.prompt_template = """
        You are a pediatric diagnostic assistant. Using the provided medical literature and context, provide an evidence-based analysis.
        
        Patient Information:
        Age: {age}
        Gender: {gender}
        Symptoms: {symptoms}
        Duration: {duration}
        Additional Info: {additional_info}
        
        Retrieved Medical Literature:
        {context}
        
        Please provide:
        1. Possible diagnoses (ranked by likelihood), with specific citations from medical literature
        2. Recommended diagnostic tests, citing relevant guidelines
        3. Scientific references supporting each diagnosis
        4. Red flags to watch for, based on published criteria
        5. Differential diagnoses to consider, supported by literature
        
        Format each point with proper citations (e.g., [NEJM 2023;388:1234-45])
        
        Important: Always note that final diagnosis should be made by a qualified healthcare provider.
        """
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.knowledge_base.vector_store.as_retriever(
                search_kwargs={"k": 5}
            ),
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": PromptTemplate(
                    template=self.prompt_template,
                    input_variables=["age", "gender", "symptoms", "duration", "additional_info", "context"]
                )
            }
        )

    def get_diagnosis(self, patient_data):
        # Query relevant medical literature
        query = f"{patient_data['symptoms']} {patient_data['age']} years old {patient_data['gender']}"
        relevant_docs = self.knowledge_base.vector_store.similarity_search(query, k=5)
        
        # Format context with citations
        context = "\n\n".join([
            f"Source [{doc.metadata['source']}]: {doc.page_content}"
            for doc in relevant_docs
        ])
        
        # Get response with citations
        response = self.qa_chain({
            "age": patient_data['age'],
            "gender": patient_data['gender'],
            "symptoms": patient_data['symptoms'],
            "duration": patient_data['duration'],
            "additional_info": patient_data['additional_info'],
            "context": context
        })
        
        return self.format_response(response)

    def format_response(self, response):
        # Add citation formatting and validation
        return {
            "diagnosis": response['result'],
            "sources": [doc.metadata['source'] for doc in response['source_documents']],
            "confidence_score": self.calculate_confidence(response)
        }

    def calculate_confidence(self, response):
        # Implement confidence scoring based on source quality and relevance
        return confidence_score