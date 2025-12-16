"""
Recommendation Engine using ChromaDB with local embeddings
Simplified version without Gemini re-ranking to avoid quota issues
"""

import os
import sys
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.embedding_pipeline_local import LocalEmbeddingPipeline
from dotenv import load_dotenv

load_dotenv()


class LocalRecommendationEngine:
    def __init__(self, chroma_dir: str = "./chroma_db"):
        """Initialize recommendation engine with local embeddings"""
        self.embedding_pipeline = LocalEmbeddingPipeline(persist_directory=chroma_dir)
        
        # Load existing collection
        try:
            self.embedding_pipeline.collection = self.embedding_pipeline.client.get_collection(
                name=self.embedding_pipeline.collection_name
            )
            print(f"Loaded collection with {self.embedding_pipeline.collection.count()} assessments")
        except Exception as e:
            print(f"Warning: Could not load collection: {e}")
    
    def extract_url_context(self, query: str) -> str:
        """Extract context from URL if present"""
        import re
        
        # Check if query contains a URL
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, query)
        
        if urls:
            # Extract key terms from URL
            url = urls[0]
            # Remove protocol and common words
            clean_url = url.replace('https://', '').replace('http://', '').replace('www.', '')
            # Extract meaningful parts
            parts = clean_url.split('/')
            keywords = []
            for part in parts:
                # Split by hyphens and underscores
                words = part.replace('-', ' ').replace('_', ' ').split()
                keywords.extend([w for w in words if len(w) > 2])
            
            return ' '.join(keywords)
        
        return query
    
    def enhance_query(self, query: str) -> str:
        """
        Enhance the query for better search results
        """
        # Extract URL context if present
        enhanced = self.extract_url_context(query)
        
        # Add common skill-related terms
        skill_keywords = {
            'developer': 'programming coding software development',
            'data scientist': 'data analysis statistics machine learning python',
            'manager': 'leadership team management communication',
            'analyst': 'analysis problem solving critical thinking',
            'engineer': 'technical engineering problem solving',
            'designer': 'design creativity user experience',
            'sales': 'communication persuasion customer relationship',
            'marketing': 'communication strategy creative content'
        }
        
        query_lower = query.lower()
        for role, keywords in skill_keywords.items():
            if role in query_lower:
                enhanced = f"{enhanced} {keywords}"
                break
        
        return enhanced
    
    def balance_recommendations(self, results: List[Dict], min_k: int = 2) -> List[Dict]:
        """
        Balance recommendations to include both K (knowledge/skills) and other types
        """
        def is_knowledge_test(r):
            test_type = r.get('test_type', [])
            if isinstance(test_type, list):
                return any('K' in str(t) or 'Knowledge' in str(t) for t in test_type)
            return 'K' in str(test_type) or 'Knowledge' in str(test_type)
        
        k_tests = [r for r in results if is_knowledge_test(r)]
        other_tests = [r for r in results if not is_knowledge_test(r)]
        
        # Ensure at least min_k knowledge tests
        balanced = k_tests[:min_k]
        
        # Add other types
        balanced.extend(other_tests[:3])
        
        # Fill remaining with top results
        remaining_slots = 10 - len(balanced)
        if remaining_slots > 0:
            all_results = k_tests[min_k:] + other_tests[3:]
            balanced.extend(all_results[:remaining_slots])
        
        return balanced[:10]
    
    def get_recommendations(self, query: str, min_results: int = 5, max_results: int = 10) -> Dict:
        """
        Get assessment recommendations for a query
        
        Pipeline:
        1. Enhance query with context
        2. Retrieve candidates from ChromaDB
        3. Balance recommendations (knowledge + behavioral)
        4. Return top results
        """
        try:
            # Step 1: Enhance query
            enhanced_query = self.enhance_query(query)
            
            # Step 2: Retrieve from ChromaDB
            search_results = self.embedding_pipeline.search(enhanced_query, n_results=20)
            
            if not search_results or not search_results.get('metadatas'):
                return {
                    'query': query,
                    'recommendations': [],
                    'message': 'No matching assessments found'
                }
            
            # Step 3: Format results
            recommendations = []
            metadatas = search_results['metadatas'][0]
            distances = search_results['distances'][0] if 'distances' in search_results else [0] * len(metadatas)
            
            for metadata, distance in zip(metadatas, distances):
                # Parse test_type
                test_type = metadata.get('test_type', '')
                if isinstance(test_type, str):
                    # Split comma-separated string or single value
                    test_type = [t.strip() for t in test_type.split(',')] if ',' in test_type else [test_type]
                
                # Parse duration
                duration = metadata.get('duration', '')
                if isinstance(duration, str):
                    duration = int(duration) if duration and duration.isdigit() else None
                elif duration == '':
                    duration = None
                
                # Parse adaptive_support and remote_support (convert bool to string)
                adaptive_support = metadata.get('adaptive_support', False)
                if isinstance(adaptive_support, bool):
                    adaptive_support = 'Yes' if adaptive_support else 'No'
                
                remote_support = metadata.get('remote_support', False)
                if isinstance(remote_support, bool):
                    remote_support = 'Yes' if remote_support else 'No'
                
                rec = {
                    'assessment_name': metadata.get('assessment_name', ''),
                    'url': metadata.get('url', ''),
                    'description': metadata.get('description', ''),
                    'duration': duration,
                    'adaptive_support': adaptive_support,
                    'remote_support': remote_support,
                    'test_type': test_type if test_type else [],
                    'relevance_score': round(1 - distance, 3)  # Convert distance to similarity
                }
                recommendations.append(rec)
            
            # Step 4: Balance recommendations
            balanced_recs = self.balance_recommendations(recommendations)
            
            # Limit to requested range
            final_recs = balanced_recs[: max_results]
            
            return {
                'query': query,
                'enhanced_query': enhanced_query,
                'total_found': len(recommendations),
                'recommendations': final_recs
            }
            
        except Exception as e:
            return {
                'query': query,
                'error': str(e),
                'recommendations': []
            }


def main():
    """Test the recommendation engine"""
    print("=" * 80)
    print("Testing Local Recommendation Engine")
    print("=" * 80)
    
    engine = LocalRecommendationEngine()
    
    # Test queries
    test_queries = [
        "Python programming skills",
        "Leadership and management assessment",
        "Data science and machine learning",
        "https://www.linkedin.com/jobs/view/software-engineer"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        result = engine.get_recommendations(query)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Enhanced Query: {result['enhanced_query']}")
            print(f"Found {result['total_found']} matches, returning top {len(result['recommendations'])}:")
            print()
            
            for i, rec in enumerate(result['recommendations'], 1):
                print(f"{i}. {rec['assessment_name']} ({rec['test_type']})")
                print(f"   Score: {rec['relevance_score']}")
                print(f"   URL: {rec['url']}")
                print()


if __name__ == "__main__":
    main()
