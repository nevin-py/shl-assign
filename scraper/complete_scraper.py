"""
Complete SHL Assessment Scraper
Fetches ALL required fields from individual assessment pages:
- name, url, description, duration, adaptive_support, remote_support, test_type
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from typing import List, Dict
import os
import re


class CompleteSHLScraper:
    def __init__(self):
        self.base_url = "https://www.shl.com"
        self.catalog_url = f"{self.base_url}/products/product-catalog/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def _parse_test_type(self, type_str: str) -> List[str]:
        """Parse test type codes from SHL catalog"""
        type_str = type_str.strip().upper()
        
        # Map letter codes to full names
        type_map = {
            'K': 'Knowledge & Skills',
            'C': 'Competencies',
            'P': 'Personality & Behaviour',
            'B': 'Personality & Behaviour',
            'S': 'Competencies',
            'A': 'Competencies',
            'E': 'Competencies',
            'D': 'Competencies'
        }
        
        # Extract all letter codes
        types = []
        for letter in type_str:
            if letter in type_map:
                full_name = type_map[letter]
                if full_name not in types:
                    types.append(full_name)
        
        return types if types else ['Knowledge & Skills']
    
    def scrape_assessment_details(self, url: str, assessment_name: str, retries: int = 2) -> Dict:
        """
        Scrape detailed information from individual assessment page with retry logic
        """
        for attempt in range(retries + 1):
            try:
                if attempt > 0:
                    print(f"  Retry {attempt}/{retries} for: {assessment_name[:40]}...", end=' ')
                    time.sleep(2)  # Wait before retry
                else:
                    print(f"  Fetching: {assessment_name[:40]}...", end=' ')
                
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract description - avoid browser warnings, cookie messages
                description = ""
                skip_phrases = ['cookie', 'browser', 'javascript', 'privacy policy', 
                               'upgrade', 'enable', 'accept', 'consent']
                
                # Try to find description in meta tags first
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    desc = meta_desc.get('content').strip()
                    if len(desc) > 30 and not any(phrase in desc.lower() for phrase in skip_phrases):
                        description = desc
                
                # Fallback: Look for meaningful paragraphs
                if not description:
                    paragraphs = soup.find_all('p')
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        # Skip short text, warnings, and navigation
                        if (len(text) > 50 and 
                            not any(phrase in text.lower() for phrase in skip_phrases) and
                            not text.startswith('Read more')):
                            description = text
                            break
                
                # Extract duration (look for "minutes", "min", time patterns)
                duration = None
                duration_patterns = [
                    r'(\d+)\s*min(?:ute)?s?',
                    r'Approximate\s+Completion\s+Time.*?=\s*(\d+)',
                    r'Duration:\s*(\d+)',
                    r'(\d+)\s*minutes?'
                ]
                
                page_text = soup.get_text()
                for pattern in duration_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        duration = int(match.group(1))
                        break
                
                # Extract adaptive_support and remote_support
                # Look for specific text indicators
                adaptive_support = "No"  # Default
                remote_support = "Yes"   # Default assumption for modern tests
                
                text_lower = page_text.lower()
                if 'adaptive' in text_lower:
                    adaptive_support = "Yes"
                if 'remote' in text_lower or 'online' in text_lower:
                    remote_support = "Yes"
                if 'in-person' in text_lower or 'on-site' in text_lower:
                    remote_support = "No"
                
                print("✓")
                return {
                    'description': description if description else f"Assessment for {assessment_name}",
                    'duration': duration,
                    'adaptive_support': adaptive_support,
                    'remote_support': remote_support
                }
                
            except Exception as e:
                if attempt < retries:
                    print(f"✗ (retrying...)")
                    continue
                else:
                    print(f"✗ (Error: {str(e)[:30]})")
                    # Return defaults if all retries fail
                    return {
                        'description': f"SHL assessment for {assessment_name}",
                        'duration': None,
                        'adaptive_support': "No",
                        'remote_support': "Yes"
                    }
    
    def scrape_catalog_page(self, catalog_type: int = 1, start: int = 0) -> List[Dict]:
        """Scrape assessments from catalog page (basic info)"""
        url = f"{self.catalog_url}?start={start}&type={catalog_type}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.find_all('table')
            
            assessments = []
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    
                    if len(cells) >= 2:
                        name_cell = cells[0]
                        type_cell = cells[-1]
                        
                        link = name_cell.find('a')
                        if not link:
                            continue
                        
                        assessment_name = link.get_text(strip=True)
                        assessment_url = link.get('href', '')
                        type_codes = type_cell.get_text(strip=True)
                        
                        if assessment_name and assessment_url:
                            # Build full URL
                            if assessment_url.startswith('/'):
                                full_url = f"{self.base_url}{assessment_url}"
                            else:
                                full_url = assessment_url
                            
                            # Parse test types
                            test_types = self._parse_test_type(type_codes)
                            
                            assessments.append({
                                'name': assessment_name,
                                'url': full_url,
                                'test_type': test_types
                            })
            
            return assessments
            
        except Exception as e:
            print(f"Error scraping page (type={catalog_type}, start={start}): {e}")
            return []
    
    def scrape_all_assessments(self, fetch_details: bool = True, max_assessments: int = 377) -> List[Dict]:
        """
        Scrape all assessments with complete details
        
        Args:
            fetch_details: If True, fetch details from individual pages (slower but complete)
            max_assessments: Maximum number to scrape (377 required)
        """
        print(f"Fetching Individual Test Solutions from {self.catalog_url}...")
        print(f"Target: {max_assessments} assessments\n")
        
        all_assessments = []
        seen_names = set()
        
        # Type 1: Individual Test Solutions (32 pages, ~12 items per page)
        print("Scraping Type 1: Individual Test Solutions...")
        for page in range(32):
            start = page * 12
            print(f"Page {page + 1}/32 (start={start})...")
            
            assessments = self.scrape_catalog_page(catalog_type=1, start=start)
            
            for assessment in assessments:
                if assessment['name'] not in seen_names:
                    seen_names.add(assessment['name'])
                    
                    # Fetch detailed information if enabled
                    if fetch_details:
                        details = self.scrape_assessment_details(
                            assessment['url'],
                            assessment['name']
                        )
                        assessment.update(details)
                        time.sleep(1.5)  # Rate limiting - be polite to server
                    else:
                        # Add default values
                        assessment.update({
                            'description': f"Assessment for {assessment['name']}",
                            'duration': None,
                            'adaptive_support': "No",
                            'remote_support': "Yes"
                        })
                    
                    all_assessments.append(assessment)
                    
                    # Stop if we've reached the target
                    if len(all_assessments) >= max_assessments:
                        print(f"\n✓ Reached target of {max_assessments} assessments")
                        return all_assessments[:max_assessments]
            
            time.sleep(0.5)  # Be nice to the server
        
        print(f"\nTotal assessments scraped: {len(all_assessments)}")
        return all_assessments[:max_assessments]
    
    def save_to_json(self, assessments: List[Dict], output_file: str):
        """Save assessments to JSON file"""
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(assessments, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved {len(assessments)} assessments to {output_file}")
    
    def scrape_and_save(self, output_file: str = 'data/scraped_assessments.json', 
                       fetch_details: bool = True,
                       max_assessments: int = 377):
        """Main method to scrape and save assessments"""
        assessments = self.scrape_all_assessments(
            fetch_details=fetch_details,
            max_assessments=max_assessments
        )
        
        if assessments:
            self.save_to_json(assessments, output_file)
            
            # Print summary
            print("\n" + "="*80)
            print("SCRAPING SUMMARY")
            print("="*80)
            print(f"Total assessments: {len(assessments)}")
            print(f"With descriptions: {sum(1 for a in assessments if a.get('description'))}")
            print(f"With duration: {sum(1 for a in assessments if a.get('duration'))}")
            print(f"\nSample assessment:")
            if assessments:
                sample = assessments[0]
                print(f"  Name: {sample['name']}")
                print(f"  URL: {sample['url']}")
                print(f"  Test Type: {sample['test_type']}")
                print(f"  Duration: {sample.get('duration', 'N/A')} min")
                print(f"  Description: {sample.get('description', 'N/A')[:100]}...")
                print(f"  Adaptive: {sample.get('adaptive_support', 'N/A')}")
                print(f"  Remote: {sample.get('remote_support', 'N/A')}")
            print("="*80)
        
        return assessments


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape SHL assessment catalog')
    parser.add_argument('--quick', action='store_true', 
                       help='Quick mode: skip fetching individual page details')
    parser.add_argument('--max', type=int, default=377,
                       help='Maximum number of assessments to scrape (default: 377)')
    
    args = parser.parse_args()
    
    scraper = CompleteSHLScraper()
    
    print("="*80)
    print("SHL COMPLETE ASSESSMENT SCRAPER")
    print("="*80)
    print(f"Mode: {'QUICK (catalog only)' if args.quick else 'COMPLETE (with details)'}")
    print(f"Target: {args.max} assessments")
    print("="*80)
    print()
    
    if not args.quick:
        print("⚠️  This will take 5-10 minutes to fetch details from individual pages")
        print("   Use --quick flag to scrape only basic info (faster)\n")
    
    assessments = scraper.scrape_and_save(
        fetch_details=not args.quick,
        max_assessments=args.max
    )
    
    print(f"\n✓ Complete! Scraped {len(assessments)} assessments")
