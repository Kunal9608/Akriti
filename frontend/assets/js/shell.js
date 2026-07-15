/**
 * AKRITI — Shared Shell Utilities
 * Injects the sidebar + topbar into any authenticated page.
 * Also handles: logout, current user display, active nav highlighting,
 * mobile hamburger, and role-gating.
 */

// Global helper functions
if (typeof window.escapeHtml === 'undefined') {
  window.escapeHtml = function(str) {
    if (!str) return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  };
}
if (typeof window.formatCurrency === 'undefined') {
  window.formatCurrency = function(n) {
    if (n == null) return '—';
    return '₹' + Number(n).toLocaleString('en-IN', { minimumFractionDigits: 0 });
  };
}
if (typeof window.formatDate === 'undefined') {
  window.formatDate = function(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  };
}
if (typeof window.formatDateTime === 'undefined') {
  window.formatDateTime = function(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };
}
if (typeof window.statusBadge === 'undefined') {
  window.statusBadge = function(status) {
    const map = {
      'sample_collected': ['badge-info',    'Collected'],
      'under_process':    ['badge-warning', 'Processing'],
      'report_ready':     ['badge-success', 'Report Ready'],
      'paid':             ['badge-success', 'Paid'],
      'partial':          ['badge-warning', 'Partial'],
      'due':              ['badge-error',   'Due'],
      'active':           ['badge-success', 'Active'],
      'inactive':         ['badge-neutral', 'Inactive'],
      'face_pending':     ['badge-warning', 'Face Pending'],
      'success':          ['badge-success', 'Success'],
      'bad_password':     ['badge-error',   'Failed'],
      'locked_out':       ['badge-error',   'Locked'],
      'unknown_email':    ['badge-error',   'Unknown'],
    };
    const [cls, label] = map[status] || ['badge-neutral', status];
    return `<span class="badge ${cls}">${label}</span>`;
  };
}

const Shell = (() => {
  const NAV_ADMIN = [
    {
      group: 'Main',
      items: [
        { href: '/admin/dashboard',         label: 'Dashboard',        icon: 'grid' },
        { href: '/admin/patients',           label: 'Patients',         icon: 'users' },
        { href: '/admin/staff',              label: 'Staff',            icon: 'user-check' },
        { href: '/admin/tests',              label: 'Tests',            icon: 'clipboard' },
        { href: '/admin/doctors',            label: 'Doctors',          icon: 'person' },
      ],
    },
    {
      group: 'Finance',
      items: [
        { href: '/admin/revenue',            label: 'Revenue',          icon: 'trending-up' },
        { href: '/admin/expenses',           label: 'Expenses',         icon: 'credit-card' },
      ],
    },
    {
      group: 'Admin',
      items: [
        { href: '/admin/audit-log',          label: 'Audit Log',        icon: 'shield' },
        { href: '/admin/settings',           label: 'Settings',         icon: 'settings' },
        { href: '/profile',                  label: 'My Profile',       icon: 'person' },
      ],
    },
  ];

  const NAV_STAFF = [
    {
      group: 'Main',
      items: [
        { href: '/staff/add-patient',        label: 'Add Patient',      icon: 'user-plus' },
        { href: '/staff/patients',           label: 'Patients',         icon: 'users' },
      ],
    },
    {
      group: 'Account',
      items: [
        { href: '/profile',                  label: 'My Profile',       icon: 'person' },
        { href: '/staff/settings',           label: 'Settings',         icon: 'settings' },
      ],
    },
  ];

  const ICONS = {
    'grid':         `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>`,
    'users':        `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>`,
    'user-check':   `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="8.5" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/></svg>`,
    'user-plus':    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>`,
    'clipboard':    `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>`,
    'camera':       `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>`,
    'trending-up':  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`,
    'credit-card':  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>`,
    'calendar':     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
    'shield':       `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`,
    'settings':     `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93l-1.41 1.41M4.93 4.93l1.41 1.41M12 2v2M12 20v2M2 12h2M20 12h2M19.07 19.07l-1.41-1.41M4.93 19.07l1.41-1.41"/></svg>`,
    'log-out':      `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`,
    'person':       `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
  };

  function icon(name, size = 16) {
    const svg = ICONS[name] || '';
    return svg.replace('<svg ', `<svg width="${size}" height="${size}" `);
  }

  function showAccessDenied(expectedRole, actualRole) {
    document.getElementById('page-blocking-style')?.remove();
    const roleLabel = expectedRole === 'admin' ? 'Administrator' : 'Staff';
    const redirectDashboard = actualRole === 'admin' ? '/admin/dashboard.html' : '/staff/patients.html';
    const css = `
      <style>
        .access-denied-container {
          position: fixed;
          inset: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #0d1a17;
          background-image: radial-gradient(circle at 10% 20%, rgba(13, 26, 23, 0.95) 0%, rgba(11, 19, 17, 0.98) 90%);
          z-index: 99999;
          font-family: 'Inter', sans-serif;
          padding: 24px;
        }
        .access-denied-card {
          background: rgba(25, 40, 37, 0.35);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border: 1px solid rgba(109, 0, 1, 0.25);
          border-radius: 16px;
          padding: 48px 40px;
          max-width: 440px;
          width: 100%;
          text-align: center;
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
          animation: denSlideUp 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @keyframes denSlideUp {
          from { transform: translateY(24px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .access-denied-icon {
          width: 84px;
          height: 84px;
          background: rgba(109, 0, 1, 0.15);
          color: #ff4d4f;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 28px;
          border: 1.5px solid rgba(109, 0, 1, 0.3);
          box-shadow: 0 0 20px rgba(109, 0, 1, 0.1);
        }
        .access-denied-title {
          font-size: 26px;
          font-weight: 700;
          color: #E8F4F0;
          margin: 0 0 10px;
          letter-spacing: -0.02em;
        }
        .access-denied-subtitle {
          font-size: 13px;
          font-weight: 600;
          color: #ff4d4f;
          margin-bottom: 20px;
          text-transform: uppercase;
          letter-spacing: 0.1em;
        }
        .access-denied-text {
          font-size: 14px;
          color: #b2c4bf;
          margin: 0 0 32px;
          line-height: 1.6;
        }
        .access-denied-btn {
          width: 100%;
          padding: 14px;
          font-weight: 600;
          font-size: 14px;
          background: #6D0001;
          color: #ffffff;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.2s, transform 0.1s;
          box-shadow: 0 4px 12px rgba(109, 0, 1, 0.3);
        }
        .access-denied-btn:hover {
          background: #8b0002;
        }
        .access-denied-btn:active {
          transform: scale(0.98);
        }
      </style>
    `;
    const html = `
      ${css}
      <div class="access-denied-container">
        <div class="access-denied-card">
          <div class="access-denied-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          </div>
          <h1 class="access-denied-title">Access Denied</h1>
          <div class="access-denied-subtitle">${roleLabel} Access Required</div>
          <p class="access-denied-text">You do not have permission to view this section of the system. Please click below to return.</p>
          <button onclick="window.history.length > 1 ? window.history.back() : (window.location.href = '${redirectDashboard}')" class="access-denied-btn">Go Back</button>
        </div>
      </div>
    `;
    document.body.innerHTML = html;
  }

  async function init({ role = 'admin', pageTitle = '', searchable = false } = {}) {
    // Auth check
    let me;
    try {
      me = await API.get('/api/v1/auth/me', { silent: true });
      localStorage.setItem('akriti_current_user', JSON.stringify(me));
      // Proactively pre-cache test catalog for offline add-patient forms
      API.get('/api/v1/tests?page_size=200', { silent: true }).then(res => {
        const tests = (res.items || res || []).filter(t => t.is_active !== false);
        localStorage.setItem('akriti_tests_cache', JSON.stringify(tests));
      }).catch(() => {});
    } catch (err) {
      const isNetworkError = err.message === 'No internet connection' || err.message === 'Server is unreachable';
      const cached = localStorage.getItem('akriti_current_user');
      if (isNetworkError && cached) {
        try {
          me = JSON.parse(cached);
        } catch (_) {}
      }
      if (!me) {
        window.location.href = '/';
        throw new Error('Redirecting to login... Access denied.');
      }
    }

    // Role gate
    const path = window.location.pathname;
    let expectedRole = null;
    if (path.includes('/admin/')) {
      expectedRole = 'admin';
    } else if (path.includes('/staff/')) {
      expectedRole = 'staff';
    }

    if (expectedRole && me.role !== expectedRole) {
      showAccessDenied(expectedRole, me.role);
      throw new Error(`Access Denied: ${expectedRole} access required.`);
    }

    // Access granted — unblock page rendering
    document.getElementById('page-blocking-style')?.remove();

    const nav = me.role === 'admin' ? NAV_ADMIN : NAV_STAFF;
    const currentPath = window.location.pathname;

    // Render sidebar
    const sidebarEl = document.getElementById('sidebar');
    if (sidebarEl) {
      const initials = (me.name || 'U').split(' ').map(w => w[0]).join('').toUpperCase().slice(0,2);
      sidebarEl.innerHTML = `
        <a href="${me.role === 'admin' ? '/admin/dashboard' : '/staff/patients'}" class="sidebar-brand" aria-label="Home">
          <div class="brand-mark">A</div>
          <div class="brand-text">
            <div class="brand-name">Akriti Diagnostics</div>
            <div class="brand-sub">Lab Management</div>
          </div>
        </a>
        ${nav.map(group => `
          <div class="nav-group">
            <div class="nav-group-label">${group.group}</div>
            ${group.items.map(item => `
              <a href="${item.href}" class="nav-item ${currentPath === item.href || currentPath.endsWith(item.href.replace('/','')) ? 'active' : ''}">
                ${icon(item.icon)} ${item.label}
              </a>
            `).join('')}
          </div>
        `).join('')}
        <div class="sidebar-footer">
          <a href="/profile" class="sidebar-user" id="sidebar-user-area" title="View Profile">
            <div class="user-avatar">${initials}</div>
            <div class="user-info">
              <div class="user-name">${escapeHtml(me.name || 'User')}</div>
              <div class="user-role">${me.role}</div>
            </div>
          </a>
          <button class="nav-item" id="logout-btn" style="width:100%; border:none; background:none; text-align:left; color: var(--color-ink-muted);">
            ${icon('log-out')} Sign Out
          </button>
        </div>
      `;

      // Logout
      document.getElementById('logout-btn')?.addEventListener('click', async () => {
        await Modal.confirm('Sign Out', 'Are you sure you want to sign out?', {
          confirmText: 'Sign Out',
          danger: true,
          onConfirm: async () => {
            try {
              await API.post('/api/v1/auth/logout', {}, { silent: true });
            } catch (_) {}
            window.location.href = '/';
          }
        });
      });
    }

    // Render topbar
    const topbarEl = document.getElementById('topbar-title');
    if (topbarEl) topbarEl.textContent = pageTitle;

    // Make sure offline banner exists
    let onlineBanner = document.querySelector('.offline-banner');
    if (!onlineBanner) {
      const mainArea = document.querySelector('.main-area');
      if (mainArea) {
        onlineBanner = document.createElement('div');
        onlineBanner.className = 'offline-banner';
        onlineBanner.setAttribute('role', 'status');
        const topbar = mainArea.querySelector('.topbar');
        if (topbar) {
          topbar.after(onlineBanner);
        } else {
          mainArea.prepend(onlineBanner);
        }
      }
    }

    // Dynamically load offline-queue.js if not already present
    if (typeof window.OfflineQueue === 'undefined') {
      try {
        await new Promise((resolve, reject) => {
          const script = document.createElement('script');
          script.src = '/assets/js/offline-queue.js';
          script.onload = resolve;
          script.onerror = reject;
          document.head.appendChild(script);
        });
      } catch (err) {
        console.warn("Failed to dynamically load offline-queue.js:", err);
      }
    }

    // Mobile hamburger
    const hamburger = document.getElementById('hamburger-btn');
    const overlay   = document.getElementById('sidebar-overlay');
    const sidebar   = document.getElementById('sidebar');
    if (hamburger && sidebar) {
      hamburger.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        overlay?.classList.toggle('open');
      });
      overlay?.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.remove('open');
      });
    }

    // Re-bind theme toggle buttons now that topbar HTML has been injected by this shell
    if (typeof Theme !== 'undefined') Theme.bindButtons();

    // Auto-setup flatpickr on date fields dynamically
    try {
      const dateInputs = document.querySelectorAll('input[type="date"]');
      if (dateInputs.length > 0) {
        // 1. Inject CSS
        if (!document.querySelector('link[href*="flatpickr"]')) {
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.href = 'https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css';
          document.head.appendChild(link);
        }
        
        // 2. Inject Custom Theme overrides style block
        if (!document.getElementById('flatpickr-custom-style')) {
          const style = document.createElement('style');
          style.id = 'flatpickr-custom-style';
          style.innerHTML = `
            .flatpickr-calendar {
              background: var(--color-surface) !important;
              border: 1.5px solid var(--color-border) !important;
              box-shadow: var(--shadow-md) !important;
              font-family: var(--font-body) !important;
              border-radius: var(--radius-md) !important;
            }
            .flatpickr-calendar .flatpickr-months {
              background: transparent !important;
            }
            .flatpickr-current-month {
              color: var(--color-ink) !important;
            }
            .flatpickr-current-month input.cur-year {
              color: var(--color-ink) !important;
            }
            .flatpickr-calendar .flatpickr-weekday {
              color: var(--color-ink-muted) !important;
              font-weight: 600 !important;
            }
            .flatpickr-day {
              color: var(--color-ink) !important;
              border-radius: var(--radius-sm) !important;
            }
            .flatpickr-day.today {
              border-color: var(--color-ink-muted) !important;
            }
            .flatpickr-day.today:hover {
              background: var(--color-border) !important;
              color: var(--color-ink) !important;
            }
            .flatpickr-day.selected, .flatpickr-day.selected:focus, .flatpickr-day.selected:hover {
              background: var(--color-cherry-cola) !important;
              border-color: var(--color-cherry-cola) !important;
              color: #fff !important;
            }
            .flatpickr-day:hover {
              background: var(--color-border) !important;
            }
            .flatpickr-months .flatpickr-prev-month, .flatpickr-months .flatpickr-next-month {
              fill: var(--color-ink) !important;
              color: var(--color-ink) !important;
            }
            .flatpickr-months .flatpickr-prev-month:hover svg, .flatpickr-months .flatpickr-next-month:hover svg {
              fill: var(--color-cherry-cola) !important;
            }
          `;
          document.head.appendChild(style);
        }
        
        // 3. Inject JS and initialize
        if (typeof flatpickr === 'undefined') {
          await new Promise((resolve) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/flatpickr';
            script.onload = resolve;
            document.head.appendChild(script);
          });
        }
        
        // Convert input type to text and initialize flatpickr
        document.querySelectorAll('input[type="date"]').forEach(input => {
          input.type = 'text';
          flatpickr(input, {
            dateFormat: 'Y-m-d',
            maxDate: input.id === 'staff-dob' || input.id === 'patient-dob' ? 'today' : undefined,
            allowInput: true
          });
        });
      }
    } catch (e) {
      console.warn("Flatpickr auto initialization failed:", e);
    }

    // Store me globally
    window._me = me;
    return me;
  }

  return { init, icon };
})();
// Global password visibility toggle handler via event delegation
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.password-toggle-btn');
  if (btn) {
    const input = document.getElementById(btn.getAttribute('data-target'));
    if (input) {
      const isPass = input.type === 'password';
      input.type = isPass ? 'text' : 'password';
      btn.setAttribute('aria-label', isPass ? 'Hide password' : 'Show password');
      btn.innerHTML = isPass
        ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`
        : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
    }
  }
});

window.Shell = Shell;
