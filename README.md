# Chatbot Demo Maker

Automatically scrapes website content and creates chatbot demo scenarios using OpenAI API.

## Features

- 🕷️ **Website Scraping**: Automatically crawls and scrapes all pages from a given URL
- 🧹 **Text Cleaning**: Uses OpenAI API to clean and format extracted text
- 🤖 **Scenario Generation**: Creates realistic chatbot demo scenarios with:
  - A suggested question (clickable prompt)
  - An initial answer
  - A followup question
  - A detailed answer

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ayergoo/chatbot-demo-maker.git
cd chatbot-demo-maker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Usage

### Command Line

Run the script with a URL as an argument:
```bash
python chatbot_demo_maker.py https://example.com
```

Or run without arguments to be prompted for a URL:
```bash
python chatbot_demo_maker.py
```

### Example Output

The script will:
1. Scrape all pages from the provided website (up to 50 pages)
2. Clean each page's text using OpenAI API
3. Combine all cleaned text
4. Generate a chatbot demo scenario

Results are saved to `chatbot_scenario.json` and displayed in the console:

```
Suggested Question (clickable):
  → What services does your company offer?

Initial Answer:
  We provide comprehensive web development and AI solutions...

User Followup Question:
  → Can you tell me more about your AI capabilities?

Detailed Answer:
  Our AI services include natural language processing...
```

## Output Format

The script generates a JSON file (`chatbot_scenario.json`) with the following structure:

```json
{
  "source_url": "https://example.com",
  "pages_scraped": 15,
  "scenario": {
    "suggested_question": "...",
    "initial_answer": "...",
    "followup_question": "...",
    "detailed_answer": "..."
  },
  "cleaned_pages": [
    {
      "url": "https://example.com/page1",
      "cleaned_text": "..."
    }
  ]
}
```

## Configuration

You can modify these parameters in the code:

- `max_pages`: Maximum number of pages to scrape (default: 50)
- `model`: OpenAI model to use (default: "gpt-3.5-turbo")
- `temperature`: Creativity level for responses (default: 0.3 for cleaning, 0.7 for scenarios)

## Requirements

- Python 3.7+
- OpenAI API key
- Internet connection

## License

MIT License

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.