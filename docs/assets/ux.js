(function(){
  function ready(fn){ if(document.readyState!="loading"){ fn(); } else { document.addEventListener("DOMContentLoaded",fn); } }
  ready(function(){
    // Collapsible behavior
    var cards = document.querySelectorAll("[data-collapsible='1']");
    cards.forEach(function(card){
      if(card.classList.contains("collapsible-ready")) return;
      card.classList.add("collapsible-ready");

      var header = card.querySelector(".card-header, h2, h3, .title") || card;
      if(header){ header.style.cursor="pointer"; header.addEventListener("click", function(){ card.classList.toggle("open"); }); }

      // default state: open on desktop, closed on mobile
      if (window.matchMedia("(max-width: 768px)").matches) { card.classList.remove("open"); }
      else { card.classList.add("open"); }
    });
  });
})();

// BEGIN HOVN_VIEW_MORE
(function(){
  window.HOVN_BASE = window.HOVN_BASE || 'https://www.hovn.app/service-providers/910cpr/sessions';
  function init(){
    var cards = document.querySelectorAll('.card[data-collapsible="1"]');
    cards.forEach(function(card){
      if(card.dataset.controlsInit === '1') return;
      card.dataset.controlsInit = '1';

      var hovn = card.getAttribute('data-hovn') || window.HOVN_BASE;

      var container = document.createElement('div');
      container.className = 'card-controls';

      var more = document.createElement('a');
      more.className = 'view-more';
      more.target = '_blank';
      more.rel = 'noopener';
      more.href = hovn;
      more.textContent = 'View more dates';

      var close = document.createElement('button');
      close.className = 'close-card';
      close.type = 'button';
      close.textContent = 'Close';

      close.addEventListener('click', function(){
        card.classList.remove('open');
      });

      container.appendChild(more);
      container.appendChild(close);

      var body = card.querySelector('.card-body') || card;
      body.appendChild(container);
    });
  }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

<script>
(function(){
  const KEY = "theme";
  const doc = document.documentElement;

  function set(t){
    doc.setAttribute("data-theme", t);
    try { localStorage.setItem(KEY, t); } catch(e){}
  }

  const saved   = (function(){try{ return localStorage.getItem(KEY) }catch(e){return null}})();
  const prefers = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark":"light";
  set(saved || prefers);

  // expose a simple toggle
  window.toggleTheme = () => set(doc.getAttribute("data-theme")==="dark" ? "light" : "dark");
})();
</script>

// END HOVN_VIEW_MORE
