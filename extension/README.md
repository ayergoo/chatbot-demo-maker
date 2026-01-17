# Chatbot Demo Widget - Chrome Extension

A customizable chatbot widget Chrome extension for demonstration and advertising purposes. Display an interactive chatbot on any web page to showcase your chatbot capabilities.

## Features

- 🎨 **Fully Customizable**: Configure colors, fonts, and styling
- 💬 **Interactive Chat Widget**: Professional chat interface with smooth animations
- 📝 **Scenario-Based Responses**: Pre-configure Q&A pairs for demo purposes
- 🔧 **Easy Configuration**: User-friendly settings page
- 🚀 **Lightweight**: No external dependencies, pure vanilla JavaScript
- 📱 **Responsive**: Works on all screen sizes

## Installation

### Method 1: Load as Unpacked Extension (Development)

1. Clone or download this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top right corner
4. Click "Load unpacked"
5. Select the `extension` folder from this project
6. The extension is now installed and active!

### Method 2: Install from Chrome Web Store (Coming Soon)

Once published, you'll be able to install directly from the Chrome Web Store.

## Usage

### Basic Usage

1. After installation, the chatbot widget will appear on all web pages
2. Click the chat icon in the bottom-right corner to open the chat window
3. Click the suggested question bubble or type your own message
4. The bot will respond based on your configured scenarios

### Customization

1. Click the extension icon in Chrome toolbar
2. Click "Open Settings" to access the configuration page
3. Customize the following:
   - **Colors**: Primary, secondary, message bubbles, and text colors
   - **Font**: Font family and size
   - **Scenarios**: Suggested question and response triggers/answers
   - **Enable/Disable**: Turn the widget on or off

### Configuration Options

#### Colors
- **Primary Color**: Icon and header background
- **Secondary Color**: Secondary elements
- **Bot Message Color**: Background for bot message bubbles
- **User Message Color**: Background for user message bubbles
- **Primary Text Color**: Text on primary colored elements
- **Secondary Text Color**: Text on secondary colored elements

#### Font
- **Font Family**: Choose from preset fonts or use custom font stack
- **Font Size**: Adjust text size (12px - 18px)

#### Demo Scenarios
- **Suggested Question**: The initial prompt shown in the bubble
- **Response Triggers**: Keywords or phrases that trigger specific responses
- **Answers**: The responses shown when triggers match
- **Default Response**: Fallback response when no trigger matches

## Default Configuration

```json
{
  "colors": {
    "primary": "#007bff",
    "secondary": "#6c757d",
    "botMessage": "#e9ecef",
    "userMessage": "#007bff",
    "textPrimary": "#ffffff",
    "textSecondary": "#000000"
  },
  "font": {
    "family": "Arial, sans-serif",
    "size": "14px"
  },
  "scenario": {
    "suggestedQuestion": "How can I help you today?",
    "responses": [
      {
        "trigger": "How can I help you today?",
        "answer": "I'm here to assist you! You can ask me about our services, pricing, or any other questions you might have."
      },
      {
        "trigger": "pricing",
        "answer": "Our pricing is flexible and depends on your specific needs. Contact us for a custom quote!"
      },
      {
        "trigger": "services",
        "answer": "We offer web development, AI solutions, and chatbot integration services."
      }
    ],
    "defaultResponse": "Thank you for your question! This is a demo chatbot. In a live version, I would provide detailed answers to your queries."
  }
}
```

## File Structure

```
extension/
├── manifest.json           # Extension configuration
├── icons/                  # Extension icons
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
├── content/                # Content scripts (injected into pages)
│   ├── content.js         # Main widget logic
│   └── widget.css         # Widget styles
├── options/                # Settings page
│   ├── options.html
│   ├── options.js
│   └── options.css
├── popup/                  # Extension popup
│   ├── popup.html
│   ├── popup.js
│   └── popup.css
└── README.md              # This file
```

## Technical Details

- **Manifest Version**: V3
- **Permissions**: `storage`, `activeTab`
- **Storage**: Uses `chrome.storage.sync` for cross-device syncing
- **Injection**: Content script runs on all URLs at document_idle
- **Framework**: Vanilla JavaScript (no external dependencies)

## Response Matching

The extension uses simple pattern matching for responses:

1. **Exact Match**: Checks if user message exactly matches trigger phrase
2. **Keyword Match**: Checks if message contains trigger keyword
3. **Default Response**: Returns default if no match found

All matching is case-insensitive.

## Browser Compatibility

- Chrome 88+
- Edge 88+ (Chromium-based)
- Brave
- Opera

## Development

### Prerequisites
- Google Chrome browser
- Basic knowledge of HTML, CSS, and JavaScript

### Testing Locally

1. Make changes to the extension files
2. Go to `chrome://extensions/`
3. Click the refresh icon on the extension card
4. Test your changes on any web page

### Debugging

- Use Chrome DevTools to debug the content script
- Right-click the extension popup → "Inspect" to debug popup
- Right-click on options page → "Inspect" to debug settings

## Privacy

This extension:
- Does NOT collect any personal data
- Does NOT track user behavior
- Does NOT send data to external servers
- Only stores user preferences locally in Chrome storage

## Support

For issues, questions, or feature requests, please visit the main project repository:
https://github.com/ayergoo/chatbot-demo-maker

## License

MIT License - See main project LICENSE for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Future Enhancements

- [ ] Import scenarios from `chatbot_scenario.json` files
- [ ] Multiple preset themes
- [ ] Position customization (left/right, top/bottom)
- [ ] Typing speed customization
- [ ] Multi-language support
- [ ] Sound effects toggle
- [ ] Chat history persistence
- [ ] Export/import configuration

## Credits

Part of the Chatbot Demo Maker project by ayergoo.
