from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / "docs" / "admin" / "dashboard.html"

OLD_TOOLBAR = '<div class="actions"><span id="loadStatus" class="status">Loading live data…</span><button class="btn" id="prevMonth">‹ Earlier</button><button class="btn" id="todayBtn">Today</button><button class="btn" id="nextMonth">Later ›</button></div>'
NEW_TOOLBAR = '<div class="actions"><span id="loadStatus" class="status">Loading live data…</span><span id="calendarFreshness" class="status">Checking calendar…</span><a class="btn primary" href="/admin/refresh-availability.html">Force Refresh</a><button class="btn" id="reloadAvailability">Reload Data</button><button class="btn" id="prevMonth">‹ Earlier</button><button class="btn" id="todayBtn">Today</button><button class="btn" id="nextMonth">Later ›</button></div>'

OLD_LOAD = "async function load(){const sourceEl=document.getElementById('sources'),status=document.getElementById('loadStatus');sourceEl.innerHTML='';"
NEW_LOAD = "async function load(){const sourceEl=document.getElementById('sources'),status=document.getElementById('loadStatus'),fresh=document.getElementById('calendarFreshness');sourceEl.innerHTML='';"

OLD_CALENDAR_SUCCESS = "const data=await res.json();calendarEvents=normalizeCalendar(data);const stamp=data.generated_at?new Date(data.generated_at).toLocaleString():'unknown';addSource('Calendar snapshot',`${calendarEvents.length} events · refreshed ${stamp}`,'good')"
NEW_CALENDAR_SUCCESS = "const data=await res.json();calendarEvents=normalizeCalendar(data);const generated=data.generated_at?new Date(data.generated_at):null,stamp=generated?generated.toLocaleString():'unknown';if(fresh){const age=generated?Math.max(0,Math.round((Date.now()-generated.getTime())/60000)):null;fresh.textContent=generated?`Published ${stamp}${age!==null?` · ${age}m ago`:''}`:'Publish time unknown';fresh.className='status '+(age!==null&&age<=10?'good':'warn')}addSource('Calendar snapshot',`${calendarEvents.length} events · refreshed ${stamp}`,'good')"

OLD_END = "document.getElementById('prevMonth').onclick=()=>{monthCursor=new Date(monthCursor.getFullYear(),monthCursor.getMonth()-1,1);renderMonth()};document.getElementById('nextMonth').onclick=()=>{monthCursor=new Date(monthCursor.getFullYear(),monthCursor.getMonth()+1,1);renderMonth()};document.getElementById('todayBtn').onclick=()=>{monthCursor=new Date();monthCursor.setDate(1);selectDay(keyOf(new Date()))};load();"
NEW_END = "document.getElementById('prevMonth').onclick=()=>{monthCursor=new Date(monthCursor.getFullYear(),monthCursor.getMonth()-1,1);renderMonth()};document.getElementById('nextMonth').onclick=()=>{monthCursor=new Date(monthCursor.getFullYear(),monthCursor.getMonth()+1,1);renderMonth()};document.getElementById('todayBtn').onclick=()=>{monthCursor=new Date();monthCursor.setDate(1);selectDay(keyOf(new Date()))};document.getElementById('reloadAvailability').onclick=()=>load();load();setInterval(()=>load(),60000);"

text = DASHBOARD.read_text(encoding="utf-8")
original = text

CURRENT_MARKERS = [
    'id="calendarFreshness"',
    'href="/admin/refresh-availability.html"',
    'id="reloadAvailability"',
    "document.getElementById('reloadAvailability').onclick=()=>load()",
    "setInterval(()=>load(),60000)",
]

if all(marker in text for marker in CURRENT_MARKERS):
    print("Dashboard refresh controls already current.")
    raise SystemExit(0)

for old, new in [
    (OLD_TOOLBAR, NEW_TOOLBAR),
    (OLD_LOAD, NEW_LOAD),
    (OLD_CALENDAR_SUCCESS, NEW_CALENDAR_SUCCESS),
    (OLD_END, NEW_END),
]:
    if new in text:
        continue
    if old not in text:
        raise SystemExit(f"Expected dashboard marker not found: {old[:80]}")
    text = text.replace(old, new, 1)

if text != original:
    DASHBOARD.write_text(text, encoding="utf-8")
    print("Updated dashboard refresh controls.")
else:
    print("Dashboard refresh controls already current.")
