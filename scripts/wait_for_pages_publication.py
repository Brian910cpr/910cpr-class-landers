"""Wait for the Pages release of a completed refresh before auditing the live host.

A successful refresh can push selector JSON just before GitHub Pages begins its
deployment. Observing the old CDN lease at that point is meaningful evidence
but does not answer whether the newly generated release reached the public host.
This guard never changes availability, customer records, or publishing state.
"""
import json
from http.client import HTTPException
import os
import sys
import time
from datetime import datetime, timedelta
from urllib.request import Request, urlopen

PAGES_NAME = "pages build and deployment"
REFRESH_NAME = "Refresh admin availability"
MAX_WAIT_SECONDS = 160


def stamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def matching_pages_run(runs, expected_sha, refresh_completed_at):
    """Latest Pages run for exactly the commit published by this refresh."""
    cutoff = stamp(refresh_completed_at) - timedelta(minutes=2)
    candidates = [
        run for run in runs
        if run.get("name") == PAGES_NAME
        and run.get("head_sha") == expected_sha
        and run.get("created_at")
        and stamp(run["created_at"]) >= cutoff
    ]
    return max(candidates, key=lambda run: run["created_at"], default=None)


def read_runs(repo, token, expected_sha):
    """Read bounded, commit-filtered Pages candidates, never arbitrary huge run lists.

    A transient truncated GitHub response is retried by main(), within its
    existing deadline. Exhaustion is an error, never a green observation.
    """
    all_runs = []
    for page in range(1, 4):
        request = Request(
            f"https://api.github.com/repos/{repo}/actions/runs"
            f"?head_sha={expected_sha}&per_page=30&page={page}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urlopen(request, timeout=12) as response:
            rows = json.load(response)["workflow_runs"]
        if not isinstance(rows, list):
            raise ValueError("GitHub workflow_runs is not a list")
        all_runs.extend(rows)
        if len(rows) < 30:
            return all_runs
    raise ValueError("GitHub workflow runs exceed bounded pagination")


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as handle:
        event = json.load(handle)
    source = event.get("workflow_run") or {}
    if source.get("name") != REFRESH_NAME:
        print("Not a refresh completion; live observer will run without a Pages wait.")
        return 0
    if source.get("conclusion") != "success":
        print("Refresh was not successful; no publication success may be inferred.", file=sys.stderr)
        return 1
    repo = os.environ["GITHUB_REPOSITORY"]
    expected_sha = os.environ["GITHUB_SHA"]
    token = os.environ["GITHUB_TOKEN"]
    finished = source["updated_at"]
    deadline = time.monotonic() + MAX_WAIT_SECONDS

    while True:
        try:
            run = matching_pages_run(read_runs(repo, token, expected_sha), expected_sha, finished)
        except (OSError, HTTPException, ValueError, KeyError) as exc:
            # Never ignore a failed/missing probe. Retry only within a strict bound.
            print(f"Unable to confirm Pages status ({type(exc).__name__}); retrying.")
            run = None
        if run and run.get("status") == "completed":
            if run.get("conclusion") == "success":
                print("Pages deployment succeeded for the refresh commit; starting actual-host verification.")
                return 0
            print("Pages deployment did not succeed; public release is not verified.", file=sys.stderr)
            return 1
        if time.monotonic() >= deadline:
            print("No successful matching Pages deployment within the bounded wait; fail closed.", file=sys.stderr)
            return 1
        time.sleep(8)


if __name__ == "__main__":
    raise SystemExit(main())
