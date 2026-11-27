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


def configured_calendar_ownership(calendar_payload, scheduler_people, policy):
    """Exact logical owner keys, never display/email aliases.

    Compute required sources from the entire configuration, before observing
    exports. Duplicate source keys deny coverage for all involved owners.
    """
    owners = policy.get("calendar_owner_person_ids")
    if not isinstance(owners, dict) or not isinstance(calendar_payload, dict):
        return {}, {}
    sources = calendar_payload.get("calendar_sources")
    if not isinstance(sources, list):
        return {}, {}
    stable = unique_scheduler_ids(scheduler_people)
    valid = {key: value for key, value in owners.items()
             if isinstance(key, str) and key and isinstance(value, str) and value in stable}
    bind = policy.get("calendar_source_owners")
    if not isinstance(bind, dict):
        return {}, {}
    declared = {key: value for key, value in bind.items()
                if isinstance(key, str) and key and key == key.strip()
                and isinstance(value, str) and value in stable}
    occurrences = Counter()
    required = defaultdict(set)
    observed = {}
    invalid = set()
    for item in sources:
        if not isinstance(item, dict):
            continue
        key = item.get("calendar_source_key")
        owner_key = item.get("owner_instructor_key")
        pid = valid.get(owner_key) if isinstance(owner_key, str) else None
        if isinstance(key, str) and key and key == key.strip():
            occurrences[key] += 1
            if pid:
                required[pid].add(key)
                if declared.get(key) == pid:
                    observed[key] = pid
                else:
                    invalid.add(pid)
        elif pid:
            invalid.add(pid)
    for key, pid in declared.items():
        required[pid].add(key)
        if occurrences[key] != 1 or observed.get(key) != pid:
            invalid.add(pid)
    invalid.update(pid for pid, keys in required.items()
                   if any(occurrences[key] != 1 for key in keys))
    # A validated source can still establish occupancy without fresh coverage
    # of the other configured sources needed to open that owner's windows.
    source_owners = {key: pid for key, pid in observed.items() if occurrences[key] == 1}
    return source_owners, {pid: frozenset(keys) for pid, keys in required.items()
                           if keys and pid not in invalid}


def calendar_block_person_id(row, source_owners):
    key, pid = row.get("source_calendar_id"), row.get("person_id")
    return pid if isinstance(key, str) and isinstance(pid, str) and source_owners.get(key) == pid else None


def valid_owned_coverage(proof, required_sources):
    pid, keys = proof.get("instructor_person_id"), proof.get("source_ids")
    if (not isinstance(pid, str) or not isinstance(keys, list)
            or not all(isinstance(k, str) for k in keys)
            or len(set(keys)) != len(keys)
            or proof.get("source") != "configured_calendar_exports"):
        return False
    return bool(pid in required_sources and set(keys) == required_sources[pid])
