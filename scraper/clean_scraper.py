#!/usr/bin/env python3
"""
Clean scraper to fetch complete assessment data from individual SHL pages.
Shows progress for every entry scraped.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup

class SHLAssessmentScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
        self.success_count = 0
        self.error_count = 0
        
    def fetch_page(self, url: str, timeout: int = 60) -> Optional[str]:
        """Fetch page content with error handling."""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"      ❌ Error fetching: {str(e)[:60]}")
            return None
    
    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from page."""
        # Try to find Description heading
        desc_heading = soup.find('h4', string=re.compile(r'Description', re.I))
        if desc_heading:
            # Get next paragraph or div
            next_elem = desc_heading.find_next_sibling(['p', 'div'])
            if next_elem:
                text = next_elem.get_text(strip=True)
                # Clean up
                text = re.sub(r'\s+', ' ', text)
                if text and len(text) > 20 and 'cookie' not in text.lower():
                    return text
        return None
    
    def extract_duration(self, soup: BeautifulSoup, html: str) -> Optional[int]:
        """Extract duration from page."""
        # Try finding in "Assessment length" section
        length_heading = soup.find('h4', string=re.compile(r'Assessment length', re.I))
        if length_heading:
            next_elem = length_heading.find_next_sibling(['p', 'div'])
            if next_elem:
                text = next_elem.get_text()
                match = re.search(r'(\d+)', text)
                if match:
                    return int(match.group(1))
        
        # Try finding "Approximate Completion Time"
        match = re.search(r'Approximate Completion Time in minutes\s*=\s*(\d+)', html)
        if match:
            return int(match.group(1))
        
        return None
    
    def extract_test_type(self, html: str) -> List[str]:
        """Extract test type from page."""
        match = re.search(r'Test Type:\s*([KP])', html)
        if match:
            code = match.group(1)
            if code == 'K':
                return ["Knowledge & Skills"]
            elif code == 'P':
                return ["Personality & Behaviour"]
        return []
    
    def extract_remote_support(self, html: str) -> str:
        """Check if remote testing is supported."""
        if re.search(r'Remote Testing:', html):
            return "Yes"
        return "No"
    
    def extract_adaptive_support(self, html: str, soup: BeautifulSoup) -> str:
        """Check if adaptive testing is supported."""
        # Look for adaptive keywords
        if re.search(r'adaptive|computer adaptive', html, re.I):
            return "Yes"
        return "No"
    
    def scrape_assessment(self, name: str, url: str, existing_test_type: List = None) -> Optional[Dict]:
        """
        Scrape a single assessment page.
        
        Returns:
            Dictionary with complete assessment data or None if failed
        """
        print(f"\n  📄 {name}")
        print(f"     URL: {url}")
        
        # Fetch page
        html = self.fetch_page(url)
        if not html:
            self.error_count += 1
            return None
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check for 404
        if soup.find(string=re.compile(r"We'll try to fix this soon|404", re.I)):
            print(f"      ⚠️  Page not found (404)")
            self.error_count += 1
            return None
        
        # Extract all fields
        description = self.extract_description(soup)
        duration = self.extract_duration(soup, html)
        test_type = self.extract_test_type(html)
        remote_support = self.extract_remote_support(html)
        adaptive_support = self.extract_adaptive_support(html, soup)
        
        # Use existing test_type if we couldn't extract it
        if not test_type and existing_test_type:
            test_type = existing_test_type
        
        # Build assessment object
        assessment = {
            "url": url,
            "name": name,
            "adaptive_support": adaptive_support,
            "description": description if description else f"Multi-choice test that measures the knowledge of {name}.",
            "duration": duration,
            "remote_support": remote_support,
            "test_type": test_type if test_type else ["Knowledge & Skills"]
        }
        
        # Print what we found
        print(f"      ✅ Description: {assessment['description'][:60]}...")
        print(f"      ✅ Duration: {assessment['duration']} minutes")
        print(f"      ✅ Type: {', '.join(assessment['test_type'])}")
        print(f"      ✅ Remote: {assessment['remote_support']}, Adaptive: {assessment['adaptive_support']}")
        
        self.success_count += 1
        return assessment
    
    def scrape_all(self, assessments: List[Dict], delay: float = 3.0) -> List[Dict]:
        """
        Scrape all assessments.
        
        Args:
            assessments: List of dicts with 'name' and 'url'
            delay: Delay between requests in seconds
            
        Returns:
            List of complete assessment dictionaries
        """
        total = len(assessments)
        results = []
        
        print(f"\n{'='*80}")
        print(f"🚀 Starting to scrape {total} assessments")
        print(f"{'='*80}")
        
        for i, assessment in enumerate(assessments, 1):
            print(f"\n[{i}/{total}] ({i/total*100:.1f}%)", end='')
            
            name = assessment.get('name', 'Unknown')
            url = assessment.get('url', '')
            existing_test_type = assessment.get('test_type', [])
            
            if not url:
                print(f"\n  ❌ {name}: No URL")
                self.error_count += 1
                continue
            
            # Scrape the assessment
            result = self.scrape_assessment(name, url, existing_test_type)
            
            if result:
                results.append(result)
            
            # Progress update every 25 assessments
            if i % 25 == 0:
                print(f"\n{'─'*80}")
                print(f"📊 Progress: {i}/{total} | Success: {self.success_count} | Errors: {self.error_count}")
                print(f"{'─'*80}")
            
            # Delay to be respectful to server
            if i < total:
                time.sleep(delay)
        
        return results
    
    def save_results(self, assessments: List[Dict], output_path: Path):
        """Save results to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(assessments, f, indent=2, ensure_ascii=False)
        print(f"\n\n✅ Saved {len(assessments)} assessments to {output_path}")
    
    def print_summary(self, total: int):
        """Print final summary."""
        print(f"\n{'='*80}")
        print("📊 SCRAPING COMPLETE")
        print(f"{'='*80}")
        print(f"✅ Successfully scraped: {self.success_count}/{total}")
        print(f"❌ Errors: {self.error_count}/{total}")
        print(f"📈 Success rate: {self.success_count/total*100:.1f}%")
        print(f"{'='*80}\n")


def main():
    """Main execution."""
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / "data" / "scraped_assessments.json"
    output_path = base_dir / "data" / "scraped_assessments_complete.json"
    
    # Load existing data
    print("📂 Loading assessments...")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            assessments = json.load(f)
        print(f"✅ Loaded {len(assessments)} assessments")
    except Exception as e:
        print(f"❌ Error loading {input_path}: {e}")
        return
    
    # Create scraper
    scraper = SHLAssessmentScraper()
    
    # Scrape all
    try:
        results = scraper.scrape_all(assessments, delay=3.0)
        
        # Save
        scraper.save_results(results, output_path)
        scraper.print_summary(len(assessments))
        
        # Show samples
        print("\n📋 Sample entries:")
        for i, assessment in enumerate(results[:3], 1):
            print(f"\n{i}. {json.dumps(assessment, indent=2)}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted! Saving what we have...")
        if results:
            scraper.save_results(results, output_path)
            scraper.print_summary(len(assessments))


if __name__ == "__main__":
    main()
