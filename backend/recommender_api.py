"""
Lightweight Recommendation Engine for Render deployment
Uses Google Gemini API for query embeddings (no heavy local models)
"""

import os
import json
from typing import List, Dict, Optional
from collections import defaultdict
import re

from backend.embedding_pipeline_api import APIEmbeddingPipeline


class APIRecommendationEngine:
    def __init__(self, chroma_dir: str = "./chroma_db"):
        """Initialize with API-based embedding pipeline (lightweight)"""
        self.embedding_pipeline = APIEmbeddingPipeline(persist_directory=chroma_dir)
        
        # Try to load the collection (pre-computed embeddings)
        try:
            self.embedding_pipeline.collection = self.embedding_pipeline.client.get_collection(
                name=self.embedding_pipeline.collection_name
            )
            print(f"✓ Loaded collection with {self.embedding_pipeline.collection.count()} assessments")
        except Exception as e:
            print(f"⚠ Warning: Could not load collection: {e}")
    
    def enhance_query(self, query: str) -> str:
        """
        Enhance user query for better semantic search
        """
        query = query.strip()
        
        # Already good as-is for semantic search
        return query
    
    def balance_recommendations(self, results: List[Dict], min_results: int = 5, max_results: int = 10) -> List[Dict]:
        """
        Balance recommendations across different test types
        """
        if not results:
            return []
        
        # Group by test type
        type_groups = defaultdict(list)
        # Normalize test_type to a hashable key (string). metadata may contain list/tuple.
        for rec in results:
            test_type = rec.get('test_type', 'Unknown')
            if isinstance(test_type, (list, tuple)):
                key = ', '.join([str(t) for t in test_type])
            else:
                key = str(test_type)
            # store the normalized key temporarily for later cleanup
            rec['_test_type_key'] = key
            type_groups[key].append(rec)
        
        # Balanced selection
        balanced = []
        type_order = list(type_groups.keys())

        # Round-robin selection
        while len(balanced) < max_results and any(type_groups.values()):
            for test_type in type_order:
                if type_groups[test_type]:
                    balanced.append(type_groups[test_type].pop(0))
                    if len(balanced) >= max_results:
                        break

        # Ensure minimum
        if len(balanced) < min_results and results:
            for rec in results:
                if rec not in balanced:
                    balanced.append(rec)
                    if len(balanced) >= min_results:
                        break

        # Clean up temporary keys before returning
        final = balanced[:max_results]
        for r in final:
            if '_test_type_key' in r:
                del r['_test_type_key']

        return final
    
    def get_recommendations(self, query: str, min_results: int = 5, max_results: int = 10) -> Dict:
        """
        Get assessment recommendations based on query
        """
        try:
            # Enhance query
            enhanced_query = self.enhance_query(query)
            
            # Search using API embeddings
            search_results = self.embedding_pipeline.search(enhanced_query, n_results=20)
            
            # Process results
            recommendations = []
            if search_results and 'metadatas' in search_results:
                for metadata in search_results['metadatas'][0]:
                    # Parse test_type back to list if it's a string
                    test_type = metadata.get('test_type', '')
                    if isinstance(test_type, str):
                        test_type = [t.strip() for t in test_type.split(',')]
                    
                    rec = {
                        'url': metadata.get('url', ''),
                        'assessment_name': metadata.get('assessment_name', ''),
                        'adaptive_support': metadata.get('adaptive_support', 'No'),
                        'description': metadata.get('description', ''),
                        'duration': metadata.get('duration'),
                        'remote_support': metadata.get('remote_support', 'No'),
                        'test_type': test_type
                    }
                    recommendations.append(rec)
            
            # Balance recommendations
            balanced_recs = self.balance_recommendations(recommendations, min_results, max_results)
            
            return {
                'query': query,
                'recommendations': balanced_recs,
                'total_found': len(recommendations)
            }
            
        except Exception as e:
            print(f"Error in get_recommendations: {e}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}
