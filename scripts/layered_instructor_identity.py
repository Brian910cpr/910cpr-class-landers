"""Private V2 scheduler identity helpers. Never use a display label as proof."""
from collections import Counter, defaultdict
import re


def unique_scheduler_ids(people):
    counts = Counter(p.get("person_id") for p in people)
    return {pid for pid, count in counts.items() if isinstance(pid, str) and pid and count == 1}


def explicit_external_crosswalk(people, configured):
    """Return only unique, explicitly mapped active scheduler people."""
    if not isinstance(configured, dict):
        return {}
    unique_people = unique_scheduler_ids(people)
    candidates = defaultdict(set)
    for pid, external in configured.items():
        if (pid in unique_people
                and isinstance(external, str) and re.fullmatch(r"[1-9][0-9]{0,19}", external)):
            candidates[external].add(pid)
    # A contradictory configured row must prevent authorization even if the
    # second person is not available in the scheduler at this moment.
    references = Counter(x for x in configured.values() if isinstance(x, str))
    return {external: next(iter(ids)) for external, ids in candidates.items()
            if len(ids) == 1 and references[external] == 1}


def canonical_instructor_projection(row, crosswalk):
    proof = row.get("lead_instructor_identity")
    if not isinstance(proof, dict):
        return "unresolved", None
    state = proof.get("status")
    external = proof.get("catalog_external_id")
    stored = row.get("lead_instructor_id")
    if (state == "unassigned" and external is None and "lead_instructor_id" in row
            and stored is None and not row.get("lead_instructor_name")):
        return "unassigned", None
    if state == "verified" and isinstance(stored, str) and stored and isinstance(external, str):
        if person := crosswalk.get(external):
            return "verified", person
    return "unresolved", None


def same_proved_instructor(row, window):
    pid = row.get("effective_instructor_person_id")
    return bool(pid and pid == window.get("person_id"))


def strict_coverage_matches(proof, window):
    pid = proof.get("instructor_person_id")
    return bool(pid and pid == window.get("person_id"))
