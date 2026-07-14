/**
 * AKRITI — Modal Component
 * Replaces all native confirm()/prompt() calls. Focus-trapped, Esc-to-close.
 * Usage:
 *   Modal.confirm('Title', 'Message') → Promise<boolean>
 *   Modal.open('modal-id')
 *   Modal.close('modal-id')
 */

const Modal = (() => {
  let activeModal = null;
  let focusableEls = [];
  let firstFocusable = null;
  let lastFocusable = null;

  const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

  function trapFocus(e) {
    if (!activeModal) return;
    if (e.key !== 'Tab') return;
    if (focusableEls.length === 0) return;

    if (e.shiftKey) {
      if (document.activeElement === firstFocusable) {
        e.preventDefault();
        lastFocusable.focus();
      }
    } else {
      if (document.activeElement === lastFocusable) {
        e.preventDefault();
        firstFocusable.focus();
      }
    }
  }

  function handleKeydown(e) {
    if (e.key === 'Escape' && activeModal) {
      close(activeModal.id);
    }
    trapFocus(e);
  }

  function open(modalId) {
    const backdrop = document.getElementById(modalId);
    if (!backdrop) return;

    backdrop.classList.add('open');
    backdrop.style.display = 'flex';
    activeModal = backdrop;

    focusableEls = Array.from(backdrop.querySelectorAll(FOCUSABLE));
    firstFocusable = focusableEls[0];
    lastFocusable = focusableEls[focusableEls.length - 1];

    if (firstFocusable) firstFocusable.focus();

    document.addEventListener('keydown', handleKeydown);

    // Backdrop click to close (only if clicking the backdrop itself)
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) close(modalId);
    }, { once: true });
  }

  function close(modalId) {
    const backdrop = document.getElementById(modalId);
    if (!backdrop) return;
    backdrop.classList.remove('open');
    backdrop.style.display = '';
    document.removeEventListener('keydown', handleKeydown);
    activeModal = null;
  }

  function confirm(title, message, { confirmText = 'Confirm', cancelText = 'Cancel', danger = false, onConfirm = null } = {}) {
    return new Promise((resolve) => {
      // Remove any existing confirm modal
      const existing = document.getElementById('_confirm-modal');
      if (existing) existing.remove();

      const backdrop = document.createElement('div');
      backdrop.id = '_confirm-modal';
      backdrop.className = 'modal-backdrop';
      backdrop.innerHTML = `
        <div class="modal modal-sm" role="dialog" aria-modal="true" aria-labelledby="_confirm-title">
          <div class="modal-header">
            <h2 class="modal-title" id="_confirm-title">${title}</h2>
            <button class="modal-close" id="_confirm-cancel-x" aria-label="Close">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <div class="modal-body">
            <p style="color: var(--color-ink-muted); font-size: var(--text-base); line-height: 1.6;">${message}</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-ghost" id="_confirm-cancel">${cancelText}</button>
            <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" id="_confirm-ok">${confirmText}</button>
          </div>
        </div>
      `;

      document.body.appendChild(backdrop);
      open('_confirm-modal');

      function done(result) {
        close('_confirm-modal');
        backdrop.remove();
        resolve(result);
      }

      const okBtn = backdrop.querySelector('#_confirm-ok');
      const cancelBtn = backdrop.querySelector('#_confirm-cancel');
      const cancelX = backdrop.querySelector('#_confirm-cancel-x');

      async function handleOk() {
        if (onConfirm) {
          okBtn.setAttribute('aria-busy', 'true');
          okBtn.innerHTML = `<span class="btn-loading-spinner"></span>`;
          okBtn.disabled = true;
          if (cancelBtn) cancelBtn.disabled = true;
          if (cancelX) cancelX.disabled = true;
          try {
            await onConfirm();
          } catch (_) {
            okBtn.removeAttribute('aria-busy');
            okBtn.innerHTML = confirmText;
            okBtn.disabled = false;
            if (cancelBtn) cancelBtn.disabled = false;
            if (cancelX) cancelX.disabled = false;
            return;
          }
        }
        done(true);
      }

      okBtn.addEventListener('click', handleOk);
      cancelBtn.addEventListener('click', () => done(false));
      cancelX.addEventListener('click', () => done(false));
    });
  }

  return { open, close, confirm };
})();

window.Modal = Modal;
