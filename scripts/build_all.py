import subprocess
import sys
import time

print("====================================")
print("910CPR MASTER LANDER BUILD")
print("====================================")

steps = [
    ("Build Public Schedule", "scripts/build_public_schedule.py"),
    ("Build Course Pages", "scripts/build_course_pages.py"),
    ("Build Class Landers", "scripts/build_class_landers.py"),
    ("Build Index and Sitemap", "scripts/build_index_and_sitemap.py"),
]

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