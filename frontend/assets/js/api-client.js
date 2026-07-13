/**
 * AKRITI — API Client
 * Wraps fetch with:
 *  - credentials: 'include' (httpOnly cookies)
 *  - Idempotency-Key on mutating requests (UUID v4)
 *  - Silent 401 → token refresh → retry once
 *  - Structured error handling → Toast
 *
 * Usage:
 *   const data = await API.get('/api/v1/patients');
 *   const result = await API.post('/api/v1/patients', payload);
 *   const result = await API.patch('/api/v1/patients/123', payload);
 *   const result = await API.delete('/api/v1/patients/123');
 */

const API = (() => {
  let isRefreshing = false;
  let refreshWaiters = [];

  function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  async function refreshToken() {
    const res = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });
    if (!res.ok) throw new Error('Session expired');
    return res.ok;
  }

  async function request(method, path, body = null, options = {}) {
    const mutating = ['POST', 'PATCH', 'PUT', 'DELETE'].includes(method.toUpperCase());

    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    if (mutating && !options.skipIdempotency) {
      headers['Idempotency-Key'] = options.idempotencyKey || uuidv4();
    }

    const init = {
      method: method.toUpperCase(),
      credentials: 'include',
      headers,
    };

    if (body !== null) {
      init.body = JSON.stringify(body);
    }

    let res;
    try {
      res = await fetch(path, init);
    } catch (err) {
      const isOnline = navigator.onLine !== false;
      const errorMsg = isOnline ? 'Server is unreachable' : 'No internet connection';
      if (!options.silent) {
        if (typeof window.Toast !== 'undefined') {
          window.Toast.show(errorMsg, 'error');
        }
      }
      throw new Error(errorMsg);
    }

    // 401 → try refresh once
    if (res.status === 401 && !options._retry) {
      if (isRefreshing) {
        await new Promise((resolve, reject) => refreshWaiters.push({ resolve, reject }));
        return request(method, path, body, { ...options, _retry: true });
      }
      isRefreshing = true;
      try {
        await refreshToken();
        refreshWaiters.forEach(w => w.resolve());
      } catch (err) {
        refreshWaiters.forEach(w => w.reject(err));
        refreshWaiters = [];
        isRefreshing = false;
        // Redirect to login if not already there
        if (!window.location.pathname.endsWith('/index.html') && window.location.pathname !== '/') {
            window.location.href = '/index.html';
        }
        throw err;
      }
      refreshWaiters = [];
      isRefreshing = false;
      return request(method, path, body, { ...options, _retry: true });
    }

    if (!res.ok) {
      let errData = {};
      try { errData = await res.json(); } catch (_) {}
      
      let msg = errData?.detail || errData?.message || `Request failed (${res.status})`;
      if (typeof msg === 'object' && msg !== null) {
        if (Array.isArray(msg)) {
          msg = msg.map(e => e.msg || e.message || JSON.stringify(e)).join(', ');
        } else {
          msg = msg.message || msg.detail || JSON.stringify(msg);
        }
      }

      if (!options.silent) {
        if (typeof window.Toast !== 'undefined') {
          window.Toast.show(msg, 'error');
        }
      }
      const err = new Error(msg);
      err.status = res.status;
      err.data = errData;
      throw err;
    }

    // 204 No Content
    if (res.status === 204) return null;

    return res.json();
  }

  return {
    get:    (path, opts)         => request('GET',    path, null, opts),
    post:   (path, body, opts)   => request('POST',   path, body, opts),
    patch:  (path, body, opts)   => request('PATCH',  path, body, opts),
    put:    (path, body, opts)   => request('PUT',    path, body, opts),
    delete: (path, opts)         => request('DELETE', path, null, opts),
    // Raw request with full control
    raw:    (method, path, body, opts) => request(method, path, body, opts),
    uuidv4,
  };
})();

window.API = API;
