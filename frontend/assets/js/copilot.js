/**
 * PathLab AI Copilot
 */
const Copilot = (() => {
  let isInit = false;

  const COPILOT_ICON = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path><path d="M9 9h6"></path><path d="M9 13h6"></path></svg>`;

  function initUI() {
    if (isInit) return;
    
    // Replace Theme Toggle with Copilot Toggle
    document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
      btn.removeAttribute('data-theme-toggle');
      btn.setAttribute('data-copilot-toggle', 'true');
      btn.setAttribute('aria-label', 'Open AI Copilot');
      btn.innerHTML = COPILOT_ICON;
      
      // Remove old theme click listeners (cloning removes listeners)
      const newBtn = btn.cloneNode(true);
      btn.parentNode.replaceChild(newBtn, btn);
      
      newBtn.addEventListener('click', toggleDrawer);
    });

    // Inject CSS
    if (!document.getElementById('copilot-css')) {
      const link = document.createElement('link');
      link.id = 'copilot-css';
      link.rel = 'stylesheet';
      link.href = '/assets/css/copilot.css';
      document.head.appendChild(link);
    }

    // Inject Drawer HTML
    const drawerHtml = `
      <div class="copilot-overlay" id="copilot-overlay"></div>
      <div class="copilot-drawer" id="copilot-drawer">
        <div class="copilot-header">
          <div class="copilot-brand">
            ${COPILOT_ICON} PathLab AI
          </div>
          <button class="copilot-close" id="copilot-close" aria-label="Close AI">&times;</button>
        </div>
        <div class="copilot-body" id="copilot-messages">
          <div class="copilot-msg system">
            Hi ${window._me?.name || 'there'}! I'm your PathLab AI assistant. How can I help you today?
          </div>
        </div>
        <div class="copilot-footer">
          <textarea id="copilot-input" placeholder="Ask PathLab AI..." rows="1"></textarea>
          <button id="copilot-send">${COPILOT_ICON}</button>
        </div>
      </div>
    `;
    
    const wrapper = document.createElement('div');
    wrapper.innerHTML = drawerHtml;
    document.body.appendChild(wrapper);

    // Bind Drawer Events
    document.getElementById('copilot-close').addEventListener('click', closeDrawer);
    document.getElementById('copilot-overlay').addEventListener('click', closeDrawer);
    
    const input = document.getElementById('copilot-input');
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    
    document.getElementById('copilot-send').addEventListener('click', sendMessage);

    isInit = true;
  }

  function toggleDrawer() {
    document.getElementById('copilot-drawer').classList.add('open');
    document.getElementById('copilot-overlay').classList.add('open');
  }

  function closeDrawer() {
    document.getElementById('copilot-drawer').classList.remove('open');
    document.getElementById('copilot-overlay').classList.remove('open');
  }

  function appendMessage(role, text) {
    const container = document.getElementById('copilot-messages');
    const msg = document.createElement('div');
    msg.className = `copilot-msg ${role}`;
    msg.textContent = text; // basic text for now
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
  }

  async function sendMessage() {
    const input = document.getElementById('copilot-input');
    const text = input.value.trim();
    if (!text) return;
    
    appendMessage('user', text);
    input.value = '';
    
    // Create an empty system message to stream into
    const container = document.getElementById('copilot-messages');
    const msg = document.createElement('div');
    msg.className = 'copilot-msg system';
    msg.textContent = 'Processing request...';
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
    
    try {
      const token = localStorage.getItem('akriti_token') || '';
      const response = await fetch('/api/v1/copilot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: text })
      });
      
      if (!response.ok) {
        msg.textContent = 'Error connecting to AI Copilot.';
        return;
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let isFirstChunk = true;
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') break;
            
            if (isFirstChunk) {
               msg.textContent = '';
               isFirstChunk = false;
            }
            
            let textToAppend = data;
            try {
              textToAppend = JSON.parse(data);
            } catch(e) {
              // Fallback to raw text if parsing fails
            }
            
            msg.textContent += textToAppend;
            container.scrollTop = container.scrollHeight;
          }
        }
      }
    } catch (err) {
      console.error(err);
      msg.textContent = 'Error connecting to AI Copilot.';
    }
  }

  return { init: initUI, toggle: toggleDrawer, close: closeDrawer };
})();

window.Copilot = Copilot;
