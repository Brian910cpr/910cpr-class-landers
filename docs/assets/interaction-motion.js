(function () {
  const reduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
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
  window.LanderWareMotion = Object.freeze({ connect });
}());
