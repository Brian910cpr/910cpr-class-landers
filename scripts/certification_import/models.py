from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SourceFile:
    id: str
    name: str
    modified_at: str | None
    mime_type: str
    size: int | None = None
    md5_checksum: str | None = None
    local_path: str | None = None


@dataclass
class NormalizedCertification:
    source_file_id: str
    source_file_name: str
    source_file_modified_at: str | None
    source_file_sha256: str
    source_sheet: str
    source_row: int
    participant_name_raw: str
    first_name: str
    last_name: str
    normalized_name: str
    email: str | None
    course_name_raw: str
    normalized_course: str
    ecard_code: str
    class_date: str | None
    issue_date: str | None
    expiration_date: str | None
    corporate_customer: str | None
    raw_record: dict[str, Any]
    record_fingerprint: str = ""
    identity_fingerprint: str = ""
    validation_errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MatchResult:
    status: str
    employee_profile_id: str | None = None
    method: str | None = None
    confidence: float | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    suggested_employee_profile_id: str | None = None


@dataclass
class ReconciledRecord:
    certification: NormalizedCertification
    match: MatchResult
    duplicate_of: str | None = None
    proposed_history_insert: dict[str, Any] | None = None
    proposed_profile_update: dict[str, Any] | None = None
    skip_reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "certification": self.certification.as_dict(),
            "match": asdict(self.match),
            "duplicate_of": self.duplicate_of,
            "proposed_history_insert": self.proposed_history_insert,
            "proposed_profile_update": self.proposed_profile_update,
            "skip_reasons": self.skip_reasons,
        }
