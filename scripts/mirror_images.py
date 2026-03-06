import os
import re
import requests
from urllib.parse import urlparse
from pathlib import Path

# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

PROJECT_ROOT = r"D:\Users\ten77\Documents\GitHub\910cpr-class-landers"
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
IMAGE_DIR = os.path.join(DOCS_DIR, "images")

TIMEOUT = 10

# ---------------------------------------------------
# PREP
# ---------------------------------------------------

os.makedirs(IMAGE_DIR, exist_ok=True)

IMG_PATTERN = re.compile(
    r'<img[^>]+src=["\'](https?://[^"\']+)["\']',
    re.IGNORECASE
)

# ---------------------------------------------------
# DOWNLOAD IMAGE
# ---------------------------------------------------

def download_image(url):

    try:
        parsed = urlparse(url)

        filename = os.path.basename(parsed.path)

        if not filename:
            filename = "image.jpg"

        local_path = os.path.join(IMAGE_DIR, filename)

        if os.path.exists(local_path):
            return "/images/" + filename

        r = requests.get(url, timeout=TIMEOUT)

        if r.status_code == 200:

            with open(local_path, "wb") as f:
                f.write(r.content)

            print("Downloaded:", filename)

            return "/images/" + filename

        else:
            print("Failed:", url)
            return url

    except Exception as e:

        print("Error:", url)
        return url


# ---------------------------------------------------
# PROCESS HTML FILE
# ---------------------------------------------------

def process_file(path):

    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    changed = False

    matches = IMG_PATTERN.findall(html)

    for url in matches:

        local = download_image(url)

        if local != url:

            html = html.replace(url, local)
            changed = True

    if changed:

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

        print("Updated:", path)


# ---------------------------------------------------
# SCAN LANDERS
# ---------------------------------------------------

def run():

    print("Scanning HTML landers...")

    for root, dirs, files in os.walk(DOCS_DIR):

        for file in files:

            if file.endswith(".html"):

                path = os.path.join(root, file)
                process_file(path)

    print("Done.")


# ---------------------------------------------------

if __name__ == "__main__":
    run()