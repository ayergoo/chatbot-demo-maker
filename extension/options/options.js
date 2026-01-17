/**
 * Chatbot Demo Widget - Options Page Script
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

let currentConfig = { ...DEFAULT_CONFIG };

// Load saved settings
function loadSettings() {
  chrome.storage.sync.get(['chatbotConfig'], (result) => {
    if (result.chatbotConfig) {
      currentConfig = {
        ...DEFAULT_CONFIG,
        ...result.chatbotConfig,
        colors: { ...DEFAULT_CONFIG.colors, ...(result.chatbotConfig.colors || {}) },
        font: { ...DEFAULT_CONFIG.font, ...(result.chatbotConfig.font || {}) },
        scenario: { 
          ...DEFAULT_CONFIG.scenario, 
          ...(result.chatbotConfig.scenario || {}),
          responses: result.chatbotConfig.scenario?.responses || DEFAULT_CONFIG.scenario.responses
        }
      };
    }
    populateForm();
  });
}

// Populate form with current settings
function populateForm() {
  // General
  document.getElementById('enabled').checked = currentConfig.enabled;

  // Colors
  document.getElementById('primaryColor').value = currentConfig.colors.primary;
  document.getElementById('secondaryColor').value = currentConfig.colors.secondary;
  document.getElementById('botMessageColor').value = currentConfig.colors.botMessage;
  document.getElementById('userMessageColor').value = currentConfig.colors.userMessage;
  document.getElementById('textPrimaryColor').value = currentConfig.colors.textPrimary;
  document.getElementById('textSecondaryColor').value = currentConfig.colors.textSecondary;

  // Font
  document.getElementById('fontFamily').value = currentConfig.font.family;
  document.getElementById('fontSize').value = currentConfig.font.size;

  // Scenario
  document.getElementById('suggestedQuestion').value = currentConfig.scenario.suggestedQuestion;
  document.getElementById('defaultResponse').value = currentConfig.scenario.defaultResponse;

  // Responses
  renderResponses();
}

// Render response items
function renderResponses() {
  const container = document.getElementById('responsesContainer');
  container.innerHTML = '';

  currentConfig.scenario.responses.forEach((response, index) => {
    const responseItem = createResponseItem(response, index);
    container.appendChild(responseItem);
  });
}

// Create a response item element
function createResponseItem(response, index) {
  const div = document.createElement('div');
  div.className = 'response-item';
  div.innerHTML = `
    <div class="response-fields">
      <div class="field-group">
        <label>Trigger Phrase</label>
        <input type="text" class="text-input response-trigger" 
               data-index="${index}" 
               value="${response.trigger}" 
               placeholder="e.g., pricing">
      </div>
      <div class="field-group">
        <label>Answer</label>
        <textarea class="text-input response-answer" 
                  data-index="${index}" 
                  rows="2" 
                  placeholder="The response to show">${response.answer}</textarea>
      </div>
    </div>
    <button type="button" class="btn-remove" data-index="${index}">Remove</button>
  `;

  // Attach event listeners
  const triggerInput = div.querySelector('.response-trigger');
  const answerInput = div.querySelector('.response-answer');
  const removeBtn = div.querySelector('.btn-remove');

  triggerInput.addEventListener('input', (e) => {
    currentConfig.scenario.responses[index].trigger = e.target.value;
  });

  answerInput.addEventListener('input', (e) => {
    currentConfig.scenario.responses[index].answer = e.target.value;
  });

  removeBtn.addEventListener('click', () => {
    currentConfig.scenario.responses.splice(index, 1);
    renderResponses();
  });

  return div;
}

// Add new response
function addResponse() {
  currentConfig.scenario.responses.push({
    trigger: "",
    answer: ""
  });
  renderResponses();
}

// Save settings
function saveSettings() {
  // Update config from form
  currentConfig.enabled = document.getElementById('enabled').checked;
  
  currentConfig.colors.primary = document.getElementById('primaryColor').value;
  currentConfig.colors.secondary = document.getElementById('secondaryColor').value;
  currentConfig.colors.botMessage = document.getElementById('botMessageColor').value;
  currentConfig.colors.userMessage = document.getElementById('userMessageColor').value;
  currentConfig.colors.textPrimary = document.getElementById('textPrimaryColor').value;
  currentConfig.colors.textSecondary = document.getElementById('textSecondaryColor').value;

  currentConfig.font.family = document.getElementById('fontFamily').value;
  currentConfig.font.size = document.getElementById('fontSize').value;

  currentConfig.scenario.suggestedQuestion = document.getElementById('suggestedQuestion').value;
  currentConfig.scenario.defaultResponse = document.getElementById('defaultResponse').value;

  // Save to storage
  chrome.storage.sync.set({ chatbotConfig: currentConfig }, () => {
    showStatus('Settings saved successfully!', 'success');
  });
}

// Reset to defaults
function resetSettings() {
  if (confirm('Are you sure you want to reset all settings to defaults?')) {
    currentConfig = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
    populateForm();
    saveSettings();
    showStatus('Settings reset to defaults', 'success');
  }
}

// Show status message
function showStatus(message, type = 'success') {
  const statusEl = document.getElementById('statusMessage');
  statusEl.textContent = message;
  statusEl.className = `status-message ${type}`;
  statusEl.style.display = 'block';

  setTimeout(() => {
    statusEl.style.display = 'none';
  }, 3000);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();

  // Attach event listeners
  document.getElementById('saveSettings').addEventListener('click', saveSettings);
  document.getElementById('resetSettings').addEventListener('click', resetSettings);
  document.getElementById('addResponse').addEventListener('click', addResponse);
});
