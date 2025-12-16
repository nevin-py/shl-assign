"""
Embedding Pipeline using Sentence-Transformers (local) and ChromaDB
No API limits - runs entirely locally
"""

import os
import json
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class LocalEmbeddingPipeline:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize the embedding pipeline with ChromaDB and local embeddings
        """
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Load local sentence transformer model
        # Using all-MiniLM-L6-v2: fast, efficient, good quality
        print("Loading local embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully!")
        
        # Create or get collection
        self.collection_name = "shl_assessments"
        self.collection = None
    
    def create_collection(self, reset: bool = False):
        """
        Create or get the ChromaDB collection
        """
        if reset:
            try:
                self.client.delete_collection(name=self.collection_name)
                print(f"Deleted existing collection: {self.collection_name}")
            except:
                pass
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        print(f"Collection '{self.collection_name}' ready with {self.collection.count()} items")
        return self.collection
    
    def prepare_document_text(self, assessment: Dict) -> str:
        """
        Prepare text for embedding by combining relevant fields
        Uses only authentic data from SHL catalog
        """
        parts = []
        
        # Assessment name (most important)
        name = assessment.get('name') or assessment.get('assessment_name', '')
        if name:
            parts.append(name)
        
        # Test type - now stored as full names in a list
        if assessment.get('test_type'):
            test_type = assessment['test_type']
            if isinstance(test_type, list):
                # Join list of full category names
                type_text = ', '.join(test_type)
            else:
                type_text = str(test_type)
            parts.append(type_text)
        
        # Description provides rich semantic context
        if assessment.get('description'):
            parts.append(assessment['description'])
        
        return " | ".join(parts)
    
    def load_and_embed_assessments(self, json_file: str = "data/scraped_assessments_complete.json"):
        """
        Load assessments from JSON and create embeddings in ChromaDB
        """
        # Load assessments
        with open(json_file, 'r', encoding='utf-8') as f:
            assessments = json.load(f)
        
        print(f"Loaded {len(assessments)} assessments from {json_file}")
        
        # Create collection
        self.create_collection(reset=True)
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for i, assessment in enumerate(assessments):
            # Create unique ID
            assessment_id = f"assessment_{i}"
            ids.append(assessment_id)
            
            # Prepare document text for embedding
            doc_text = self.prepare_document_text(assessment)
            documents.append(doc_text)
            
            # Store metadata - include all fields for API response
            metadata = {
                'assessment_name': assessment.get('name', ''),
                'url': assessment.get('url', ''),
                'test_type': ', '.join(assessment.get('test_type', [])) if isinstance(assessment.get('test_type'), list) else assessment.get('test_type', ''),
                'description': assessment.get('description', ''),
                'duration': assessment.get('duration'),
                'adaptive_support': assessment.get('adaptive_support', 'No'),
                'remote_support': assessment.get('remote_support', 'No')
            }
            # Remove None values
            metadata = {k: v for k, v in metadata.items() if v is not None}
            metadatas.append(metadata)
        
        # Generate embeddings using local model
        print("Generating embeddings locally (this may take a minute)...")
        embeddings = self.model.encode(documents, show_progress_bar=True)
        
        # Add to ChromaDB
        print("Adding to ChromaDB...")
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )
        
        print(f"✓ Successfully embedded {len(assessments)} assessments!")
        print(f"✓ Collection now contains {self.collection.count()} items")
        
        return self.collection
    
    def search(self, query: str, n_results: int = 10) -> Dict:
        """
        Search for assessments similar to the query
        """
        if not self.collection:
            self.collection = self.client.get_collection(name=self.collection_name)
        
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
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
            "persist_directory": self.persist_directory
        }


def main():
    """
    Main function to create embeddings
    """
    print("=" * 80)
    print("SHL Assessment Embedding Pipeline (Local - No API Limits)")
    print("=" * 80)
    
    pipeline = LocalEmbeddingPipeline()
    
    # Load and embed assessments
    pipeline.load_and_embed_assessments()
    
    # Show stats
    stats = pipeline.get_stats()
    print(f"\n{'='*80}")
    print("Collection Statistics:")
    print(f"  - Collection: {stats['collection_name']}")
    print(f"  - Total Assessments: {stats['total_assessments']}")
    print(f"  - Storage: {stats['persist_directory']}")
    print(f"{'='*80}")
    
    # Test search
    print("\nTesting search with query: 'Python programming'")
    results = pipeline.search("Python programming", n_results=5)
    print("\nTop 5 results:")
    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"{i+1}. {metadata['assessment_name']} ({metadata['test_type']})")
    
    print("\n✓ Embedding pipeline setup complete!")


if __name__ == "__main__":
    main()
