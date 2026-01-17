# Chatbot Demo Maker

Automatically scrapes website content and creates chatbot demo scenarios using OpenAI API. Also includes a Chrome extension to showcase your chatbot demos on any web page!

## Features

### Python Script
- 🕷️ **Website Scraping**: Automatically crawls and scrapes all pages from a given URL
- 🧹 **Text Cleaning**: Uses OpenAI API to clean and format extracted text
- 🤖 **Scenario Generation**: Creates realistic chatbot demo scenarios with:
  - A suggested question (clickable prompt)
  - An initial answer
  - A followup question
  - A detailed answer

### Chrome Extension
- 💬 **Interactive Widget**: Display a customizable chatbot widget on any web page
- 🎨 **Full Customization**: Configure colors, fonts, and demo scenarios
- 📱 **Responsive Design**: Works seamlessly on all screen sizes
- ⚡ **Lightweight**: Pure vanilla JavaScript with no external dependencies

## Installation

### Python Script

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

### Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" in the top right corner
3. Click "Load unpacked"
4. Select the `extension` folder from this project
5. The extension is now installed and ready to use!

See [extension/README.md](extension/README.md) for detailed instructions and customization options.

## Usage

### Python Script - Command Line

Run the script with a URL as an argument:
```bash
python chatbot_demo_maker.py https://example.com
```

Or run without arguments to be prompted for a URL:
```bash
python chatbot_demo_maker.py
```

### Chrome Extension

1. Click the extension icon in the Chrome toolbar to enable/disable the widget
2. The chatbot widget appears in the bottom-right corner of every web page
3. Click the chat icon to open the chat window
4. Click "Open Settings" to customize colors, fonts, and demo scenarios

For detailed usage instructions, see [extension/README.md](extension/README.md).

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

### Python Script
- Python 3.7+
- OpenAI API key
- Internet connection

### Chrome Extension
- Chrome 88+ or any Chromium-based browser (Edge, Brave, Opera)
- No external dependencies required

## Project Structure

```
chatbot-demo-maker/
├── scenario_maker/          # Python web scraping and scenario generation
│   ├── chatbot_demo_maker.py
│   └── test_chatbot_demo_maker.py
├── extension/               # Chrome extension for widget display
│   ├── manifest.json
│   ├── icons/
│   ├── content/            # Widget injected into pages
│   ├── options/            # Settings page
│   ├── popup/              # Extension popup
│   └── README.md
├── requirements.txt
└── README.md
```

## License

MIT License

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.