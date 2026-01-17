/**
 * Chatbot Demo Widget - Popup Script
 */

// Load current status
function loadStatus() {
  chrome.storage.sync.get(['chatbotConfig'], (result) => {
    const config = result.chatbotConfig || { enabled: true };
    const enabled = config.enabled !== false;
    
    const toggleCheckbox = document.getElementById('toggleWidget');
    const statusBadge = document.getElementById('widgetStatus');
    
    toggleCheckbox.checked = enabled;
    updateStatusBadge(enabled);
  });
}

// Update status badge
function updateStatusBadge(enabled) {
  const statusBadge = document.getElementById('widgetStatus');
  statusBadge.textContent = enabled ? 'Active' : 'Disabled';
  statusBadge.className = enabled ? 'status-badge active' : 'status-badge inactive';
}

// Toggle widget
function toggleWidget(enabled) {
  chrome.storage.sync.get(['chatbotConfig'], (result) => {
    const config = result.chatbotConfig || {};
    config.enabled = enabled;
    
    chrome.storage.sync.set({ chatbotConfig: config }, () => {
      updateStatusBadge(enabled);
      
      // Reload all tabs to apply changes
      chrome.tabs.query({}, (tabs) => {
        tabs.forEach(tab => {
          if (tab.url && !tab.url.startsWith('chrome://') && !tab.url.startsWith('chrome-extension://')) {
            chrome.tabs.reload(tab.id);
          }
        });
      });
    });
  });
}

// Open settings page
function openSettings() {
  chrome.runtime.openOptionsPage();
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadStatus();
  
  // Toggle widget
  document.getElementById('toggleWidget').addEventListener('change', (e) => {
    toggleWidget(e.target.checked);
  });
  
  // Open settings
  document.getElementById('openSettings').addEventListener('click', openSettings);
});
