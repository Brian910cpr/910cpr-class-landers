# Name Dependency Report

This build keeps legacy Course HTML parsing for backward compatibility, but mapping is authoritative for operational metadata.

- Course map: `E:\GitHub\910cpr-class-landers\data\config\course_map.json`
- Sessions written: `26002`
- Unmapped sessions: `2760`
- Mapping conflicts: `0`

## Phase 1 Rules

- Do not infer certifying body/family/delivery from display name when mapping is missing.
- Display text may come from cleaned course name.
- Operational fields must come from course map when available.
