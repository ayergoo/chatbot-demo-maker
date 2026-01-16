#!/usr/bin/env python3
"""
Test script for chatbot_demo_maker.py
Tests the scraping and text extraction functionality without requiring OpenAI API
"""

from chatbot_demo_maker import WebsiteScraper
from bs4 import BeautifulSoup

def test_text_extraction():
    """Test that HTML text extraction works correctly"""
    scraper = WebsiteScraper("https://example.com")
    
    # Test HTML
    html = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <nav>Navigation Menu</nav>
            <h1>Welcome to Test Company</h1>
            <p>We provide excellent services.</p>
            <script>alert('test');</script>
            <footer>Copyright 2024</footer>
        </body>
    </html>
    """
    
    text = scraper.extract_text_from_html(html)
    
    # Verify script/nav/footer are removed
    assert "alert" not in text.lower(), "Script content should be removed"
    assert "navigation" not in text.lower(), "Nav content should be removed"
    assert "copyright" not in text.lower(), "Footer content should be removed"
    
    # Verify main content is preserved
    assert "welcome to test company" in text.lower(), "Main heading should be preserved"
    assert "excellent services" in text.lower(), "Paragraph content should be preserved"
    
    print("✓ Text extraction test passed")

def test_url_validation():
    """Test that URL validation works correctly"""
    scraper = WebsiteScraper("https://example.com")
    
    # Same domain
    assert scraper.is_valid_url("https://example.com/about"), "Should accept same domain URL"
    
    # Different domain
    assert not scraper.is_valid_url("https://different.com"), "Should reject different domain"
    
    # Relative URL (empty netloc)
    assert scraper.is_valid_url("/about"), "Should accept relative URL"
    
    print("✓ URL validation test passed")

def test_scraper_initialization():
    """Test that WebsiteScraper initializes correctly"""
    scraper = WebsiteScraper("https://example.com", max_pages=10)
    
    assert scraper.base_url == "https://example.com"
    assert scraper.max_pages == 10
    assert scraper.domain == "example.com"
    assert len(scraper.visited_urls) == 0
    assert len(scraper.pages_content) == 0
    
    print("✓ Scraper initialization test passed")

if __name__ == "__main__":
    print("Running tests for chatbot_demo_maker.py\n")
    
    try:
        test_scraper_initialization()
        test_url_validation()
        test_text_extraction()
        
        print("\n" + "="*50)
        print("All tests passed! ✓")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
