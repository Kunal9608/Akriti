/**
 * AKRITI — Toast Notification System
 * Replaces all native alert() calls. No emoji.
 * Usage: Toast.show('Message', 'success' | 'error' | 'warning' | 'info')
 */

const Toast = (() => {
  let container = null;

  function ensureContainer() {
    if (!container) {
      container = document.getElementById('toast-container');
      if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
      }
    }
    return container;
  }

  const ICONS = {
    success: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
    error:   `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
    warning: `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    info:    `<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
  };

  function show(message, type = 'info', duration = 3500) {
    // Prevent [object Object] displaying in toast
    if (typeof message === 'object' && message !== null) {
      if (Array.isArray(message)) {
        message = message.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
      } else {
        message = message.message || message.detail || JSON.stringify(message);
      }
    }

    const c = ensureContainer();
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      ${ICONS[type] || ICONS.info}
      <span class="toast-message">${message}</span>
      <button class="toast-close" aria-label="Dismiss">&times;</button>
    `;

    c.appendChild(toast);

    const dismiss = () => {
      toast.classList.add('out');
      toast.addEventListener('animationend', () => toast.remove(), { once: true });
    };

    toast.querySelector('.toast-close').addEventListener('click', dismiss);

    const timer = duration > 0 ? setTimeout(dismiss, duration) : null;

    // Clear timer if manually dismissed
    toast.querySelector('.toast-close').addEventListener('click', () => {
      if (timer) clearTimeout(timer);
    }, { once: true });

    return { dismiss };
  }

  return { show };
})();

// Make globally available
window.Toast = Toast;
