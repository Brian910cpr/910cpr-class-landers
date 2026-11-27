"""Restricted replay adapter; expectations are provided independently of the selector.

Only supply LAYERED_INDEPENDENT_ORACLE_FILE in a trusted, nonpublishing workspace.
The reviewed JSON manifest binds a UTC as_of/epoch and input_sha256, page_courses,
instructors, rooms, and one outcome (offers or an explicit zero reason) per
90-day Eastern scope. Adjacent authorities/{lane}.json files are independently
sourced and fingerprinted; do not generate expectations from selector output.
Review source provenance outside this adapter. Hashes prove consistency, not
source authority. Local comparator success must never authorize deployment.
"""
import hashlib
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
UTC = timezone.utc
SCHEMA = "independent-layered-outcomes.v1"
# Bind the independent witness to bytes the selector actually consumes, including
# the unmodified scheduling policy and the browser's route rules.
INPUTS = (
    "data/audit/live_availability_snapshot_preview.json",
    "data/runtime/canonical_scheduling_demand.json",
    "data/sessions_current.json",
    "docs/data/schedule_future.json",
    "data/inventory/course_consumption_rules.json",
    "data/inventory/appointment_containers.json",
    "data/config/block_schedule_pages.json",
    "data/config/course_catalog.json",
    "data/config/people_catalog.json",
    "data/config/location_resource_map.json",
    "data/config/calendar_sources.json",
    "data/config/layered_scheduling_policy.json",
    "data/config/public_location_policy.json",
    "data/config/public_offer_policy.json",
    "data/config/native_class_checkout_capabilities.json",
    "data/config/native_skills_activation.json",
    "docs/assets/resolved-selector-availability.js",
)
AUTHORITIES = {"calendar", "occupancy", "catalog", "qualified_instructors", "resources", "routes"}


def instant(value):
    if not isinstance(value, str) or "T" not in value:
        raise ValueError("invalid instant")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.utcoffset() is None:
        raise ValueError("unqualified instant")
    return dt.astimezone(UTC)


def freeze_inputs(root, policy_bytes=None):
    return {name: hashlib.sha256(
        policy_bytes if name == "data/config/layered_scheduling_policy.json" and policy_bytes is not None
        else (root / name).read_bytes()).hexdigest() for name in INPUTS}


def epoch_for(now, inputs):
    return hashlib.sha256(json.dumps([now.isoformat(), inputs],
        sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def configure(manifest, inputs, configs, pages, authority_dir):
    """Independent authority axes stay separate from hand-checked outcomes."""
    if manifest.get("schema") != SCHEMA or manifest.get("input_sha256") != inputs:
        raise ValueError("independent snapshot mismatch")
    now = instant(manifest["as_of"])
    if manifest.get("epoch") != epoch_for(now, inputs):
        raise ValueError("independent epoch mismatch")
    witnesses = manifest["authority_sha256"]
    if set(witnesses) != AUTHORITIES or any(not isinstance(v, str)
            or not re.fullmatch("[0-9a-f]{64}", v) for v in witnesses.values()):
        raise ValueError("independent source evidence missing")
    evidence = {}
    for lane in AUTHORITIES:
        data = (authority_dir / (lane + ".json")).read_bytes()
        if hashlib.sha256(data).hexdigest() != witnesses[lane]:
            raise ValueError("independent authority digest mismatch")
        values = json.loads(data)
        if values.get("epoch") != manifest["epoch"]:
            raise ValueError("independent authority epoch mismatch")
        evidence[lane] = values
    courses = manifest["page_courses"]
    if set(courses) != pages or not pages.issubset(configs):
        raise ValueError("independent course universe incomplete")
    for key in pages:
        reviewed = courses[key]
        if (not isinstance(reviewed, list) or not reviewed or len(set(reviewed)) != len(reviewed)
                or set(reviewed) != set(configs[key]["allowed_course_ids"])):
            raise ValueError("independent course universe does not match configured courses")
    instructors = manifest["instructors"] # independently reviewed roster key -> public selector label
    rooms = manifest["rooms"]               # public resource/venue label -> reviewed room key
    if (instructors != evidence["qualified_instructors"]["instructors"]
            or rooms != evidence["resources"]["rooms"]
            or courses != evidence["catalog"]["page_courses"]):
        raise ValueError("expected scope axes differ from independent authority")
    if not instructors or not rooms or any(not isinstance(k, str) or not k.strip()
            or not isinstance(v, str) or not v.strip()
            for table in (instructors, rooms) for k, v in table.items()):
        raise ValueError("missing instructor or room crosswalk")
    if len(set(instructors.values())) != len(instructors):
        raise ValueError("ambiguous public instructor identity")
    first_day = now.astimezone(ET).date()
    dates = [(first_day + timedelta(days=i)).isoformat() for i in range(90)]
    required = {(page, day, teacher, course) for page in pages for day in dates
                for teacher in instructors for course in courses[page]}
    expected = {}
    for row in manifest["outcomes"]:
        scope = tuple(row["scope"])
        if scope in expected:
            raise ValueError("duplicate independent scope")
        expected[scope] = {"offers": row["offers"], "zero_reason": row.get("zero_reason")}
    return now, required, expected


# Execute the actual shipped client lease, elapsed-time and action code; never
# navigate to any returned URL or use it to claim checkout was tested.
VISIBILITY_JS = """
const fs = require('node:fs');
const resolver = require(process.argv[1]);
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const now = resolver.businessNow('America/New_York', new Date(input.now));
const result = {};
for (const [page, {feed, path, capabilities, options}] of Object.entries(input.pages)) {
  const rows = [];
  for (const day of resolver.datesForPublication(feed.dates, feed.validUntil, Date.parse(input.now))) {
    for (const slot of resolver.selectableStartTimes(day, now)) {
      for (const course of slot.courses) {
        const option = options.find(o => o.courseId === course.courseId);
        if (!option) continue;
        const contexts = option.fullWidth && option.skillsContexts?.length
          ? option.skillsContexts.map(c => c.key) : [''];
        const actions = contexts.map(skillsContext => resolver.registrationAction(course, {
          date: day.date, startTime: slot.startTime, pagePath: path,
          familyContext: page === 'heartsaver' ? 'heartsaver' : '',
          skillsContext, skillsContextVerified: !!skillsContext
        }, capabilities));
        const modes = [...new Set(actions.map(a => a.mode))];
        rows.push([day.date, slot.startTime, course, modes]);
      }
    }
  }
  result[page] = rows;
}
process.stdout.write(JSON.stringify(result));
"""


def observed_outcomes(root, feeds, html_pages, configs, manifest, now, required):
    def embedded(html, key):
        match = re.search(r"(?m)^\s*const " + key + r" = ", html)
        if not match:
            raise ValueError("required renderer schema missing")
        return json.JSONDecoder().raw_decode(html[match.end():])[0]

    pages = {}
    for name, feed in feeds.items():
        path = "/" + configs[name]["output_path"].removeprefix("docs/")
        html = html_pages[name]
        route = embedded(html, "availabilityUrl")
        if not route.startswith("/data/block-selector-availability/" + name + ".json?v="):
            raise ValueError("renderer refers to another feed")
        pages[name] = {"feed": feed, "path": path,
            "capabilities": embedded(html, "nativeClassCapabilities"),
            "options": embedded(html, "courseOptions")}
    if set(pages) != {scope[0] for scope in required}:
        raise ValueError("renderer omitted a page")
    output = subprocess.run(["node", "-e", VISIBILITY_JS,
        str((root / "docs/assets/resolved-selector-availability.js").resolve())],
        input=json.dumps({"now": now.isoformat(), "pages": pages}), text=True,
        capture_output=True, timeout=45, check=True)
    rows = json.loads(output.stdout)
    people = {label: key for key, label in manifest["instructors"].items()}
    observed = {scope: [] for scope in required}
    for page, offers in rows.items():
        for day, clock, course, modes in offers:
            local = datetime.fromisoformat(day + "T" + clock)
            start = local.replace(tzinfo=ET).astimezone(UTC)
            if (local.replace(tzinfo=ET, fold=1).astimezone(UTC) != start
                    or start.astimezone(ET).replace(tzinfo=None) != local):
                raise ValueError("ambiguous rendered start")
            minutes = course["schedulerConsumptionMinutes"]
            if type(minutes) is not int or minutes <= 0:
                raise ValueError("missing positive consumed duration")
            end = start + timedelta(minutes=minutes)
            if course.get("occupiedUntil") and instant(course["occupiedUntil"]) != end:
                raise ValueError("rendered end mismatch")
            scope = (page, day, people[course["instructor"]], str(course["courseId"]))
            room = manifest["rooms"][course.get("resource") or course["location"]]
            if len(modes) != 1 or modes[0] not in {"request", "native", "skills-reservation"}:
                raise ValueError("unresolved or variant-dependent browser route")
            # This observes what customers are offered, not a successful checkout.
            # A booking CTA unauthorized by the independent manifest is a mismatch.
            capability = "request_only" if modes[0] == "request" else "verified_booking"
            role = ("seated" if course["offerType"] == "seated_class" else
                    "barnacle" if course.get("scheduleRole") == "barnacle" else "open")
            observed.setdefault(scope, []).append((start.isoformat(), end.isoformat(), room, role, capability))
    return observed
