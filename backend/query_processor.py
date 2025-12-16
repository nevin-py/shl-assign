"""
Query Processor using Google Gemini for query enhancement and JD parsing
"""

import os
import re
import validators
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()


class QueryProcessor:
    def __init__(self):
        """Initialize query processor with Gemini"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def is_url(self, text: str) -> bool:
        """Check if the input is a URL"""
        return validators.url(text) or bool(re.match(r'^https?://', text))
    
    def extract_jd_from_url(self, url: str) -> str:
        """Extract job description text from a URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # Limit to first 5000 characters
            
        except Exception as e:
            raise Exception(f"Error extracting JD from URL: {str(e)}")
    
    def enhance_query(self, query: str) -> str:
        """
        Use Gemini to enhance the query and extract key requirements
        """
        prompt = f"""You are an expert HR analyst. Analyze the following job description or query and extract the key skills, competencies, and assessment requirements.

Focus on:
1. Technical skills (programming languages, tools, technologies)
2. Soft skills (communication, teamwork, leadership)
3. Cognitive abilities (problem-solving, analytical thinking)
4. Personality traits (behavioral aspects)
5. Experience level

Query/JD:
{query}

Provide a concise summary of what assessments would be needed to evaluate candidates for this role. Focus on the types of tests needed (e.g., coding tests, personality assessments, cognitive tests, behavioral tests).

Summary:"""

        try:
            response = self.model.generate_content(prompt)
            enhanced_query = response.text.strip()
            return enhanced_query
        except Exception as e:
            print(f"Error enhancing query with Gemini: {e}")
            return query  # Return original query if enhancement fails
    
    def detect_skill_categories(self, query: str) -> Dict[str, bool]:
        """
        Detect what categories of skills are mentioned in the query
        Returns dict with boolean flags for different skill types
        """
        query_lower = query.lower()
        
        categories = {
            'technical': False,
            'behavioral': False,
            'cognitive': False,
            'personality': False,
            'language': False
        }
        
        # Technical keywords
        technical_keywords = ['java', 'python', 'sql', 'javascript', 'programming', 'coding', 
                             'developer', 'engineer', 'technical', 'software', 'data']
        if any(keyword in query_lower for keyword in technical_keywords):
            categories['technical'] = True
        
        # Behavioral keywords
        behavioral_keywords = ['collaborate', 'teamwork', 'communication', 'leadership', 
                              'stakeholder', 'management', 'interpersonal']
        if any(keyword in query_lower for keyword in behavioral_keywords):
            categories['behavioral'] = True
        
        # Cognitive keywords
        cognitive_keywords = ['problem-solving', 'analytical', 'critical thinking', 
                             'logical', 'reasoning', 'cognitive']
        if any(keyword in query_lower for keyword in cognitive_keywords):
            categories['cognitive'] = True
        
        # Personality keywords
        personality_keywords = ['personality', 'behavior', 'culture fit', 'values', 
                               'traits', 'emotional intelligence']
        if any(keyword in query_lower for keyword in personality_keywords):
            categories['personality'] = True
        
        return categories
    
    def process_query(self, raw_query: str) -> Dict:
        """
        Main query processing pipeline
        """
        # Check if it's a URL
        if self.is_url(raw_query):
            print(f"Detected URL, extracting job description...")
            try:
                jd_text = self.extract_jd_from_url(raw_query)
                processed_query = jd_text
            except Exception as e:
                return {
                    'error': str(e),
                    'original_query': raw_query
                }
        else:
            processed_query = raw_query
        
        # Enhance query with Gemini
        enhanced_query = self.enhance_query(processed_query)
        
        # Detect skill categories
        categories = self.detect_skill_categories(processed_query)
        
        return {
            'original_query': raw_query,
            'processed_query': processed_query,
            'enhanced_query': enhanced_query,
            'skill_categories': categories,
            'is_url': self.is_url(raw_query)
        }


def main():
    """Test the query processor"""
    processor = QueryProcessor()
    
    # Test queries
    test_queries = [
        "I need a Java developer who can collaborate with teams",
        "Looking for mid-level professionals proficient in Python, SQL and JavaScript",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Original Query: {query}")
        print('='*60)
        
        result = processor.process_query(query)
        
        print(f"\nEnhanced Query:\n{result['enhanced_query']}")
        print(f"\nSkill Categories: {result['skill_categories']}")


if __name__ == "__main__":
    main()
