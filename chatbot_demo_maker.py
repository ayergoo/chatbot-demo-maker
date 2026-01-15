#!/usr/bin/env python3
"""
Chatbot Demo Maker - Automatically scrapes website content and creates chatbot scenarios
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from openai import OpenAI
import time
import json


class WebsiteScraper:
    """Scrapes all pages from a website and extracts text content"""
    
    def __init__(self, base_url, max_pages=50):
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited_urls = set()
        self.domain = urlparse(base_url).netloc
        self.pages_content = []
        
    def is_valid_url(self, url):
        """Check if URL belongs to the same domain"""
        parsed = urlparse(url)
        return parsed.netloc == self.domain or parsed.netloc == ''
    
    def extract_text_from_html(self, html):
        """Extract readable text from HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading/trailing space
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def scrape_page(self, url):
        """Scrape a single page and return its text content"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Only process HTML content
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                return None, []
            
            text = self.extract_text_from_html(response.content)
            
            # Extract links for further crawling
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            for link in soup.find_all('a', href=True):
                absolute_url = urljoin(url, link['href'])
                # Remove fragments
                absolute_url = absolute_url.split('#')[0]
                if self.is_valid_url(absolute_url) and absolute_url not in self.visited_urls:
                    links.append(absolute_url)
            
            return text, links
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None, []
    
    def crawl(self):
        """Crawl the website starting from base_url"""
        urls_to_visit = [self.base_url]
        
        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            url = urls_to_visit.pop(0)
            
            if url in self.visited_urls:
                continue
            
            print(f"Scraping: {url} ({len(self.visited_urls) + 1}/{self.max_pages})")
            self.visited_urls.add(url)
            
            text, links = self.scrape_page(url)
            
            if text:
                self.pages_content.append({
                    'url': url,
                    'text': text
                })
            
            # Add new links to visit
            urls_to_visit.extend([link for link in links if link not in self.visited_urls])
        
        print(f"\nScraped {len(self.pages_content)} pages successfully")
        return self.pages_content


class ChatbotDemoMaker:
    """Creates chatbot demo scenarios using OpenAI API"""
    
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
    
    def clean_text(self, text, page_url):
        """Clean and tidy up text from a webpage using OpenAI"""
        try:
            prompt = f"""You are cleaning website content for use in a chatbot knowledge base.
            
Clean and format the following text from {page_url}:
- Remove navigation elements, redundant information, and formatting artifacts
- Keep only the meaningful content about the company/organization
- Maintain important facts, features, and information
- Make it concise and well-structured

Text to clean:
{text[:4000]}  

Return only the cleaned text."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that cleans and formats website content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            cleaned_text = response.choices[0].message.content
            return cleaned_text
            
        except Exception as e:
            print(f"Error cleaning text: {e}")
            return text[:1000]  # Return truncated original text as fallback
    
    def process_all_pages(self, pages_content):
        """Clean text from all scraped pages"""
        cleaned_pages = []
        
        print("\nCleaning text from scraped pages...")
        for i, page in enumerate(pages_content, 1):
            print(f"Cleaning page {i}/{len(pages_content)}: {page['url']}")
            cleaned_text = self.clean_text(page['text'], page['url'])
            cleaned_pages.append({
                'url': page['url'],
                'cleaned_text': cleaned_text
            })
            # Rate limiting
            time.sleep(1)
        
        return cleaned_pages
    
    def combine_and_create_scenario(self, cleaned_pages):
        """Combine all cleaned text and create a chatbot scenario"""
        # Combine all cleaned text
        combined_text = "\n\n".join([
            f"From {page['url']}:\n{page['cleaned_text']}" 
            for page in cleaned_pages
        ])
        
        # Truncate if too long (to fit in API limits)
        if len(combined_text) > 10000:
            combined_text = combined_text[:10000] + "..."
        
        print("\nGenerating chatbot scenario...")
        
        try:
            prompt = f"""Based on the following information about a company/organization, create a chatbot demo scenario.

Company Information:
{combined_text}

Create a JSON response with the following structure:
{{
    "suggested_question": "A question a user might ask (this will be a clickable suggestion)",
    "initial_answer": "A helpful initial answer to the question",
    "followup_question": "A natural followup question the user might ask",
    "detailed_answer": "A more detailed, comprehensive answer to the followup"
}}

Make it realistic and based on the actual information provided. The scenario should showcase how the chatbot can help users learn about the company."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates engaging chatbot scenarios."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            scenario_text = response.choices[0].message.content
            
            # Try to parse as JSON
            try:
                # Find JSON in the response
                start_idx = scenario_text.find('{')
                end_idx = scenario_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = scenario_text[start_idx:end_idx]
                    scenario = json.loads(json_str)
                else:
                    scenario = json.loads(scenario_text)
            except json.JSONDecodeError:
                # If not valid JSON, create a structured response
                scenario = {
                    "suggested_question": "Tell me about your company",
                    "initial_answer": scenario_text[:200],
                    "followup_question": "What services do you offer?",
                    "detailed_answer": scenario_text[200:500] if len(scenario_text) > 200 else "We offer various services to meet your needs."
                }
            
            return scenario
            
        except Exception as e:
            print(f"Error creating scenario: {e}")
            return {
                "suggested_question": "Tell me about your company",
                "initial_answer": "We're here to help you.",
                "followup_question": "What can you do for me?",
                "detailed_answer": "We offer a variety of services and solutions."
            }


def main():
    """Main function to run the chatbot demo maker"""
    
    # Get OpenAI API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    # Get URL from command line or prompt
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter the website URL to scrape: ").strip()
    
    if not url:
        print("Error: No URL provided")
        sys.exit(1)
    
    # Add https:// if no protocol specified
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print(f"\n{'='*60}")
    print(f"Chatbot Demo Maker")
    print(f"{'='*60}")
    print(f"Target URL: {url}\n")
    
    # Step 1: Scrape the website
    print("Step 1: Scraping website pages...")
    scraper = WebsiteScraper(url, max_pages=50)
    pages_content = scraper.crawl()
    
    if not pages_content:
        print("Error: No pages were scraped successfully")
        sys.exit(1)
    
    # Step 2: Clean the text using OpenAI
    print("\nStep 2: Cleaning text with OpenAI...")
    demo_maker = ChatbotDemoMaker(api_key)
    cleaned_pages = demo_maker.process_all_pages(pages_content)
    
    # Step 3: Create the chatbot scenario
    print("\nStep 3: Creating chatbot scenario...")
    scenario = demo_maker.combine_and_create_scenario(cleaned_pages)
    
    # Display results
    print(f"\n{'='*60}")
    print("CHATBOT DEMO SCENARIO")
    print(f"{'='*60}\n")
    
    print(f"Suggested Question (clickable):")
    print(f"  → {scenario['suggested_question']}\n")
    
    print(f"Initial Answer:")
    print(f"  {scenario['initial_answer']}\n")
    
    print(f"User Followup Question:")
    print(f"  → {scenario['followup_question']}\n")
    
    print(f"Detailed Answer:")
    print(f"  {scenario['detailed_answer']}\n")
    
    # Save to file
    output_file = "chatbot_scenario.json"
    with open(output_file, 'w') as f:
        json.dump({
            'source_url': url,
            'pages_scraped': len(pages_content),
            'scenario': scenario,
            'cleaned_pages': cleaned_pages
        }, f, indent=2)
    
    print(f"{'='*60}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
