#!/usr/bin/env python3
"""Exchange LinkedIn's long-lived refresh token for a current access token."""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request


def main() -> int:
    required = {
        "client_id": os.getenv("LINKEDIN_CLIENT_ID"),
        "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET"),
        "refresh_token": os.getenv("LINKEDIN_REFRESH_TOKEN"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise SystemExit("Missing LinkedIn credential(s): " + ", ".join(missing))
    form = urllib.parse.urlencode({"grant_type": "refresh_token", **required}).encode()
    request = urllib.request.Request(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    access_token = payload.get("access_token")
    if not access_token:
        raise SystemExit("LinkedIn refresh response did not contain an access token")
    # The caller captures stdout. Never print the response or refresh token.
    print(access_token)
    return 0


if __name__ == "__main__":
    sys.exit(main())
