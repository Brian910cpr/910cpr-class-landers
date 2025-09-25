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
