#!/usr/bin/env python3
"""
Example usage of the Chatbot Demo Maker

This script demonstrates how to use the chatbot_demo_maker module
to create a chatbot scenario from website content.
"""

import os
import sys

# Example 1: Using the script directly from command line
print("="*60)
print("CHATBOT DEMO MAKER - USAGE EXAMPLES")
print("="*60)
print()

print("1. Run with a URL as argument:")
print("   python chatbot_demo_maker.py https://example.com")
print()

print("2. Run and be prompted for URL:")
print("   python chatbot_demo_maker.py")
print()

print("3. Set OpenAI API key:")
print("   export OPENAI_API_KEY='your-api-key-here'")
print()

print("4. Example with a real website:")
print("   export OPENAI_API_KEY='sk-...'")
print("   python chatbot_demo_maker.py https://python.org")
print()

print("="*60)
print("OUTPUT")
print("="*60)
print()
print("The script will:")
print("  1. Scrape all pages from the website")
print("  2. Clean the text using OpenAI")
print("  3. Generate a chatbot scenario")
print("  4. Save results to chatbot_scenario.json")
print()

print("="*60)
print("EXAMPLE OUTPUT STRUCTURE")
print("="*60)
print()
print("""{
  "source_url": "https://example.com",
  "pages_scraped": 5,
  "scenario": {
    "suggested_question": "What services do you offer?",
    "initial_answer": "We offer web development...",
    "followup_question": "Tell me more about your team",
    "detailed_answer": "Our team consists of..."
  },
  "cleaned_pages": [...]
}""")
print()

print("="*60)
print("REQUIREMENTS")
print("="*60)
print()
print("✓ Python 3.7+")
print("✓ OpenAI API key (set as environment variable)")
print("✓ Internet connection")
print("✓ Dependencies from requirements.txt")
print()

# Check if API key is set
if os.environ.get('OPENAI_API_KEY'):
    print("✓ OPENAI_API_KEY is set")
else:
    print("✗ OPENAI_API_KEY is not set")
    print("  Set it with: export OPENAI_API_KEY='your-key'")
print()
