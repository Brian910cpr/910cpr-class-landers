// /scripts/cards.js
(function(){
  const BASE = 'https://coastalcprtraining.enrollware.com';

  async function loadCoursesJSON(path){
    const res = await fetch(path, {cache:'no-store'}).catch(()=>null);
    return res ? res.json() : [];
  }
  async function loadScheduleHTML(path){
    const res = await fetch(path, {cache:'no-store'}).catch(()=>null);
    return res ? res.text() : '';
  }
  function absURL(url){ try{ return new URL(url, BASE).toString(); }catch(e){ return null; } }

  // Find nearest image for each enroll link; return [{label,url,img}]
  function parseSessionsWithImages(html){
    const tmp = document.createElement('div');
    tmp.innerHTML = html;

    // collect all <img> so we can match by proximity
    const allImgs = Array.from(tmp.querySelectorAll('img'));

    const out = [];
    tmp.querySelectorAll('a[href]').forEach(a=>{
      const abs = absURL(a.getAttribute('href')||'');
      if(!abs || !(/(\/enroll\?id=\d+)|(\/reg\/\d+)/i.test(abs))) return;

      const label = (a.textContent||'').trim().replace(/\s+/g,' ');

      // Heuristic: check container → siblings → previous elements → parent chain
      const container = a.closest('tr, li, .class, .schedule-item, div, section') || a.parentElement;
      let img = container ? container.querySelector('img') : null;

      // if not found, probe previous siblings up to 5
      let cur = container || a.parentElement, tries = 0;
      while(!img && cur && tries < 5){
        cur = cur.previousElementSibling;
        if(cur){ img = cur.querySelector && cur.querySelector('img'); }
        tries++;
      }
      // last resort: nearest image in DOM order (min distance)
      if(!img && allImgs.length){
        let best=null,bestDist=1e9;
        allImgs.forEach((im,idx)=>{
          const d = Math.abs(idx - allImgs.indexOf(img)); // fallback distance
        });
        // simple fallback – first image on page
        img = allImgs[0];
      }

      const src = img ? absURL(img.getAttribute('src')||'') : null;
      out.push({label, url: abs, img: src});
    });

    // de-dupe by URL
    const seen = new Set();
    return out.filter(x=>{ if(seen.has(x.url)) return false; seen.add(x.url); return true; });
  }

  function courseMatches(label, course){
    return (course.patterns||[]).some(p=>{
      try{ return new RegExp(p,'i').test(label); }catch(e){ return false; }
    });
  }

  // Build a map: slug -> representative image URL (first seen)
  function buildCourseImageMap(sessions, courses){
    const map = {};
    sessions.forEach(s=>{
      courses.forEach(c=>{
        if(!map[c.slug] && courseMatches(s.label, c) && s.img){
          map[c.slug] = s.img;
        }
      });
    });
    return map;
  }

  async function renderCards({coursesJsonPath, scheduleHtmlPath, targetSelector, prefix}){
    const [courses, html] = await Promise.all([
      loadCoursesJSON(coursesJsonPath),
      loadScheduleHTML(scheduleHtmlPath)
    ]);
    const sessions = parseSessionsWithImages(html);
    const imgMap = buildCourseImageMap(sessions, courses);

    const wrap = document.querySelector(targetSelector);
    if(!wrap) return;

    wrap.innerHTML = courses.map(c=>{
      const img = imgMap[c.slug] || c.image || ''; // allow manual override via courses.json "image"
      const href = `${prefix}${c.slug}.html`;
      return `
        <div class="card card-course">
          ${img ? `<img class="card-img" src="${img}" alt="${c.name}">` : ''}
          <h3>${c.name}</h3>
          <p><a class="btn" href="${href}">View ${c.name}</a></p>
        </div>
      `;
    }).join('');
  }

  window.CourseCards = { renderCards };
})();
