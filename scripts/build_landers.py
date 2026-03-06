import json
import os
import re
from html import unescape
from datetime import datetime

DATA_FILE = "../data/schedule.json"
OUTPUT_DIR = "../docs/classes"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

sessions = data["sessions"]


def strip_html(text):
    text = unescape(str(text))
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_dt(value):

    raw = str(value)

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I:%M %p",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except:
            pass

    return None


template = """
<!DOCTYPE html>
<html>
<head>

<meta charset="UTF-8">
<title>{course}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

body {{
font-family: Arial;
background:#eef2f5;
padding:40px;
}}

.card {{
background:white;
padding:30px;
border-radius:12px;
max-width:900px;
margin:auto;
box-shadow:0 4px 14px rgba(0,0,0,0.15);
}}

.button {{
display:inline-block;
padding:12px 22px;
background:#2c73d2;
color:white;
text-decoration:none;
border-radius:8px;
}}

.notice {{
background:#fff3cd;
padding:15px;
border-radius:8px;
margin-bottom:20px;
}}

</style>

</head>

<body>

<div class="card">

{past_notice}

<h1>{course}</h1>

<p>
<strong>Date:</strong> {date}<br>
<strong>Time:</strong> {time}<br>
<strong>Location:</strong> {location}
</p>

<p>

{button_html}

</p>

<hr>

<h2>Upcoming Classes</h2>

<div id="futureSessions">Loading upcoming classes...</div>

</div>


<script>

const courseName = "{course}";
const sessionID = "{session_id}";

fetch("/910cpr-class-landers/data/public_schedule.json")
.then(r=>r.json())
.then(data=>{{

const now = new Date();

const matches = data.sessions.filter(s=>{{

    if(!s.course.toLowerCase().includes(courseName.substring(0,25).toLowerCase()))
        return false;

    if(String(s.session_id) === String(sessionID))
        return false;

    const dt = new Date(s.start);

    return dt >= now;

}});

matches.sort((a,b)=>new Date(a.start)-new Date(b.start));

let html = "<ul>";

matches.slice(0,8).forEach(s=>{{

html += `
<li>
${{new Date(s.start).toLocaleString()}}
 • ${{s.location}}
 <a href="${{s.register_url}}">Register</a>
</li>
`;

}});

html += "</ul>";

if(matches.length === 0)
html = "No upcoming sessions scheduled.";

document.getElementById("futureSessions").innerHTML = html;

}});

</script>

</body>
</html>
"""


count = 0

for s in sessions:

    session_id = s.get("session_id")

    course = strip_html(s.get("course"))

    location = s.get("location")

    register = s.get("register_url")

    dt = parse_dt(s.get("start"))

    if dt:
        date = dt.strftime("%B %d %Y")
        time = dt.strftime("%I:%M %p")
    else:
        date = ""
        time = ""

    past_notice = ""

    if dt and dt < datetime.now():

        past_notice = """
<div class="notice">
This session has passed. See other upcoming sessions below.
</div>
"""

        button_html = f'''
<a class="button" href="/910cpr-class-landers/">
View Upcoming Classes
</a>
'''

    else:

        button_html = f'''
<a class="button" href="{register}">
Register Now
</a>
'''

    html = template.format(
        course=course,
        location=location,
        date=date,
        time=time,
        past_notice=past_notice,
        session_id=session_id,
        button_html=button_html,
    )

    path = os.path.join(OUTPUT_DIR, f"{session_id}.html")

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    count += 1

print("Landers built:", count)