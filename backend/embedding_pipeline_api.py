"""
Lightweight Embedding Pipeline using Google Gemini API
For deployment on memory-constrained environments (Render free tier)
Uses pre-computed embeddings from ChromaDB + API for query embeddings only
"""

import os
import google.generativeai as genai
from typing import Dict
import chromadb


class APIEmbeddingPipeline:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize lightweight pipeline with ChromaDB
        No heavy model loading - uses Google API for query embeddings
        """
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client (lightweight)
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Configure Google Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            print("✓ Google Gemini API configured for embeddings")
        else:
            print("⚠ Warning: GOOGLE_API_KEY not set, will fail on search")
        
        # Collection info
        self.collection_name = "shl_assessments"
        self.collection = None
    
    def search(self, query: str, n_results: int = 10) -> Dict:
        """
        Search for assessments using Google Gemini embeddings for query
        Assessment embeddings are pre-computed and stored in ChromaDB
        """
        if not self.collection:
            self.collection = self.client.get_collection(name=self.collection_name)
        
        # Generate query embedding using Google Gemini API
        # This is lightweight and doesn't require loading a local model
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=query,
                task_type="retrieval_query"
            )
            query_embedding = result['embedding']
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            raise
        
        # Search in ChromaDB using the query embedding
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return results
    
    def get_stats(self) -> Dict:
        """
        Get collection statistics
        """
        if not self.collection:
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
            except:
                return {"error": "Collection not found"}
        
        count = self.collection.count()
        
        return {
            "collection_name": self.collection_name,
            "total_assessments": count,
            "persist_directory": self.persist_directory,
            "embedding_method": "Google Gemini API (text-embedding-004)"
        }
