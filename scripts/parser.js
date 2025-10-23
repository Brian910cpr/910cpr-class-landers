
(function(){
  async function loadCourses(){
    const here = location.pathname.endsWith('/') ? location.pathname : location.pathname.replace(/[^\/]+$/, '');
    const url = here.includes('/courses/') ? '../courses.json' : './courses.json';
    const res = await fetch(url, {cache:'no-store'}).catch(()=>null);
    return res ? res.json() : [];
  }

  async function loadScheduleHTML(){
    const res = await fetch('../shared/schedule.html', {cache:'no-store'}).catch(()=>null);
    return res ? res.text() : '';
  }

  function parseSessionsFromHTML(html){
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    const items = [];
    tmp.querySelectorAll('a[href]').forEach(a=>{
      const href = a.getAttribute('href')||'';
      const abs = new URL(href, 'https://coastalcprtraining.enrollware.com').toString();
      if (/(\/enroll\?id=\d+)|(\/reg\/\d+)/i.test(abs)){
        const label = (a.textContent||'').trim().replace(/\s+/g,' ');
        items.push({label, url: abs});
      }
    });
    const seen = new Set();
    return items.filter(x=>{ if(seen.has(x.url)) return false; seen.add(x.url); return true; });
  }

  function matchesCourse(label, course){
    if (!course || !course.patterns) return true;
    return course.patterns.some(p=>{
      try{ return new RegExp(p,'i').test(label); }catch(e){ return false; }
    });
  }

  function render(list, course){
    const tbody = document.getElementById('sessions-tbody');
    const total = document.getElementById('session-total');
    tbody.innerHTML = '';
    list.sort((a,b)=>a.label.localeCompare(b.label, undefined, {numeric:true}));
    if(list.length===0){
      tbody.innerHTML = '<tr><td>No upcoming sessions detected for this course.</td><td></td></tr>';
    }else{
      list.forEach(s=>{
        const tr = document.createElement('tr');
        const td1 = document.createElement('td');
        td1.textContent = s.label;
        const td2 = document.createElement('td');
        const link = document.createElement('a');
        link.href = s.url; link.textContent='Register'; link.className='btn'; link.rel='nofollow noopener';
        td2.appendChild(link);
        tr.appendChild(td1); tr.appendChild(td2);
        tbody.appendChild(tr);
      });
    }
    if (total) total.textContent = String(list.length);

    // Minimal JSON-LD
    const ld = {
      "@context":"https://schema.org",
      "@graph": list.slice(0,100).map(s=>({
        "@type":"Event",
        "name": (course && course.name ? course.name + " – " : "") + s.label,
        "eventAttendanceMode":"https://schema.org/OfflineEventAttendanceMode",
        "eventStatus":"https://schema.org/EventScheduled",
        "url": s.url,
        "organizer":{"@type":"Organization","name":"910CPR","url":"https://910cpr.com"}
      }))
    };
    const tag = document.createElement('script');
    tag.type='application/ld+json';
    tag.textContent = JSON.stringify(ld);
    document.head.appendChild(tag);
  }

  window.CoursePage = {
    async run(){
      const slug = document.documentElement.getAttribute('data-course-slug');
      const [courses, html] = await Promise.all([loadCourses(), loadScheduleHTML()]);
      const course = (courses||[]).find(c=>c.slug===slug) || null;
      const all = parseSessionsFromHTML(html);
      const filtered = course ? all.filter(x=>matchesCourse(x.label, course)) : all;
      render(filtered, course);
    }
  };
})();