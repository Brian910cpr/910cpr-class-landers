/* Shared cabinet navigation: explicit local parents survive reload and new tabs. */
(function () {
  'use strict';
  const origin = typeof location === 'object' ? location.origin : 'https://910cpr.com';
  const pages = {
    '/admin/all-classes.html': ['session', 'q', 'filter', 'month'],
    '/admin/class-registry.html': ['q', 'source', 'visibility', 'health'],
    '/admin/person-record.html': ['id'],
    '/admin/now.html': [],
    '/admin/admin-port.html': ['date']
  };
  function parent(value, depth = 0) {
    if (!value || value.length > 12000 || depth > 4) return '';
    try {
      const url = new URL(value, origin);
      if (url.origin !== origin || url.username || url.password || !pages[url.pathname]) return '';
      const clean = new URL(url.pathname, origin);
      for (const key of pages[url.pathname]) {
        if (url.searchParams.has(key)) clean.searchParams.set(key, url.searchParams.get(key));
      }
      const y = Number(url.searchParams.get('navY'));
      if (Number.isFinite(y) && y >= 0 && y <= 1000000 && url.searchParams.has('navY')) clean.searchParams.set('navY', String(y));
      const up = parent(url.searchParams.get('up'), depth + 1);
      if (up) clean.searchParams.set('up', up);
      return clean.pathname + clean.search;
    } catch { return ''; }
  }
  function child(target, context) {
    const clean = parent(target), up = parent(context);
    if (!clean || !up) return clean;
    const url = new URL(clean, origin);
    url.searchParams.set('up', up);
    return url.pathname + url.search;
  }
  if (typeof module === 'object' && module.exports) { module.exports = {parent, child}; return; }
  function context() {
    const url = new URL(location.href);
    const values = window.LanderWareCabinetState?.() || {};
    for (const [key, value] of Object.entries(values)) url.searchParams.set(key, value);
    url.searchParams.set('navY', String(Math.round(window.scrollY)));
    return parent(url.href);
  }
  function restoreScroll() {
    const y = new URLSearchParams(location.search).get('navY');
    if (y !== null && Number.isFinite(Number(y))) requestAnimationFrame(() => window.scrollTo(0, Math.max(0, Math.min(1000000, Number(y)))));
  }
  function updateUp() {
    const control = document.getElementById('cabinetUp');
    if (!control) return;
    const current = new URL(context(), origin), explicit = parent(current.searchParams.get('up'));
    let fallback = '/admin/all-classes.html';
    if (current.pathname === '/admin/all-classes.html') {
      current.searchParams.delete('session'); current.searchParams.delete('up');
      fallback = parent(current.href);
    }
    control.href = explicit || fallback;
    const destination = new URL(control.href, origin).pathname.split('/').pop().replace('.html', '').replaceAll('-', ' ');
    control.title = control.ariaLabel = 'Up to ' + destination;
  }
  function decorate(event) {
    const link = event.target.closest?.('a[href]');
    if (!link || link.id === 'cabinetUp' || link.hasAttribute('download')) return;
    const url = new URL(link.href, origin);
    if (url.origin !== origin || !['/admin/person-record.html', '/admin/all-classes.html', '/admin/admin-port.html'].includes(url.pathname)) return;
    // Only drill-down links carry a parent; cabinet-level navigation stays ordinary.
    if (!url.searchParams.has('id') && !url.searchParams.has('session') && !url.searchParams.has('date')) return;
    link.href = child(url.href, context());
  }
  for (const type of ['click', 'auxclick', 'contextmenu']) document.addEventListener(type, decorate, true);
  window.LanderWareCabinet = {parent, child, updateUp, restoreScroll};
  updateUp();
})();
