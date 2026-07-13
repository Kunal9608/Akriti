/**
 * AKRITI — Patient Form Logic
 * Handles: multi-test selection, live total, returning-patient lookup,
 * QR generation, payment mode toggle, form submission.
 *
 * Requires: qrcode.min.js loaded on the page, API, Toast.
 *
 * FIXES:
 *  - Test search: race condition fixed — render() only called after tests loaded
 *  - Test selection: click-away-safe event delegation on container (not per-item)
 *  - QR code: generated client-side immediately from UPI string, no server call
 *  - QR code: amount change triggers fresh QR, old one cleared first
 *  - QR code: debounced so fast typing doesn't spam QR generation
 *  - QR code: re-generated whenever QR mode is active AND amount > 0
 */

const PatientForm = (() => {
  let allTests = [];
  let selectedTests = new Map(); // test_id → { name, price }
  let lookupDebounce = null;
  let qrDebounce = null;
  let labSettingsCache = null;

  // ── Load tests from API ───────────────────────────────────────────────────
  async function loadTests() {
    try {
      const res = await API.get('/api/v1/tests?page_size=200');
      allTests = (res.items || res || []).filter(t => t.is_active !== false);
      return allTests;
    } catch {
      Toast.show('Failed to load test catalog', 'error');
      return [];
    }
  }

  // ── Render test picker ────────────────────────────────────────────────────
  // Uses EVENT DELEGATION on the container — no per-item listener re-binding.
  function renderTestPicker(containerId, searchInputId) {
    const container  = document.getElementById(containerId);
    const searchInput = document.getElementById(searchInputId);
    if (!container) return;

    // Event delegation — one listener on container handles all clicks
    // Remove old listener by cloning (safe even if called multiple times)
    const fresh = container.cloneNode(false);
    container.parentNode.replaceChild(fresh, container);
    const cont = document.getElementById(containerId);

    function render(filter = '') {
      const q = (filter || '').toLowerCase().trim();
      const filtered = allTests.filter(t =>
        !q ||
        t.name.toLowerCase().includes(q) ||
        (t.category && t.category.toLowerCase().includes(q))
      );

      if (!filtered.length) {
        cont.innerHTML = `<p class="text-faint text-sm" style="padding:12px 16px">
          ${q ? `No tests match "<strong>${escapeHtml(q)}</strong>"` : 'No tests available'}
        </p>`;
        return;
      }

      // Group by category for better UX
      const groups = {};
      filtered.forEach(t => {
        const cat = t.category || 'General';
        if (!groups[cat]) groups[cat] = [];
        groups[cat].push(t);
      });

      cont.innerHTML = Object.entries(groups).map(([cat, tests]) => `
        <div class="test-group-label" style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--color-ink-faint);padding:10px 14px 4px;border-top:1px solid var(--color-border);user-select:none">${escapeHtml(cat)}</div>
        ${tests.map(t => `
          <div class="test-option ${selectedTests.has(String(t.id)) ? 'selected' : ''}" data-id="${t.id}" style="cursor:pointer;user-select:none">
            <span class="test-name">${escapeHtml(t.name)}</span>
            <span class="test-price">${formatCurrency(t.price)}</span>
          </div>
        `).join('')}
      `).join('');
    }

    cont.addEventListener('click', (e) => {
      const label = e.target.closest('.test-option');
      if (!label) return;
      const id = String(label.dataset.id);
      const test = allTests.find(t => String(t.id) === id);
      if (!test) return;

      if (selectedTests.has(id)) {
        selectedTests.delete(id);
        label.classList.remove('selected');
      } else {
        selectedTests.set(id, { name: test.name, price: Number(test.price) });
        label.classList.add('selected');
      }
      updateTotal();
      renderSelectedChips();
      triggerQRRefresh();
    });

    // Wire search input
    if (searchInput) {
      // Remove old listeners by cloning
      const freshSearch = searchInput.cloneNode(true);
      searchInput.parentNode.replaceChild(freshSearch, searchInput);
      const si = document.getElementById(searchInputId);
      si.addEventListener('input', e => {
        render(e.target.value);
      });
    }

    render(); // Initial render after tests are loaded
    return { render };
  }

  // ── Selected test chips ───────────────────────────────────────────────────
  function renderSelectedChips(chipContainerId = 'selected-tests-chips') {
    const el = document.getElementById(chipContainerId);
    if (!el) return;
    if (!selectedTests.size) {
      el.innerHTML = `<span class="text-faint text-xs">No tests selected</span>`;
      return;
    }
    el.innerHTML = [...selectedTests.entries()].map(([id, t]) => `
      <span class="chip">
        ${escapeHtml(t.name)}
        <span style="font-size:10px;color:var(--color-ink-muted);margin-left:2px">${formatCurrency(t.price)}</span>
        <button type="button" class="chip-remove" data-id="${id}" aria-label="Remove ${escapeHtml(t.name)}">×</button>
      </span>
    `).join('');

    el.querySelectorAll('.chip-remove').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.id;
        selectedTests.delete(id);
        updateTotal();
        renderSelectedChips(chipContainerId);
        triggerQRRefresh();
        // Deselect in picker
        const picker = document.querySelector(`#test-picker-container .test-option[data-id="${id}"]`);
        if (picker) {
          picker.classList.remove('selected');
        }
      });
    });
  }

  // ── Live total ────────────────────────────────────────────────────────────
  function updateTotal(totalElId = 'total-amount-display') {
    const el = document.getElementById(totalElId);
    const total = [...selectedTests.values()].reduce((s, t) => s + Number(t.price), 0);
    if (el) el.textContent = formatCurrency(total);
    const hidden = document.getElementById('total-amount-hidden');
    if (hidden) hidden.value = total;

    // Auto-adjust Amount Paid if it exceeds the new total bill
    const amountInput = document.getElementById('amount-paid');
    if (amountInput) {
      let amount = parseFloat(amountInput.value) || 0;
      if (amount > total) {
        amountInput.value = total;
        // Trigger update to update visibility/QR code
        const modeSection = document.getElementById('payment-mode-section');
        const modeSelect  = document.getElementById('payment-mode');
        const qrSection   = document.getElementById('qr-code-section');
        if (modeSection) modeSection.style.display = total > 0 && total > 0 ? '' : 'none';
        if (qrSection) {
          const isQR = modeSelect && modeSelect.value === 'qr';
          qrSection.style.display = (total > 0 && isQR) ? '' : 'none';
        }
      }
    }
    return total;
  }

  // ── Payment mode toggle ───────────────────────────────────────────────────
  function initPaymentMode() {
    const amountInput = document.getElementById('amount-paid');
    const modeSection = document.getElementById('payment-mode-section');
    const modeSelect  = document.getElementById('payment-mode');
    const qrSection   = document.getElementById('qr-code-section');
    if (!amountInput) return;

    function update() {
      const total = [...selectedTests.values()].reduce((s, t) => s + Number(t.price), 0);
      let amount = parseFloat(amountInput.value) || 0;
      if (amount > total) {
        amount = total;
        amountInput.value = total;
      }
      if (modeSection) modeSection.style.display = amount > 0 ? '' : 'none';
      if (qrSection) {
        const isQR = modeSelect && modeSelect.value === 'qr';
        qrSection.style.display = (amount > 0 && isQR) ? '' : 'none';
      }
      triggerQRRefresh();
    }

    amountInput.addEventListener('input', update);
    if (modeSelect) modeSelect.addEventListener('change', update);
    update();
  }

  // ── QR Code — client-side generation ─────────────────────────────────────
  // Generates UPI QR directly without a server call.
  // Debounced so rapid amount typing doesn't spam renders.
  function triggerQRRefresh() {
    if (qrDebounce) clearTimeout(qrDebounce);
    qrDebounce = setTimeout(_generateQR, 400);
  }

  async function _generateQR() {
    const modeSelect  = document.getElementById('payment-mode');
    const amountInput = document.getElementById('amount-paid');
    const qrEl        = document.getElementById('qr-code-canvas');
    const qrSection   = document.getElementById('qr-code-section');
    if (!qrEl) return;

    const mode   = modeSelect ? modeSelect.value : '';
    const amount = parseFloat(amountInput ? amountInput.value : 0) || 0;

    if (mode !== 'qr' || amount <= 0) {
      qrEl.innerHTML = '';
      if (qrSection) qrSection.style.display = 'none';
      return;
    }

    if (qrSection) qrSection.style.display = '';

    // Fetch lab settings once and cache
    if (!labSettingsCache) {
      try {
        labSettingsCache = await API.get('/api/v1/settings/lab', { silent: true });
      } catch {
        labSettingsCache = {};
      }
    }

    const vpa     = labSettingsCache.lab_upi_vpa || '';
    const labName = labSettingsCache.lab_name    || 'Akriti Diagnostics';

    // Clear previous QR
    qrEl.innerHTML = '';

    if (!vpa) {
      qrEl.innerHTML = `
        <div style="text-align:center;padding:20px">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#9A0002" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <p style="font-size:13px;color:var(--color-ink-muted);margin-top:8px">UPI VPA not configured.<br>Go to <strong>Settings → Lab UPI VPA</strong> to set it.</p>
        </div>`;
      return;
    }

    // Build UPI deep link
    const note = 'Lab Payment';
    const upiString = `upi://pay?pa=${encodeURIComponent(vpa)}&pn=${encodeURIComponent(labName)}&am=${amount.toFixed(2)}&cu=INR&tn=${encodeURIComponent(note)}`;

    // Amount display above QR
    qrEl.innerHTML = `
      <div style="margin-bottom:12px">
        <div style="font-size:12px;color:var(--color-ink-faint);margin-bottom:2px">Pay to: <strong>${escapeHtml(labName)}</strong></div>
        <div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:var(--color-cherry-cola)">${formatCurrency(amount)}</div>
        <div style="font-size:11px;color:var(--color-ink-faint)">${escapeHtml(vpa)}</div>
      </div>
      <div id="qr-canvas-inner" style="display:inline-block;padding:12px;background:#fff;border-radius:8px;border:2px solid var(--color-border)"></div>
      <p style="font-size:11px;color:var(--color-ink-faint);margin-top:8px">Scan with any UPI app (PhonePe, GPay, Paytm…)</p>
    `;

    try {
      if (typeof QRCode !== 'undefined') {
        new QRCode(document.getElementById('qr-canvas-inner'), {
          text: upiString,
          width: 200,
          height: 200,
          colorDark: '#1a1a1a',
          colorLight: '#ffffff',
          correctLevel: QRCode.CorrectLevel.M,
        });
      } else {
        // Fallback: use a public QR API
        const encoded = encodeURIComponent(upiString);
        document.getElementById('qr-canvas-inner').innerHTML =
          `<img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encoded}" width="200" height="200" alt="UPI QR Code">`;
      }
    } catch (err) {
      document.getElementById('qr-canvas-inner').innerHTML =
        `<p style="font-size:12px;color:var(--color-ink-muted)">QR generation failed.<br>Ask patient to pay manually.</p>`;
    }
  }

  // ── Returning patient lookup ───────────────────────────────────────────────
  function initReturningPatientLookup() {
    const mobileInput  = document.getElementById('patient-mobile');
    const suggestionEl = document.getElementById('returning-patient-suggestion');
    if (!mobileInput) return;

    mobileInput.addEventListener('input', e => {
      const val = e.target.value.replace(/\D/g, '');
      if (lookupDebounce) clearTimeout(lookupDebounce);
      if (val.length < 10) {
        if (suggestionEl) suggestionEl.style.display = 'none';
        return;
      }
      lookupDebounce = setTimeout(async () => {
        try {
          const res = await API.get(`/api/v1/patients/search?mobile=${val}`, { silent: true });
          if (res && res.length > 0 && suggestionEl) {
            const p = res[0];
            suggestionEl.style.display = '';
            suggestionEl.innerHTML = `
              <div class="suggestion-card">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                Returning patient: <strong>${escapeHtml(p.name)}</strong> · Age ${p.age} · Dr. ${escapeHtml(p.doctor_name || 'Self')}
                <button type="button" id="autofill-btn" class="btn btn-sm btn-secondary" style="margin-left:8px">Autofill</button>
              </div>
            `;
            document.getElementById('autofill-btn')?.addEventListener('click', () => {
              const nameEl = document.getElementById('patient-name');
              const ageEl  = document.getElementById('patient-age');
              const genderEl = document.getElementById('patient-gender');
              const doctorEl = document.getElementById('patient-doctor');
              if (nameEl)   nameEl.value   = p.name;
              if (ageEl)    ageEl.value    = p.age;
              if (genderEl) genderEl.value = p.gender || '';
              if (doctorEl) doctorEl.value = p.doctor_name || '';
              suggestionEl.style.display = 'none';
              Toast.show('Patient details prefilled', 'info', 2000);
            });
          } else if (suggestionEl) {
            suggestionEl.style.display = 'none';
          }
        } catch {
          if (suggestionEl) suggestionEl.style.display = 'none';
        }
      }, 500);
    });
  }

  // ── Collect form data ─────────────────────────────────────────────────────
  function getFormData() {
    const v = id => { const el = document.getElementById(id); return el ? el.value : ''; };
    return {
      name:          v('patient-name').trim(),
      mobile:        v('patient-mobile').trim(),
      age:           parseInt(v('patient-age')),
      gender:        v('patient-gender'),
      doctor_name:   v('patient-doctor').trim(),
      sample_date:   v('patient-sample-date'),
      amount_paid:   parseFloat(v('amount-paid')) || 0,
      payment_mode:  v('payment-mode') || 'cash',
      test_ids:      [...selectedTests.keys()],
      total_amount:  [...selectedTests.values()].reduce((s, t) => s + Number(t.price), 0),
    };
  }

  function getSelectedTestIds() { return [...selectedTests.keys()]; }

  function setSelectedTests(tests) {
    selectedTests.clear();
    tests.forEach(t => selectedTests.set(String(t.test_id || t.id), { name: t.name, price: Number(t.price) }));
  }

  function clearForm() { selectedTests.clear(); }

  return {
    loadTests,
    renderTestPicker,
    renderSelectedChips,
    updateTotal,
    initPaymentMode,
    initReturningPatientLookup,
    triggerQRRefresh,
    getFormData,
    getSelectedTestIds,
    setSelectedTests,
    clearForm,
  };
})();

window.PatientForm = PatientForm;
