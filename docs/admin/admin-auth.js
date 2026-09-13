/* Shared owner/admin credential transport. Loading this file does not authorize a user. */
(() => {
  'use strict';
  if (window.LanderAdminAuth) return;

  const STORAGE_KEY = 'hotSyncAdminKey';
  const HEADER_NAME = 'X-Hot-Sync-Admin-Key';
  let key = '', revision = 0, storageBlocked = false;
  const listeners = new Set(), pending = new Set();
  const failure = (code, message) => Object.assign(new Error(message), { code });
  const snapshot = reason => Object.freeze({ hasKey: !!key, revision, reason });

  function change(next, reason) {
    key = next;
    revision++;
    for (const controller of pending) controller.abort();
    pending.clear();
    const state = snapshot(reason);
    for (const listener of listeners) {
      if (revision !== state.revision) break;
      // A broken page hook must not stop credential invalidation or other hooks.
      try { listener(state); } catch (_) { /* Page-specific error handling belongs to the page. */ }
    }
  }

  function getKey() {
    if (storageBlocked) return '';
    try {
      const stored = window.sessionStorage.getItem(STORAGE_KEY) || '';
      if (stored !== key) change(stored, 'credential_changed');
    } catch (_) {
      storageBlocked = true;
      change('', 'storage_unavailable');
    }
    return key;
  }

  function setKey(value) {
    if (typeof value !== 'string' || !value.trim() || /[\r\n\0]/.test(value)) {
      throw failure('INVALID_KEY', 'Enter an admin key.');
    }
    const next = value.trim();
    try { window.sessionStorage.setItem(STORAGE_KEY, next); }
    catch (_) {
      storageBlocked = true;
      change('', 'storage_unavailable');
      throw failure('STORAGE_UNAVAILABLE', 'Admin session storage is unavailable.');
    }
    storageBlocked = false;
    change(next, 'unlock');
  }

  function clearKey(reason = 'lock') {
    let removed = true;
    try { window.sessionStorage.removeItem(STORAGE_KEY); }
    catch (_) { removed = false; }
    storageBlocked = !removed;
    change('', removed ? reason : 'storage_unavailable');
    if (!removed) throw failure('STORAGE_UNAVAILABLE', 'This page is locked, but the stored admin key could not be cleared.');
  }

  function subscribe(listener) {
    if (typeof listener !== 'function') throw new TypeError('An admin state listener is required.');
    getKey();
    listeners.add(listener);
    try { listener(snapshot('initial')); } catch (_) { /* Keep all other hooks operational. */ }
    return () => listeners.delete(listener);
  }

  function parseURL(value) {
    let url;
    try { url = new URL(value, window.location.href); }
    catch (_) { throw failure('UNTRUSTED_URL', 'Admin request URL is invalid.'); }
    if (url.username || url.password || url.hash || /%2f|%5c|%25/i.test(url.pathname) ||
        (url.protocol !== 'https:' && !(url.protocol === 'http:' && url.origin === window.location.origin))) {
      throw failure('UNTRUSTED_URL', 'Admin request URL is not allowed.');
    }
    return url;
  }

  function createClient({ endpoints = [] } = {}) {
    if (!Array.isArray(endpoints) || !endpoints.length) throw new TypeError('Declare the exact admin API endpoints.');
    const allowed = endpoints.map(value => {
      const url = parseURL(value);
      if (url.search || url.pathname === '/') throw new TypeError('Declare an API path, not an entire origin or query.');
      return { origin: url.origin, path: url.pathname.replace(/\/+$/, '') };
    });

    function prepare(value, initialHeaders) {
      const url = parseURL(value);
      if (!allowed.some(base => base.origin === url.origin &&
          (url.pathname === base.path || url.pathname.startsWith(base.path + '/')))) {
        throw failure('UNTRUSTED_URL', 'Admin request is outside this client\'s API endpoints.');
      }
      const credential = getKey(), version = revision;
      if (!credential) throw failure('AUTH_REQUIRED', 'Admin authentication is required.');
      const headers = new Headers(initialHeaders);
      if (headers.has('authorization') || headers.has('x-maxim-session')) {
        throw failure('MIXED_AUTH', 'Corporate or bearer authentication cannot be mixed into an admin request.');
      }
      headers.set(HEADER_NAME, credential);
      const controller = new AbortController();
      pending.add(controller);
      const isCurrent = () => getKey() === credential && revision === version;
      const assertCurrent = () => {
        if (!isCurrent()) throw failure('STALE_AUTH', 'Admin session changed while the request was pending.');
      };
      const handleStatus = status => {
        assertCurrent();
        if (status === 401 || status === 403) {
          clearKey('denied');
          throw failure('AUTH_DENIED', 'Admin authentication was rejected.');
        }
      };
      return Object.freeze({
        url: url.href, headers, signal: controller.signal, isCurrent, assertCurrent, handleStatus,
        finish: () => pending.delete(controller),
      });
    }

    async function json(value, options = {}) {
      const ticket = prepare(value, options.headers);
      const controller = new AbortController();
      const abort = () => controller.abort();
      const signals = [ticket.signal, options.signal].filter(Boolean);
      for (const signal of signals) {
        signal.addEventListener('abort', abort, { once: true });
        if (signal.aborted) abort();
      }
      try {
        const response = await window.fetch(ticket.url, {
          ...options, headers: ticket.headers, signal: controller.signal,
          cache: 'no-store', credentials: 'omit', redirect: 'error', referrerPolicy: 'no-referrer',
        });
        ticket.handleStatus(response.status);
        if (!response.ok) throw failure('HTTP_ERROR', `Admin request failed (HTTP ${response.status}).`);
        const data = await response.json();
        ticket.assertCurrent();
        if (controller.signal.aborted) throw failure('REQUEST_ABORTED', 'Admin request was cancelled.');
        return Object.freeze({
          data, isCurrent: ticket.isCurrent,
          // Call synchronously when updating private UI, including after other awaits.
          commit: render => { ticket.assertCurrent(); return render(data); },
        });
      } finally {
        for (const signal of signals) signal.removeEventListener('abort', abort);
        ticket.finish();
      }
    }
    return Object.freeze({ prepare, json });
  }

  // Back/forward restoration must discard old private UI even after re-entry of the same key.
  window.addEventListener('pageshow', event => {
    getKey();
    if (event.persisted) change(key, 'pageshow');
  });
  window.addEventListener('storage', event => {
    try {
      if (event.storageArea === window.sessionStorage && (event.key === STORAGE_KEY || event.key === null)) {
        change(getKey(), 'credential_changed');
      }
    } catch (_) { getKey(); }
  });
  window.LanderAdminAuth = Object.freeze({
    version: '2026-09-13-r2', STORAGE_KEY, HEADER_NAME,
    getKey, setKey, clearKey, subscribe, createClient,
  });
})();
