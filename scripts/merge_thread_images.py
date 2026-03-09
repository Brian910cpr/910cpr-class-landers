import json
from pathlib import Path

repo_root = Path(".")
archive_path = repo_root / "raw" / "course_archive_v3.json"
thread_map_path = repo_root / "raw" / "thread_course_image_map.json"
output_path = repo_root / "raw" / "course_archive_v4.json"

archive = json.loads(archive_path.read_text(encoding="utf-8"))
thread_map = json.loads(thread_map_path.read_text(encoding="utf-8"))

# Support either:
# 1) {"courses": [...]}
# 2) {"209806": {...}, "210549": {...}}
if isinstance(thread_map, dict) and "courses" in thread_map and isinstance(thread_map["courses"], list):
    thread_index = {str(c["course_id"]): c for c in thread_map["courses"]}
elif isinstance(thread_map, dict):
    thread_index = {str(k): v for k, v in thread_map.items()}
else:
    raise ValueError("thread_course_image_map.json is not in a supported format.")

for course in archive["courses"]:
    cid = str(course["course_id"])

    if cid in thread_index:
        recovered = thread_index[cid].get("image_urls", []) or []

        existing = set(course.get("image_urls", []) or [])
        merged = sorted(existing.union(recovered))

        course["image_urls"] = merged
        course["thread_images_added"] = len(merged) - len(existing)
        course["thread_image_recovery"] = "matched"
    else:
        course["thread_images_added"] = 0
        course["thread_image_recovery"] = "no-match"

archive["version"] = 4
archive["recovered_thread_images"] = True

output_path.write_text(json.dumps(archive, indent=2), encoding="utf-8")

print("Wrote:", output_path)