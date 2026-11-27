/* Pick one approved hero at random on each load. Never animate or prefetch the deck. */
(() => {
  document.querySelectorAll('[data-family-hero]').forEach(image => {
    let images;
    try { images = JSON.parse(image.dataset.heroImages); } catch { return; }
    if (!Array.isArray(images) || !images.length) return;
    const key = `910cpr:family-hero:${image.dataset.familyHero}`;
    let previous;
    try {
      previous = sessionStorage.getItem(key);
    } catch { /* Storage is optional; selection is still random. */ }
    const choices = images.filter(item => item.url !== previous);
    const previousImage = images.find(item => item.url === previous);
    let selected;
    const show = () => {
      selected = choices.length
        ? choices.splice(Math.floor(Math.random() * choices.length), 1)[0]
        : previousImage && previousImage !== selected ? previousImage : null;
      if (!selected) {
        image.hidden = true;
        if (image.parentElement) image.parentElement.hidden = true;
        return;
      }
      image.alt = selected.alt;
      if (selected.srcset) image.srcset = selected.srcset;
      else image.removeAttribute('srcset');
      image.src = selected.url;
    };
    image.addEventListener('load', () => {
      if (selected) {
        try { sessionStorage.setItem(key, selected.url); } catch { /* optional */ }
      }
    });
    image.addEventListener('error', show);
    show();
  });
})();
