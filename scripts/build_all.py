import subprocess
import sys
import time

print("====================================")
print("910CPR MASTER LANDER BUILD")
print("====================================")

complete_rebuild = any(arg in {"--complete", "--full"} for arg in sys.argv[1:])

steps = [
    ("Build Public Schedule", "scripts/build_public_schedule.py"),
    ("Build Course Pages", "scripts/build_course_pages.py"),
    ("Build Class Landers", "scripts/build_class_landers.py"),
]

if complete_rebuild:
    steps.append(("Build Index and Sitemap", "scripts/build_index_and_sitemap.py"))

mode_label = "COMPLETE REBUILD" if complete_rebuild else "STANDARD REBUILD"
print("Mode:", mode_label)
print("Note: build_sessions_current is not part of this run.")

for name, script in steps:
    print("")
    print("Running:", name)
    print("------------------------------------")

    result = subprocess.run([sys.executable, script])

    if result.returncode != 0:
        print("")
        print("ERROR during:", name)
        print("Build stopped.")
        sys.exit(1)

    print("Completed:", name)

print("")
print("====================================")
print("ALL BUILDS COMPLETED SUCCESSFULLY")
print("====================================")

time.sleep(2)
