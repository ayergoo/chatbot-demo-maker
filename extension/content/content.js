/**
 * Chatbot Demo Widget - Content Script
 * Injects and controls the chatbot widget on web pages
 */

// Default configuration
const DEFAULT_CONFIG = {
  colors: {
    primary: "#007bff",
    secondary: "#6c757d",
    botMessage: "#e9ecef",
    userMessage: "#007bff",
    textPrimary: "#ffffff",
    textSecondary: "#000000"
  },
  font: {
    family: "Arial, sans-serif",
    size: "14px"
  },
  scenario: {
    suggestedQuestion: "How can I help you today?",
    responses: [
      {
        trigger: "How can I help you today?",
        answer: "I'm here to assist you! You can ask me about our services, pricing, or any other questions you might have."
      },
      {
        trigger: "pricing",
        answer: "Our pricing is flexible and depends on your specific needs. Contact us for a custom quote!"
      },
      {
        trigger: "services",
        answer: "We offer web development, AI solutions, and chatbot integration services."
      }
    ],
    defaultResponse: "Thank you for your question! This is a demo chatbot. In a live version, I would provide detailed answers to your queries."
  },
  enabled: true
};

class ChatbotWidget {
  constructor(config) {
    this.config = config;
    this.isOpen = false;
    this.messages = [];
    this.widgetContainer = null;
    this.init();
  }

  init() {
    if (!this.config.enabled) {
      return;
    }
    this.createWidget();
    this.attachEventListeners();
    this.applyCustomStyles();
  }

  createWidget() {
    // Create main container
    this.widgetContainer = document.createElement('div');
    this.widgetContainer.id = 'chatbot-demo-widget';
    this.widgetContainer.innerHTML = `
      <!-- Chat Icon Button -->
      <div id="chatbot-icon" class="chatbot-icon">
        <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
          <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
        </svg>
      </div>

      <!-- Suggested Question Bubble -->
      <div id="chatbot-suggestion-bubble" class="chatbot-suggestion-bubble">
        <div class="suggestion-text">${this.config.scenario.suggestedQuestion}</div>
        <button class="bubble-close" aria-label="Close suggestion">&times;</button>
      </div>

      <!-- Chat Window -->
      <div id="chatbot-window" class="chatbot-window">
        <div class="chatbot-header">
          <div class="header-title">
            <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
              <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
            </svg>
            <span>Chat Support</span>
          </div>
          <button id="chatbot-close" class="header-close" aria-label="Close chat">&times;</button>
        </div>
        <div id="chatbot-messages" class="chatbot-messages">
          <div class="bot-message">
            <div class="message-bubble">Hello! ${this.config.scenario.suggestedQuestion}</div>
          </div>
        </div>
        <div class="chatbot-input-area">
          <input 
            type="text" 
            id="chatbot-input" 
            class="chatbot-input" 
            placeholder="Type your message..."
            aria-label="Chat input"
          />
          <button id="chatbot-send" class="chatbot-send-btn" aria-label="Send message">
            <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
        <div id="chatbot-typing" class="chatbot-typing" style="display: none;">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    `;

    document.body.appendChild(this.widgetContainer);
  }

  attachEventListeners() {
    const icon = document.getElementById('chatbot-icon');
    const closeBtn = document.getElementById('chatbot-close');
    const sendBtn = document.getElementById('chatbot-send');
    const input = document.getElementById('chatbot-input');
    const suggestionBubble = document.getElementById('chatbot-suggestion-bubble');
    const bubbleClose = suggestionBubble.querySelector('.bubble-close');
    const suggestionText = suggestionBubble.querySelector('.suggestion-text');

    // Toggle chat window
    icon.addEventListener('click', () => this.toggleChat());

    // Close chat
    closeBtn.addEventListener('click', () => this.toggleChat());

    // Send message
    sendBtn.addEventListener('click', () => this.handleSendMessage());

    // Enter key to send
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.handleSendMessage();
      }
    });

    // Click suggested question
    suggestionText.addEventListener('click', () => {
      this.handleSuggestedQuestion();
    });

    // Close suggestion bubble
    bubbleClose.addEventListener('click', (e) => {
      e.stopPropagation();
      suggestionBubble.style.display = 'none';
    });
  }

  toggleChat() {
    const window = document.getElementById('chatbot-window');
    const icon = document.getElementById('chatbot-icon');
    const bubble = document.getElementById('chatbot-suggestion-bubble');

    this.isOpen = !this.isOpen;

    if (this.isOpen) {
      window.classList.add('open');
      icon.classList.add('hidden');
      bubble.style.display = 'none';
      
      // Auto-focus input
      setTimeout(() => {
        document.getElementById('chatbot-input').focus();
      }, 300);
    } else {
      window.classList.remove('open');
      icon.classList.remove('hidden');
      if (this.messages.length === 0) {
        bubble.style.display = 'block';
      }
    }
  }

  handleSuggestedQuestion() {
    const input = document.getElementById('chatbot-input');
    input.value = this.config.scenario.suggestedQuestion;
    
    // Hide bubble and open chat
    document.getElementById('chatbot-suggestion-bubble').style.display = 'none';
    if (!this.isOpen) {
      this.toggleChat();
    }
    
    // Send the message
    setTimeout(() => {
      this.handleSendMessage();
    }, 300);
  }

  handleSendMessage() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    this.addMessage(message, 'user');
    input.value = '';

    // Show typing indicator
    this.showTypingIndicator();

    // Simulate bot response delay
    setTimeout(() => {
      const response = this.getResponse(message);
      this.hideTypingIndicator();
      this.addMessage(response, 'bot');
    }, 800);
  }

  getResponse(userMessage) {
    const lowerMessage = userMessage.toLowerCase();
    
    // Check for exact match or keyword match
    for (const responseObj of this.config.scenario.responses) {
      const trigger = responseObj.trigger.toLowerCase();
      
      // Exact match
      if (lowerMessage === trigger) {
        return responseObj.answer;
      }
      
      // Keyword match
      if (lowerMessage.includes(trigger) || trigger.includes(lowerMessage)) {
        return responseObj.answer;
      }
    }

    return this.config.scenario.defaultResponse;
  }

  addMessage(text, sender) {
    const messagesContainer = document.getElementById('chatbot-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `${sender}-message`;
    
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    bubbleDiv.textContent = text;
    
    messageDiv.appendChild(bubbleDiv);
    messagesContainer.appendChild(messageDiv);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    this.messages.push({ text, sender, timestamp: Date.now() });
  }

  showTypingIndicator() {
    const typing = document.getElementById('chatbot-typing');
    typing.style.display = 'flex';
    
    const messagesContainer = document.getElementById('chatbot-messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  hideTypingIndicator() {
    const typing = document.getElementById('chatbot-typing');
    typing.style.display = 'none';
  }

  applyCustomStyles() {
    const root = document.documentElement;
    const colors = this.config.colors;
    const font = this.config.font;

    root.style.setProperty('--chatbot-primary-color', colors.primary);
    root.style.setProperty('--chatbot-secondary-color', colors.secondary);
    root.style.setProperty('--chatbot-bot-message-color', colors.botMessage);
    root.style.setProperty('--chatbot-user-message-color', colors.userMessage);
    root.style.setProperty('--chatbot-text-primary-color', colors.textPrimary);
    root.style.setProperty('--chatbot-text-secondary-color', colors.textSecondary);
    root.style.setProperty('--chatbot-font-family', font.family);
    root.style.setProperty('--chatbot-font-size', font.size);
  }
}

// Initialize widget when DOM is ready
function initWidget() {
  // Load configuration from storage
  chrome.storage.sync.get(['chatbotConfig'], (result) => {
    const config = result.chatbotConfig || DEFAULT_CONFIG;
    
    // Merge with defaults to ensure all properties exist
    const mergedConfig = {
      ...DEFAULT_CONFIG,
      ...config,
      colors: { ...DEFAULT_CONFIG.colors, ...(config.colors || {}) },
      font: { ...DEFAULT_CONFIG.font, ...(config.font || {}) },
      scenario: { ...DEFAULT_CONFIG.scenario, ...(config.scenario || {}) }
    };

    // Create widget
    new ChatbotWidget(mergedConfig);
  });
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initWidget);
} else {
  initWidget();
}
