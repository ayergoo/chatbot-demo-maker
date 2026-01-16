#!/usr/bin/env python3
"""
Chatbot Demo Maker - Automatically scrapes website content and creates chatbot scenarios
"""

import os
import sys
import argparse
import shutil
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from openai import OpenAI
import time
import json
from typing import Optional

SAVE_PATH_BASE = "C:/Data/scraped_websites/"
SAVE_PATH_DOMAIN = SAVE_PATH_BASE + "{domain}/"
SAVE_RAW = SAVE_PATH_DOMAIN + "raw/"
SAVE_CLEAN = SAVE_PATH_DOMAIN + "clean/"

class WebsiteScraper:
    """Scrapes all pages from a website and extracts text content"""
    
    def __init__(self, base_url, max_pages=50, render_js=False, render_timeout_ms=30000):
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited_urls = set()
        self.domain = urlparse(base_url).netloc
        self.pages_content = []
        self.render_js = render_js
        self.render_timeout_ms = render_timeout_ms
        
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
        text = soup.get_text(separator=' ')
        
        # Break into lines and remove leading/trailing space
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text

    def _fetch_html(self, url) -> Optional[str]:
        if not self.render_js:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '')
            if 'text/html' not in content_type:
                return None
            return response.text

        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:
            raise RuntimeError(
                "Playwright is required for JS-rendered pages. Install it with: pip install playwright; playwright install"
            ) from e

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=self.render_timeout_ms)
            html = page.content()
            browser.close()
            return html

    def scrape_page(self, url):
        """Scrape a single page and return its text content"""
        try:
            html = self._fetch_html(url)
            if not html:
                return None, []
            
            text = self.extract_text_from_html(html)
            print('page char length: ', len(text))
            # Extract links for further crawling
            soup = BeautifulSoup(html, 'html.parser')
            
            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href') or ''
                if (
                    not href
                    or href.startswith('mailto')
                    or href == '/'
                    ):
                    continue

                absolute_url = urljoin(url, href)
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

    @staticmethod
    def save_pages_content(content_list:list, dir:str):
        """Save pages to location"""
        for i, page in enumerate(content_list):
            url = page['url']
            
            # remove http, so it can be split by /
            if 'www' in url:
                url = url.split('www', 1)[1]
            if 'http' in url:
                url = url.split('.', 1)[1]

            ext = url.split('/', 1)
            if len(ext) > 1:
                ext = ext[1]
            else:
                ext = ext[0]

            ext_norm = ext.replace('/', '_').replace('.', '_')
            
            filename = f'{i}_{ext_norm}.json'
            save_path = dir + filename
            with open(save_path, 'w') as f:
                json.dump(page, f, indent=2)

class ChatbotDemoMaker:
    """Creates chatbot demo scenarios using OpenAI API"""
    
    def __init__(self, api_key, max_chars_per_page):
        self.client = OpenAI(api_key=api_key)
        self.max_chars_per_page = max_chars_per_page
    
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
{text[:self.max_chars_per_page]}  

Return only the cleaned text."""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
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
                model="gpt-4o-mini",
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


def normalize_domain_name(domain_name):
    if 'www' in domain_name:
        domain_name = domain_name.split('.', 1)[1]

    if 'http' in domain_name:
        domain_name = domain_name.split('/', 2)[-1]

    return domain_name.replace('.', '_').replace('/', '_')[:80]

def create_domain_dir(normalized_domain_name, skip_clean):
    # norm_domain_name = normalize_domain_name(domain_name)
    os.mkdir(SAVE_PATH_DOMAIN.format(domain=normalized_domain_name))
    os.mkdir(SAVE_RAW.format(domain=normalized_domain_name))
    if not skip_clean:
        os.mkdir(SAVE_CLEAN.format(domain=normalized_domain_name))

def main():
    """Main function to run the chatbot demo maker"""
    parser = argparse.ArgumentParser(description="Chatbot Demo Maker")
    parser.add_argument("url", nargs="?", help="Website URL to scrape")
    parser.add_argument("--max-pages", type=int, default=50, help="Maximum pages to scrape (default: 50)")
    parser.add_argument("--max-chars", type=int, default=10000, help="Maximum characters per page (default: 10000)")
    parser.add_argument("--skip-clean", action="store_true", help="Skip OpenAI cleanup of pages")
    args = parser.parse_args()

    # Get URL from command line or prompt
    url = args.url or input("Enter the website URL to scrape: ").strip()
    
    if not url:
        print("Error: No URL provided")
        sys.exit(1)
    
    url = url.strip().strip('/')

    # Add https:// if no protocol specified
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print(f"\n{'='*60}")
    print(f"Chatbot Demo Maker")
    print(f"{'='*60}")
    print(f"Target URL: {url}\n")

    # Step 0: Check if already exists
    print("Step 0: Check if already been scraped...")
    normalized_url = normalize_domain_name(url)
    if os.path.exists(SAVE_PATH_DOMAIN.format(domain=normalized_url)):
        print("Error: Domain already exists in scraped domains")
        sys.exit(1)
    else:
        create_domain_dir(normalized_url, args.skip_clean)

    # get save dirs
    save_dir = SAVE_PATH_DOMAIN.format(domain=normalized_url)
    save_raw_dir = SAVE_RAW.format(domain=normalized_url)
    save_clean_dir = SAVE_CLEAN.format(domain=normalized_url)
    
    # Step 1: Scrape the website
    print("Step 1: Scraping website pages...")
    scraper = WebsiteScraper(
        url,
        max_pages=args.max_pages,
        render_js=True,
    )
    pages_content = scraper.crawl()
    
    if not pages_content:
        print("Error: No pages were scraped successfully")
        shutil.rmtree(save_dir)
        sys.exit(1)
    
    scraper.save_pages_content(pages_content, save_raw_dir)
    print(f"Saved raw pages to: {save_raw_dir}")

    # Get OpenAI API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        shutil.rmtree(save_dir)
        sys.exit(1)

    demo_maker = ChatbotDemoMaker(api_key, args.max_chars)

    # Step 2: Clean the text using OpenAI
    if args.skip_clean:
        print("\nStep 2: Skipping text cleanup...")
        scenario_pages = [
            {"url": page["url"], "cleaned_text": page["text"]}
            for page in pages_content
        ]
    else:
        print("\nStep 2: Cleaning text with OpenAI...")
        cleaned_pages = demo_maker.process_all_pages(pages_content)
        scenario_pages = cleaned_pages
        
        scraper.save_pages_content(cleaned_pages, save_clean_dir)
        print(f"Saved clean pages to: {save_clean_dir}")

    # Step 3: Create the chatbot scenario
    print("\nStep 3: Creating chatbot scenario...")
    scenario = demo_maker.combine_and_create_scenario(scenario_pages)
    
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
    output_file = save_dir + "chatbot_scenario.json"
    with open(output_file, 'w') as f:
        json.dump({
            'source_url': url,
            'pages_scraped': len(pages_content),
            'scenario': scenario,
        }, f, indent=2)
    
    print(f"{'='*60}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    
    main()
