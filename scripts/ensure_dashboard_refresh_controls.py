from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "docs" / "admin" / "dashboard.html"

OLD_TOOLBAR = '<div class="actions"><span id="loadStatus" class="status">Loading live data…</span><button class="btn" id="prevMonth">‹ Earlier</button><button class="btn" id="todayBtn">Today</button><button class="btn" id="nextMonth">Later ›</button></div>'
CURRENT_TOOLBAR = '<div class="actions"><span id="loadStatus" class="status loading" role="status" aria-live="polite">Loading live data…</span><span id="calendarFreshness" class="status">Checking calendar…</span><a class="btn primary" href="/admin/refresh-availability.html">Force Refresh</a><button class="btn" id="reloadAvailability">Reload Data</button><button class="btn" id="prevMonth">‹ Earlier</button><button class="btn" id="todayBtn">Today</button><button class="btn" id="nextMonth">Later ›</button></div>'
NEW_TOOLBAR = '<div class="actions"><span id="loadStatus" class="status loading" role="status" aria-live="polite">Loading live data…</span><span id="calendarFreshness" class="status">Checking calendar…</span><a class="btn primary" href="/admin/refresh-availability.html">Force Refresh</a><button class="btn" id="reloadAvailability">Reload Data</button><button class="btn" id="todayBtn">Today</button></div>'

OLD_LOAD = "async function load(){const sourceEl=document.getElementById('sources'),status=document.getElementById('loadStatus');sourceEl.innerHTML='';"
NEW_LOAD = "async function load(){const sourceEl=document.getElementById('sources'),status=document.getElementById('loadStatus'),fresh=document.getElementById('calendarFreshness');sourceEl.innerHTML='';"

OLD_CALENDAR_SUCCESS = "const data=await res.json();calendarEvents=normalizeCalendar(data);const stamp=data.generated_at?new Date(data.generated_at).toLocaleString():'unknown';addSource('Calendar snapshot',`${calendarEvents.length} events · refreshed ${stamp}`,'good')"
NEW_CALENDAR_SUCCESS = "const data=await res.json();calendarEvents=normalizeCalendar(data);const generated=data.generated_at?new Date(data.generated_at):null,stamp=generated?generated.toLocaleString():'unknown';if(fresh){const age=generated?Math.max(0,Math.round((Date.now()-generated.getTime())/60000)):null;fresh.textContent=generated?`Published ${stamp}${age!==null?` · ${age}m ago`:''}`:'Publish time unknown';fresh.className='status '+(age!==null&&age<=10?'good':'warn')}addSource('Calendar snapshot',`${calendarEvents.length} events · refreshed ${stamp}`,'good')"

OLD_END = "document.getElementById('prevMonth').onclick=()=>{monthCursor=new Date(monthCursor.getFullYear(),monthCursor.getMonth()-1,1);renderMonth()};document.getElementById('nextMonth').onclick=()=>{monthCursor=new Date(monthCursor.getFullYear(),monthCursor.getMonth()+1,1);renderMonth()};document.getElementById('todayBtn').onclick=()=>{monthCursor=new Date();monthCursor.setDate(1);selectDay(keyOf(new Date()))};document.getElementById('reloadAvailability').onclick=()=>load();load();setInterval(()=>load(),60000);"
CURRENT_END = "document.getElementById('prevMonth').onclick=()=>{monthCursor=new Date(monthCursor.getFullYear(),monthCursor.getMonth()-1,1);renderMonth()};document.getElementById('nextMonth').onclick=()=>{monthCursor=new Date(monthCursor.getFullYear(),monthCursor.getMonth()+1,1);renderMonth()};document.getElementById('todayBtn').onclick=()=>{monthCursor=new Date();monthCursor.setDate(1);selectDay(keyOf(new Date()))};document.getElementById('reloadAvailability').onclick=()=>load();clearRecord();load();setInterval(()=>load(),60000);"
NEW_END = "document.getElementById('todayBtn').onclick=()=>{monthCursor=new Date();monthCursor.setDate(1);selectDay(keyOf(new Date()))};document.getElementById('reloadAvailability').onclick=()=>load();clearRecord();load();setInterval(()=>load(),60000);"

OLD_MONTH_CSS = '.month{border:1px solid var(--line);border-radius:12px;padding:10px}.month h3{text-align:center;margin:0 0 7px}.cal{display:grid;grid-template-columns:repeat(7,1fr);gap:4px}'
NEW_MONTH_CSS = '.month{border:1px solid var(--line);border-radius:12px;padding:10px}.monthnav{display:flex;align-items:center;justify-content:center;gap:8px;margin:0 0 7px}.monthnav h3{text-align:center;margin:0;min-width:150px}.monthnav .btn{padding:3px 8px;font-size:14px;line-height:1.2}.cal{display:grid;grid-template-columns:repeat(7,1fr);gap:4px}'

OLD_RENDER_HEADER = "let h=`<h3>${first.toLocaleDateString('en-US',{month:'long',year:'numeric'})}</h3><div class=\"cal\">`;"
NEW_RENDER_HEADER = "let h=`<div class=\"monthnav\"><button class=\"btn\" id=\"monthPrev\" type=\"button\" aria-label=\"Previous month\">‹</button><h3>${first.toLocaleDateString('en-US',{month:'long',year:'numeric'})}</h3><button class=\"btn\" id=\"monthNext\" type=\"button\" aria-label=\"Next month\">›</button></div><div class=\"cal\">`;"

OLD_RENDER_TAIL = "h+='</div>';host.innerHTML=h;host.querySelectorAll('[data-day]').forEach(el=>el.onclick=()=>selectDay(el.dataset.day))}"
NEW_RENDER_TAIL = "h+='</div>';host.innerHTML=h;const prev=host.querySelector('#monthPrev'),next=host.querySelector('#monthNext');if(prev)prev.onclick=()=>{monthCursor=new Date(monthCursor.getFullYear(),monthCursor.getMonth()-1,1);renderMonth()};if(next)next.onclick=()=>{monthCursor=new Date(monthCursor.getFullYear(),monthCursor.getMonth()+1,1);renderMonth()};host.querySelectorAll('[data-day]').forEach(el=>el.onclick=()=>selectDay(el.dataset.day))}"

text = DASHBOARD.read_text(encoding="utf-8")
original = text

CURRENT_MARKERS = [
    'id="calendarFreshness"',
    'href="/admin/refresh-availability.html"',
    'id="reloadAvailability"',
    'class="monthnav"',
    'id="monthPrev"',
    'id="monthNext"',
    "host.querySelector('#monthPrev')",
    "host.querySelector('#monthNext')",
    "document.getElementById('reloadAvailability').onclick=()=>load()",
    "setInterval(()=>load(),60000)",
]

# New dashboard features may add controls inside the toolbar. If every durable
# refresh/navigation marker is already present, preserve that newer markup.
if all(marker in text for marker in CURRENT_MARKERS):
    print("Dashboard refresh controls and month navigation already current.")
    raise SystemExit(0)

# Keep older refresh-control migrations working if the dashboard is ever regenerated
# from a pre-refresh version.
for old, new in [
    (OLD_TOOLBAR, CURRENT_TOOLBAR),
    (OLD_LOAD, NEW_LOAD),
    (OLD_CALENDAR_SUCCESS, NEW_CALENDAR_SUCCESS),
    (OLD_END, CURRENT_END),
]:
    if old in text and new not in text:
        text = text.replace(old, new, 1)

# Planner month navigation belongs beside the visible month name. The calendar
# snapshots already publish a 90-day planning horizon; these controls simply let
# the operator browse that loaded future data without changing scheduling policy.
for old, new in [
    (CURRENT_TOOLBAR, NEW_TOOLBAR),
    (OLD_MONTH_CSS, NEW_MONTH_CSS),
    (OLD_RENDER_HEADER, NEW_RENDER_HEADER),
    (OLD_RENDER_TAIL, NEW_RENDER_TAIL),
    (CURRENT_END, NEW_END),
]:
    if new in text:
        continue
    if old not in text:
        raise SystemExit(f"Expected dashboard marker not found: {old[:100]}")
    text = text.replace(old, new, 1)

if not all(marker in text for marker in CURRENT_MARKERS):
    missing = [marker for marker in CURRENT_MARKERS if marker not in text]
    raise SystemExit(f"Dashboard update incomplete; missing markers: {missing}")

if text != original:
    DASHBOARD.write_text(text, encoding="utf-8")
    print("Updated dashboard refresh controls and month navigation.")
else:
    print("Dashboard refresh controls and month navigation already current.")
