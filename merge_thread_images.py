import json
from pathlib import Path

repo_root = Path(".")
archive_path = repo_root / "raw" / "course_archive_v3.json"
thread_map_path = repo_root / "raw" / "thread_course_image_map.json"
output_path = repo_root / "raw" / "course_archive_v4.json"

archive = json.loads(archive_path.read_text(encoding="utf-8"))
thread_map = json.loads(thread_map_path.read_text(encoding="utf-8"))

thread_index = {c["course_id"]: c for c in thread_map["courses"]}

for course in archive["courses"]:
    cid = str(course["course_id"])

    if cid in thread_index:
        recovered = thread_index[cid].get("image_urls", [])

        existing = set(course.get("image_urls", []))
        merged = sorted(existing.union(recovered))

        course["image_urls"] = merged
        course["thread_images_added"] = len(merged) - len(existing)

archive["version"] = 4
archive["recovered_thread_images"] = True

output_path.write_text(json.dumps(archive, indent=2), encoding="utf-8")

print("Wrote:", output_path)