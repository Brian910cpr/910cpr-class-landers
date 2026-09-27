/* Select one approved, build-verified image per visit. No timer or slideshow. */
(() => {
  document.querySelectorAll('[data-family-hero]').forEach(image => {
    let images;
    try { images = JSON.parse(image.dataset.heroImages); } catch { return; }
    if (!Array.isArray(images) || !images.length) return;
    const key = `910cpr:family-hero:${image.dataset.familyHero}`;
    let index = 0;
    try {
      const previous = sessionStorage.getItem(key);
      const lastIndex = images.findIndex(item => item.url === previous);
      index = (lastIndex + 1) % images.length;
      sessionStorage.setItem(key, images[index].url);
    } catch {
      // Storage can be disabled; the first approved image remains usable.
    }
    let attempts = 0;
    const show = () => {
      const selected = images[index];
      image.alt = selected.alt;
      if (selected.srcset) image.srcset = selected.srcset;
      else image.removeAttribute('srcset');
      image.src = selected.url;
    };
    image.addEventListener('error', () => {
      attempts += 1;
      if (attempts >= images.length) {
        image.hidden = true;
        return;
      }
      index = (index + 1) % images.length;
      show();
    });
    show();
  });
})();
