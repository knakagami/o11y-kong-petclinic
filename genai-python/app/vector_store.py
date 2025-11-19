"""
Vector store controller for RAG (Retrieval-Augmented Generation) functionality.
Loads veterinarian data into a vector store for semantic search.
"""

import os
import logging
import json
from typing import List, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from langchain.schema import Document

from app.models import Vet
from app.data_provider import DataProvider

logger = logging.getLogger(__name__)


class VectorStoreController:
    """Manages the vector store for veterinarian data"""
    
    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider
        self.vector_store: Optional[Chroma] = None
        self.persist_directory = "./vectorstore"
        self.collection_name = "vets_collection"
        
        # Initialize embeddings based on environment
        self._init_embeddings()
        
    def _init_embeddings(self):
        """Initialize the appropriate embeddings model"""
        azure_key = os.getenv("AZURE_OPENAI_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if azure_key and azure_endpoint:
            logger.info("Using Azure OpenAI embeddings")
            self.embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=azure_endpoint,
                api_key=azure_key,
                azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
            )
        else:
            logger.info("Using OpenAI embeddings")
            openai_key = os.getenv("OPENAI_API_KEY", "demo")
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=openai_key,
                model="text-embedding-ada-002"
            )
    
    async def load_vector_store_on_startup(self):
        """
        Load veterinarian data into vector store on application startup.
        Checks if persisted data exists; if so, loads it to save on AI credits.
        Otherwise, fetches data from vets-service and creates embeddings.
        """
        persist_path = Path(self.persist_directory)
        
        # Check if vector store already exists
        if persist_path.exists() and any(persist_path.iterdir()):
            logger.info(f"Loading existing vector store from {self.persist_directory}")
            try:
                self.vector_store = Chroma(
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_directory
                )
                logger.info("Vector store loaded from existing data")
                return
            except Exception as e:
                logger.warning(f"Failed to load existing vector store: {e}. Creating new one.")
        
        # If vectorstore doesn't exist, create it from vets data
        logger.info("Creating new vector store from vets data")
        
        try:
            # Fetch all vets from vets-service
            vets = await self.data_provider.get_all_vets()
            
            if not vets:
                logger.warning("No vets data available")
                return
            
            # Convert vets to documents
            documents = self._convert_vets_to_documents(vets)
            
            # Create vector store
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=self.collection_name,
                persist_directory=self.persist_directory
            )
            
            logger.info(f"Vector store created with {len(documents)} documents and persisted to {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            # Create empty vector store as fallback
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
    
    def _convert_vets_to_documents(self, vets: List[Vet]) -> List[Document]:
        """
        Convert list of Vet objects to LangChain Documents for vector store.
        
        Args:
            vets: List of Vet objects
            
        Returns:
            List of Document objects
        """
        documents = []
        
        for vet in vets:
            # Create a text representation of the vet
            vet_dict = vet.model_dump()
            
            # Format specialties nicely
            specialties_str = ", ".join([s.get("name", "") for s in vet_dict.get("specialties", [])])
            
            # Create document content
            content = json.dumps({
                "id": vet_dict.get("id"),
                "firstName": vet_dict.get("firstName"),
                "lastName": vet_dict.get("lastName"),
                "specialties": specialties_str
            }, ensure_ascii=False)
            
            # Create metadata
            metadata = {
                "id": str(vet_dict.get("id")),
                "firstName": vet_dict.get("firstName", ""),
                "lastName": vet_dict.get("lastName", ""),
                "specialties": specialties_str
            }
            
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def search_vets(self, query: str, top_k: int = 20) -> List[str]:
        """
        Search for veterinarians using semantic similarity.
        
        Args:
            query: Search query (can be vet name, specialty, or general description)
            top_k: Number of top results to return
            
        Returns:
            List of vet information as JSON strings
        """
        if not self.vector_store:
            logger.warning("Vector store not initialized")
            return []
        
        try:
            # Perform similarity search
            docs = self.vector_store.similarity_search(query, k=top_k)
            
            # Extract content from documents
            results = [doc.page_content for doc in docs]
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vets: {e}")
            return []
    
    def get_vector_store(self) -> Optional[Chroma]:
        """Get the vector store instance"""
        return self.vector_store

