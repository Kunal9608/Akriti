/**
 * AKRITI — Offline Queue (IndexedDB + auto-sync)
 * SRS §5.11 — FR-11.1, FR-11.2
 *
 * While offline: Add Patient + Attendance actions are queued with their
 * original Idempotency-Key so the backend's idempotency replay prevents
 * duplicates on sync even if the connection drops mid-replay.
 */

const OfflineQueue = (() => {
  const DB_NAME  = 'akriti-offline';
  const DB_VER   = 1;
  const STORE    = 'queue';
  let db = null;
  let onlineBanner = null;
  let syncInProgress = false;

  // ── IndexedDB setup ───────────────────────────────────────────────────────
  function openDB() {
    return new Promise((resolve, reject) => {
      if (db) return resolve(db);
      const req = indexedDB.open(DB_NAME, DB_VER);
      req.onupgradeneeded = e => {
        const d = e.target.result;
        if (!d.objectStoreNames.contains(STORE)) {
          const store = d.createObjectStore(STORE, { keyPath: 'id', autoIncrement: true });
          store.createIndex('timestamp', 'timestamp');
        }
      };
      req.onsuccess = e => { db = e.target.result; resolve(db); };
      req.onerror   = e => reject(e.target.error);
    });
  }

  async function enqueue(endpoint, method, payload, idempotencyKey) {
    const d = await openDB();
    return new Promise((resolve, reject) => {
      const tx = d.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).add({
        endpoint, method, payload, idempotencyKey,
        timestamp: Date.now(),
      });
      tx.oncomplete = resolve;
      tx.onerror    = e => reject(e.target.error);
    });
  }

  async function getAll() {
    const d = await openDB();
    return new Promise((resolve, reject) => {
      const req = d.transaction(STORE, 'readonly').objectStore(STORE).getAll();
      req.onsuccess = e => resolve(e.target.result || []);
      req.onerror   = e => reject(e.target.error);
    });
  }

  async function remove(id) {
    const d = await openDB();
    return new Promise((resolve, reject) => {
      const tx = d.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).delete(id);
      tx.oncomplete = resolve;
      tx.onerror    = e => reject(e.target.error);
    });
  }

  // ── Connectivity detection ────────────────────────────────────────────────
  async function isOnline() {
    if (!navigator.onLine) return false;
    try {
      const res = await fetch('/health', { method: 'GET', cache: 'no-store' });
      return res.ok;
    } catch {
      return false;
    }
  }

  function updateBanner(offline, count = 0) {
    if (!onlineBanner) onlineBanner = document.querySelector('.offline-banner');
    if (!onlineBanner) return;
    if (offline) {
      onlineBanner.textContent = count > 0
        ? `Offline — ${count} action${count > 1 ? 's' : ''} queued`
        : 'Offline — Changes will sync when connection is restored';
      onlineBanner.classList.add('show');
    } else {
      onlineBanner.classList.remove('show');
    }
  }

  // ── Sync ──────────────────────────────────────────────────────────────────
  async function flush() {
    if (syncInProgress) return;
    const online = await isOnline();
    if (!online) return;

    const items = await getAll();
    if (!items.length) { updateBanner(false); return; }

    syncInProgress = true;
    let synced = 0;
    let failed = 0;

    for (const item of items) {
      try {
        const res = await fetch(item.endpoint, {
          method: item.method,
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            'Idempotency-Key': item.idempotencyKey,
          },
          body: JSON.stringify(item.payload),
        });
        if (res.ok || res.status === 409) {
          // 409 = idempotent replay (already exists), treat as success
          await remove(item.id);
          synced++;
        } else {
          failed++;
        }
      } catch {
        failed++;
      }
    }

    syncInProgress = false;

    if (synced > 0 && typeof window.Toast !== 'undefined') {
      window.Toast.show(`${synced} offline action${synced > 1 ? 's' : ''} synced successfully`, 'success');
    }
    if (failed === 0) {
      updateBanner(false);
    }
  }

  // ── Init: connectivity listeners ──────────────────────────────────────────
  async function init() {
    onlineBanner = document.querySelector('.offline-banner');

    const check = async () => {
      const online = await isOnline();
      const items = await getAll();
      if (!online) {
        updateBanner(true, items.length);
      } else {
        await flush();
      }
    };

    window.addEventListener('online',  () => flush());
    window.addEventListener('offline', () => check());

    // Initial check
    check();

    // Periodic ping every 30s
    setInterval(check, 30_000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  return { enqueue, flush, getAll };
})();

window.OfflineQueue = OfflineQueue;
