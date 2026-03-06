import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

schedule_file = ROOT / "data" / "schedule.json"
index_file = ROOT / "docs" / "index.html"

with open(schedule_file,"r",encoding="utf-8") as f:
    data=json.load(f)

sessions=data["sessions"]

rows=""

for s in sessions:

    session_id=s.get("session_id")
    course=s.get("course","CPR Class")
    start=s.get("start","")

    if "T" in start:
        date=start.split("T")[0]
        time=start.split("T")[1][:5]
    else:
        date=start
        time=""

    rows+=f"""
<li>
<a href="classes/{session_id}.html">
{course} — {date} {time}
</a>
</li>
"""

html=f"""
<!DOCTYPE html>
<html>
<head>

<title>CPR Class Schedule | 910CPR</title>

<meta name="viewport" content="width=device-width,initial-scale=1">

<style>

body {{
font-family: Arial;
background: linear-gradient(#f3f5f7,#e8f0f8);
padding:40px;
}}

.container {{
max-width:900px;
margin:auto;
background:#f5f6f7;
padding:30px;
border-radius:12px;
}}

a {{
text-decoration:none;
color:#2a7de1;
}}

li {{
margin:8px 0;
}}

</style>

</head>

<body>

<div class="container">

<h1>CPR Class Schedule</h1>

<p>Select a class session below.</p>

<ul>

{rows}

</ul>

</div>

</body>
</html>
"""

with open(index_file,"w",encoding="utf-8") as f:
    f.write(html)

print(f"Index created with {len(sessions)} sessions.")