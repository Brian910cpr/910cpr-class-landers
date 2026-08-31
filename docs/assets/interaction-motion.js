(function () {
  const reduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isMaximPortal = /\/corp\/maxim(?:\.html)?\/?$/i.test(window.location.pathname);

  // TEMPORARY DIAGNOSTIC: expose the Maxim portal shell without the access gate.
  // Authenticated employee/workflow API calls remain protected server-side.
  if (isMaximPortal) {
    window.addEventListener('DOMContentLoaded', () => {
      document.getElementById('accessGate')?.classList.add('hidden');
    });
  }

  // The Maxim corporate portal performs authenticated Supabase Edge Function
  // requests from its inline application script. A network request that never
  // settles used to leave the access gate displaying "Checking..." forever.
  // Keep this guard scoped to /corp/maxim so shared site behavior is unchanged.
  if (isMaximPortal) {
    const nativeFetch = window.fetch.bind(window);
    window.fetch = function maximFetchWithTimeout(input, init) {
      const url = typeof input === 'string' ? input : input && input.url;
      if (!String(url || '').includes('/functions/v1/maxim-portal')) {
        return nativeFetch(input, init);
      }
      const controller = new AbortController();
      const upstreamSignal = init && init.signal;
      const timeout = window.setTimeout(() => controller.abort(), 15000);
      if (upstreamSignal) {
        if (upstreamSignal.aborted) controller.abort();
        else upstreamSignal.addEventListener('abort', () => controller.abort(), { once: true });
      }
      return nativeFetch(input, { ...(init || {}), signal: controller.signal })
        .catch(error => {
          if (controller.signal.aborted && !(upstreamSignal && upstreamSignal.aborted)) {
            throw new Error('Maxim portal request timed out. Please try again.');
          }
          throw error;
        })
        .finally(() => window.clearTimeout(timeout));
    };
  }

  function connect(source, destination) {
    if (!source || !destination) return;
    destination.classList.remove('lw-motion-settle');
    if (reduced()) return;
    const from = source.getBoundingClientRect();
    const to = destination.getBoundingClientRect();
    const trail = document.createElement('span');
    trail.className = 'lw-motion-trail';
    trail.style.left = `${from.left + from.width / 2}px`;
    trail.style.top = `${from.top + from.height / 2}px`;
    document.body.appendChild(trail);
    const animation = trail.animate([
      { transform: 'translate(-50%, -50%) scale(.65)', opacity: .2 },
      { transform: `translate(${to.left + to.width / 2 - from.left - from.width / 2}px, ${to.top + Math.min(to.height, 80) / 2 - from.top - from.height / 2}px) scale(1)`, opacity: .8 }
    ], { duration: 260, easing: 'cubic-bezier(.2,.7,.2,1)' });
    animation.finished.finally(() => {
      trail.remove();
      destination.classList.add('lw-motion-settle');
      window.setTimeout(() => destination.classList.remove('lw-motion-settle'), 300);
    });
  }

  function progress(source, destination) {
    if (!source || !destination) return;
    connect(source, destination);
    if (!window.matchMedia('(max-width: 820px)').matches) return;
    // Advance only when the visitor makes a new choice.
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        const target = destination.getBoundingClientRect();
        const viewportOffset = Math.max(88, window.innerHeight * 0.38);
        const top = Math.max(0, window.scrollY + target.top - viewportOffset);
        window.scrollTo({ top, behavior: reduced() ? 'auto' : 'smooth' });
      });
    });
  }

  window.LanderWareMotion = Object.freeze({ connect, progress });
}());
