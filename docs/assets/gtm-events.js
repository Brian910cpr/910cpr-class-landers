window.dataLayer = window.dataLayer || [];
function dl(event, props){ try{ dataLayer.push(Object.assign({event}, props||{})); }catch(e){} }

document.addEventListener('DOMContentLoaded', function () {
  var sessionLinks = Array.prototype.slice.call(document.querySelectorAll('a[href*=""\/sessions\/""]')).slice(0, 15);
  if (sessionLinks.length) {
    var items = sessionLinks.map(function(a){
      var m = (a.href||'').match(/\/sessions\/([a-z0-9]+)/i);
      return {
        item_id:   (m && m[1]) || null,
        item_name: ((a.dataset && (a.dataset.title||'')) || a.title || a.textContent || '').trim().slice(0,100),
        item_list_name: 'Periscope Sessions',
        item_category: (a.dataset && a.dataset.course) || null,
        location_id: (a.dataset && a.dataset.city) || null
      };
    });
    dl('view_item_list', { items: items });
  }

  document.addEventListener('click', function(e){
    var el = e.target.closest && e.target.closest('a,button');
    if (!el) return;

    if (el.dataset && el.dataset.event) {
      var payload = {};
      for (var k in el.dataset) if (k !== 'event') payload[k] = el.dataset[k];
      payload.link_text = (el.innerText||'').trim().slice(0,80);
      payload.link_url  = el.href || null;
      dl(el.dataset.event, payload);
      return;
    }

    if (el.matches && el.matches('a[href*=""\/sessions\/""]')) {
      var m = (el.href||'').match(/\/sessions\/([a-z0-9]+)/i);
      dl('select_item', {
        item_id: (m && m[1]) || null,
        item_name: ((el.dataset && (el.dataset.title||'')) || el.title || el.textContent || '').trim().slice(0,100),
        item_list_name: 'Periscope Sessions',
        link_url: el.href
      });
      dl('book_click', { link_url: el.href });
      return;
    }

    if (el.matches && el.matches('a[href^=""tel:""]'))   { dl('click_phone', { link_url: el.href }); return; }
    if (el.matches && el.matches('a[href^=""mailto:""]')){ dl('click_email', { link_url: el.href }); return; }
  });

  var searchForm = document.querySelector('form[id*=""search""], form[action*=""search""]');
  if (searchForm) {
    searchForm.addEventListener('submit', function(){
      var qInput = searchForm.querySelector('input[name=""q""], input[type=""search""]');
      var q = (qInput && qInput.value) || '';
      dl('search', { search_term: (q||'').toString().slice(0,100) });
    });
  }
});
