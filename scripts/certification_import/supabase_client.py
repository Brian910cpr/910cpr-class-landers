from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any


class SupabaseClient:
    def __init__(self, url: str | None = None, key: str | None = None):
        self.url = (url or os.environ.get("SUPABASE_URL") or "").rstrip("/")
        self.key = key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
        if not self.url or not self.key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    def request(
        self, path: str, *, method: str = "GET", payload: Any = None,
        prefer: str | None = None,
    ) -> Any:
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            f"{self.url}/rest/v1/{path}", data=body, headers=headers, method=method
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            content = response.read()
            return json.loads(content) if content else None

    def matching_snapshot(self) -> dict[str, list[dict[str, Any]]]:
        profiles = self.request(
            "maxim_employee_profiles?"
            + urllib.parse.urlencode(
                {
                    "select": (
                        "id,billing_account,required_training,workflow_stage,"
                        "status_detail,prior_class_date,expiration_date,"
                        "prior_ecard_code,ecard_detected_at,scheduled_class_date,"
                        "current_external_registration_id,"
                        "customers(first_name,last_name,email)"
                    ),
                    "active": "eq.true",
                    "order": "id",
                }
            )
        )
        history = self.request(
            "maxim_certification_history?"
            + urllib.parse.urlencode(
                {
                    "select": (
                        "id,employee_profile_id,ecard_number,course,issue_date,"
                        "expiration_date,certification_status,source_drive_file_id,"
                        "source_filename,source_occurrences"
                    ),
                    "order": "issue_date.desc.nullslast,expiration_date.desc.nullslast",
                }
            )
        )
        return {"profiles": profiles or [], "history": history or []}
