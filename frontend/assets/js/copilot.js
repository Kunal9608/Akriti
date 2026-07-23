/**
 * PathLab AI Copilot
 */
const Copilot = (() => {
  let isInit = false;

  function formatMarkdown(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code style="background:rgba(0,0,0,0.08);padding:2px 6px;border-radius:4px;font-family:monospace;font-weight:700;">$1</code>');
  }

  const COPILOT_ICON = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path><path d="M9 9h6"></path><path d="M9 13h6"></path></svg>`;
  const SEND_ICON = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>`;

  function initUI() {
    if (isInit) return;
    
    // Inject Copilot Toggle into Topbar
    const topbar = document.querySelector('.topbar');
    if (topbar) {
      let topbarRight = topbar.querySelector('.topbar-right');
      if (!topbarRight) {
        topbarRight = document.createElement('div');
        topbarRight.className = 'topbar-right';
        topbarRight.style.marginLeft = 'auto'; // Ensure it floats right
        topbar.appendChild(topbarRight);
      }
      const copilotBtn = document.createElement('button');
      copilotBtn.className = 'ask-ai-badge';
      copilotBtn.setAttribute('aria-label', 'Open AI Copilot');
      copilotBtn.innerHTML = `Ask AI ✨`;
      copilotBtn.addEventListener('click', toggleDrawer);
      topbarRight.appendChild(copilotBtn);
    }

    // Inject CSS
    if (!document.getElementById('copilot-css')) {
      const link = document.createElement('link');
      link.id = 'copilot-css';
      link.rel = 'stylesheet';
      link.href = '/assets/css/copilot.css?v=' + Date.now();
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
          <textarea id="copilot-input" placeholder="Ask PathLab AI..." rows="1" enterkeyhint="send" style="resize: none; overflow: hidden;"></textarea>
          <button id="copilot-send" aria-label="Send message">${SEND_ICON}</button>
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
    msg.textContent = text;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
    return msg;
  }

  async function sendMessage() {
    const input = document.getElementById('copilot-input');
    const sendBtn = document.getElementById('copilot-send');
    const text = input.value.trim();
    if (!text) return;
    
    input.disabled = true;
    sendBtn.disabled = true;

    appendMessage('user', text);
    input.value = '';
    input.style.height = 'auto';

    const msg = appendMessage('system', 'Thinking');
    let dotCount = 0;
    const loadingInterval = setInterval(() => {
      dotCount = (dotCount + 1) % 4;
      msg.textContent = 'Thinking' + '.'.repeat(dotCount);
    }, 400);

    let isFirstChunk = true;
    let rawText = '';
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
        clearInterval(loadingInterval);
        msg.textContent = 'Error connecting to AI Copilot.';
        return;
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
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
               clearInterval(loadingInterval);
               msg.innerHTML = '';
               isFirstChunk = false;
            }
            
            let textToAppend = data;
            try {
              textToAppend = JSON.parse(data);
            } catch(e) {
              // Fallback to raw text if parsing fails
            }
            
            rawText += textToAppend;
            msg.innerHTML = formatMarkdown(rawText);
            const container = document.getElementById('copilot-messages');
            container.scrollTop = container.scrollHeight;
          }
        }
      }
    } catch (err) {
      clearInterval(loadingInterval);
      console.error(err);
      if (isFirstChunk) msg.textContent = 'Error connecting to AI Copilot.';
    } finally {
      input.disabled = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  return { init: initUI, toggle: toggleDrawer, close: closeDrawer };
})();

window.Copilot = Copilot;
