#!/usr/bin/env python3
"""Hx-Builder: source-agnostic historical ingestion planner.

Only dry-run mode exists. The worker emits proposed canonical operations and
append-only evidence assertions; it never connects to or mutates production.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from import_enrollware_registration_events import UNKNOWN, import_events, read_json


REPORT_FIELDS = (
    "source_records_examined",
    "people_matched",
    "people_created",
    "sessions_matched",
    "sessions_created",
    "registrations_matched",
    "registrations_created",
    "reschedules_reconstructed",
    "completions_reconstructed",
    "credentials_cards_reconstructed",
    "unresolved_identities",
    "ambiguous_conflicting_facts",
    "duplicate_candidates",
    "records_intentionally_excluded",
)

SOURCE_FINGERPRINT_ALGORITHM = "sha256-canonical-json-v1"


def text(value: Any) -> str:
    return str(value or "").strip()


def email(value: Any) -> str:
    return text(value).lower()


def phone(value: Any) -> str:
    return "".join(c for c in text(value) if c.isdigit())


def stable_key(*parts: Any) -> str:
    raw = "|".join(text(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def source_fingerprint(record: dict[str, Any]) -> str:
    raw = json.dumps(record.get("raw", record), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def known(value: Any) -> bool:
    return value not in (None, "", [], {}, UNKNOWN, "unknown", "UNKNOWN")


def date_part(value: Any) -> str:
    raw = text(value)
    return raw[:10] if len(raw) >= 10 else "unknown"


def parse_timestamp(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(text(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo is not None else None


def canonical_record(record: dict[str, Any], source: str) -> dict[str, Any]:
    person = record.get("person") or {}
    session = record.get("session") or {}
    registration = record.get("registration") or {}
    facts = record.get("facts") or {}
    return {
        **record,
        "source": text(record.get("source") or source),
        "source_record_id": text(record.get("source_record_id")),
        "person": person,
        "session": session,
        "registration": registration,
        "facts": facts,
        "confidence_state": text(record.get("confidence_state") or "unknown"),
        "confidence": record.get("confidence"),
        "source_created_at": record.get("source_created_at"),
        "observed_at": record.get("observed_at"),
        "raw": record.get("raw", record),
    }


def adapt_enrollware_csv(path: Path, seeds_path: Path) -> dict[str, Any]:
    seeds, error = read_json(seeds_path)
    if error:
        raise ValueError(f"could not read Enrollware seed reference: {error}")
    imported = import_events(path, seeds)
    records = []
    for event in imported["normalized_events"]:
        if event["regId"] == UNKNOWN:
            source_id = event["event_id"]
        else:
            source_id = event["regId"]
        first = event.get("firstName")
        last = event.get("lastName")
        if first == UNKNOWN and event.get("student") not in (None, UNKNOWN):
            pieces = text(event["student"]).split(None, 1)
            first, last = pieces[0], pieces[1] if len(pieces) > 1 else "Unknown"
        facts: dict[str, Any] = {}
        if known(event.get("payments")) or known(event.get("balanceDue")):
            facts["payment"] = {
                "details": event.get("payments"),
                "balance_due": event.get("balanceDue"),
                "state": "unknown",
            }
        if known(event.get("options")):
            facts["products"] = [{"description": event["options"], "fulfillment_state": "unknown"}]
        # Registration status is not evidence of attendance or completion.
        records.append({
            "source": "enrollware",
            "source_record_id": source_id,
            "source_created_at": event.get("receivedAt"),
            "observed_at": event.get("importedAt"),
            "confidence_state": "confirmed" if not event.get("warnings") else "possible",
            "person": {
                "source_id": event.get("corporate_account_preview", {}).get("possible_person_key"),
                "first_name": None if first == UNKNOWN else first,
                "last_name": None if last == UNKNOWN else last,
                "email": None if event.get("emailAddress") == UNKNOWN else event.get("emailAddress"),
                "phone": None if event.get("phoneNumber") == UNKNOWN else event.get("phoneNumber"),
            },
            "session": {
                "source_id": None if event.get("courseSchedId") == UNKNOWN else event.get("courseSchedId"),
                "course_source_id": None if event.get("courseId") == UNKNOWN else event.get("courseId"),
                "course_name": None if event.get("courseName") == UNKNOWN else event.get("courseName"),
                "start_at": None if event.get("startTime") == UNKNOWN else event.get("startTime"),
                "location_name": None if event.get("locationName") == UNKNOWN else event.get("locationName"),
            },
            "registration": {
                "source_id": None if event.get("regId") == UNKNOWN else event.get("regId"),
                "status": None if event.get("status") == UNKNOWN else event.get("status"),
            },
            "facts": facts,
            "exclude_reason": "missing canonical source identifiers" if event.get("missing_identifiers") else None,
            "raw": event.get("raw", event),
        })
    return {
        "batch": {
            "batch_key": f"enrollware:{stable_key(path.resolve(), path.stat().st_size)}",
            "source": "enrollware",
            "source_file_id": str(path.resolve()),
            "parser_version": "hx-builder-enrollware-v1",
            "created_at": datetime.now().astimezone().isoformat(),
        },
        "records": records,
        "adapter_summary": imported["summary"],
    }


class HxBuilder:
    def __init__(self, payload: dict[str, Any], reference: dict[str, Any]):
        self.payload = payload
        self.reference = reference
        self.batch = payload.get("batch") or {}
        self.counts = Counter({field: 0 for field in REPORT_FIELDS})
        self.operations: list[dict[str, Any]] = []
        self.decisions: list[dict[str, Any]] = []
        self.assertions: list[dict[str, Any]] = []
        self.duplicates: list[dict[str, Any]] = []
        self.ambiguities: list[dict[str, Any]] = []
        self.exclusions: list[dict[str, Any]] = []
        self.totals: dict[tuple[str, str, str], Counter[str]] = defaultdict(Counter)
        self.seen_source_records: set[tuple[str, str]] = set()
        self.seen_people: set[str] = set()
        self.seen_sessions: set[str] = set()
        self.seen_registrations: set[str] = set()
        self.proposed_identity_ids: dict[tuple[str, str], str] = {}
        self.proposed_session_ids: dict[tuple[str, str], str] = {}

        self.customers = reference.get("customers", [])
        self.aliases = {
            (text(a.get("source")), text(a.get("source_record_id") or a.get("source_identity"))): a
            for a in reference.get("identity_aliases", reference.get("aliases", []))
        }
        self.sessions = reference.get("sessions", [])
        self.source_sessions = reference.get("source_sessions", [])
        self.registrations = reference.get("registrations", [])
        self.import_records: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for import_record in reference.get("import_records", []):
            key = (
                text(import_record.get("source_system") or import_record.get("source")),
                text(import_record.get("source_record_id")),
                text(import_record.get("entity_type") or "registration"),
            )
            self.import_records[key].append(import_record)
        self.inventory_pools = {
            text(pool.get("pool_key")): pool for pool in reference.get("inventory_entitlement_pools", [])
        }
        self.organizations = reference.get("organizations", [])
        self.products = reference.get("products", [])
        self.product_aliases = reference.get("product_aliases", [])
        self.courses = reference.get("courses", [])
        self.course_aliases = reference.get("course_aliases", [])
        self.locations = reference.get("locations", [])
        self.location_aliases = reference.get("location_aliases", [])
        self.people = reference.get("people", [])
        self.instructor_aliases = reference.get("instructor_aliases", [])
        self.canonicalization = Counter()

    def canonicalize_session(self, record: dict[str, Any]) -> bool:
        """Resolve session facts by durable IDs or exact curated aliases only."""
        session, raw = record["session"], record.get("raw") or {}
        source_course = text(session.get("course_name"))
        source_location = text(session.get("location_name"))
        source_instructor = text(session.get("instructor_name") or raw.get("Instructor"))
        source_duration = text(session.get("duration_hours") or raw.get("Hours"))
        provenance = session.setdefault("source_values", {})
        provenance.update({"course": source_course, "location": source_location,
                           "lead_instructor": source_instructor, "duration_hours": source_duration,
                           "start_at": session.get("start_at")})

        def resolve(kind: str, value: str, rows: list[dict[str, Any]], aliases: list[dict[str, Any]],
                    id_field: str, name_field: str, hash_field: str | None = None) -> str | None:
            if not value:
                self.ambiguities.append({"kind": f"session_{kind}", "source_record_id": record["source_record_id"],
                                         "source_value": value, "reason": f"missing {kind}", "action": "manual_review"})
                return None
            alias_matches = [a for a in aliases if a.get("active") is not False
                             and text(a.get("review_status") or "approved_legacy") in ("reviewed", "approved_legacy")
                             and text(a.get("source")) in ("", record["source"])
                             and (text(a.get("source_label")) == value or text(a.get("source_value")) == value
                                  or (hash_field and text(a.get(hash_field)) == hashlib.sha256(value.encode()).hexdigest()))]
            ids = {text(a.get(id_field)) for a in alias_matches if text(a.get(id_field))}
            direct = [r for r in rows if text(r.get(name_field)) == value]
            ids.update(text(r.get("id")) for r in direct)
            if len(ids) == 1:
                self.canonicalization[f"{kind}_resolved"] += 1
                return next(iter(ids))
            self.ambiguities.append({"kind": f"session_{kind}", "source_record_id": record["source_record_id"],
                                     "source_value": value, "candidate_ids": sorted(ids),
                                     "reason": "canonical match must be a unique exact name/source alias",
                                     "action": "manual_review"})
            return None

        session["course_id"] = session.get("course_id") or resolve(
            "course", source_course, self.courses, self.course_aliases, "course_id", "name", "source_label_sha256")
        session["location_id"] = session.get("location_id") or resolve(
            "location", source_location, self.locations, self.location_aliases, "location_id", "name")
        session["lead_instructor_id"] = session.get("lead_instructor_id") or resolve(
            "instructor", source_instructor, self.people, self.instructor_aliases, "person_id", "display_name")

        start = parse_timestamp(session.get("start_at"))
        if start:
            self.canonicalization["start_at_resolved"] += 1
        else:
            self.ambiguities.append({"kind": "session_start_at", "source_record_id": record["source_record_id"],
                                     "source_value": session.get("start_at"), "reason": "missing or malformed timezone-aware start",
                                     "action": "manual_review"})
        end = parse_timestamp(session.get("end_at"))
        duration_hours = None
        if source_duration:
            try:
                duration_hours = float(source_duration)
            except ValueError:
                pass
        if end and start and end > start:
            self.canonicalization["end_at_resolved"] += 1
        elif start and duration_hours and 0 < duration_hours <= 24:
            session["end_at"] = (start + timedelta(hours=duration_hours)).isoformat()
            session["duration_minutes"] = round(duration_hours * 60)
            session["end_at_resolution"] = "source_duration"
            self.canonicalization["end_at_resolved"] += 1
        else:
            self.ambiguities.append({"kind": "session_end_at", "source_record_id": record["source_record_id"],
                                     "source_value": source_duration, "reason": "missing, malformed, or implausible end/duration",
                                     "action": "manual_review"})
        ready = all(known(session.get(k)) for k in
                    ("course_id", "location_id", "lead_instructor_id", "start_at", "end_at")) and bool(start)
        session["canonical_ready"] = ready
        self.canonicalization["sessions_ready" if ready else "sessions_review_required"] += 1
        return ready

    def assertion(self, record: dict[str, Any], fact_type: str, value: Any, **links: Any) -> dict[str, Any]:
        key = f"{record['source']}:{record['source_record_id']}:{fact_type}:{stable_key(value)}"
        assertion = {
            "assertion_key": key,
            "fact_type": fact_type,
            "source": record["source"],
            "source_record_id": record["source_record_id"],
            "import_batch_id": self.batch.get("batch_key"),
            "asserted_value": value,
            "original_source_value": record["raw"],
            "confidence_state": record["confidence_state"],
            "confidence": record.get("confidence"),
            "source_created_at": record.get("source_created_at"),
            "observed_at": record.get("observed_at"),
            "reconciliation_status": "unreviewed",
            **{k: v for k, v in links.items() if v is not None},
        }
        self.assertions.append(assertion)
        return assertion

    def resolve_person(self, record: dict[str, Any]) -> tuple[str | None, str]:
        person = record["person"]
        source_id = text(person.get("source_id"))
        alias = self.aliases.get((record["source"], source_id)) if source_id else None
        if alias:
            if alias.get("resolution_status") == "matched":
                return text(alias.get("customer_id")), "matched_alias"
            return None, "ambiguous_alias"

        email_value, phone_value = email(person.get("email")), phone(person.get("phone"))
        email_hash = text(person.get("email_hash")) or (hashlib.sha256(email_value.encode()).hexdigest() if email_value else "")
        phone_hash = text(person.get("phone_hash")) or (hashlib.sha256(phone_value.encode()).hexdigest() if phone_value else "")
        batch_keys = [key for key in (("email", email_value), ("phone", phone_value)) if key[1]]
        proposed = {self.proposed_identity_ids[key] for key in batch_keys if key in self.proposed_identity_ids}
        if len(proposed) == 1:
            return next(iter(proposed)), "matched_batch_identity"
        if len(proposed) > 1:
            self.ambiguities.append({
                "source": record["source"], "source_record_id": record["source_record_id"],
                "kind": "identity", "candidate_customer_ids": sorted(proposed),
            })
            return None, "ambiguous"
        email_ids = {
            text(c["id"]) for c in self.customers
            if email_value and (email(c.get("email")) == email_value or text(c.get("email_hash")) == email_hash)
        }
        phone_ids = {
            text(c["id"]) for c in self.customers
            if phone_value and (phone(c.get("phone")) == phone_value or text(c.get("phone_hash")) == phone_hash)
        }
        candidates = email_ids | phone_ids
        if (email_ids and phone_ids and email_ids != phone_ids) or len(candidates) > 1:
            self.ambiguities.append({
                "source": record["source"],
                "source_record_id": record["source_record_id"],
                "kind": "identity",
                "candidate_customer_ids": sorted(candidates),
            })
            return None, "ambiguous"
        if len(candidates) == 1:
            return next(iter(candidates)), "matched_exact"
        if not known(person.get("first_name")) or not known(person.get("last_name")):
            return None, "unresolved"
        proposed_id = f"proposed-customer:{stable_key(record['source'], source_id or email_value or phone_value or record['source_record_id'])}"
        for key in batch_keys:
            self.proposed_identity_ids[key] = proposed_id
        return proposed_id, "created"

    def resolve_session(self, record: dict[str, Any]) -> tuple[str | None, str]:
        session = record["session"]
        source_id = text(session.get("source_id"))
        batch_key = (record["source"], source_id)
        if source_id and batch_key in self.proposed_session_ids:
            return self.proposed_session_ids[batch_key], "matched_batch_session"
        matches = [
            s for s in self.sessions
            if (
                text(s.get("source")) == record["source"]
                and text(s.get("source_record_id") or s.get("external_class_id")) == source_id
            )
        ]
        if len(matches) > 1:
            self.duplicates.append({
                "kind": "session",
                "source": record["source"],
                "source_record_id": source_id,
                "candidate_ids": [text(s.get("id")) for s in matches],
            })
            return None, "duplicate_candidate"
        if len(matches) == 1:
            return text(matches[0]["id"]), "matched"
        if not self.canonicalize_session(record):
            return None, "review_required"
        required = (
            source_id,
            session.get("course_source_id") or session.get("course_id") or session.get("course_name"),
            session.get("start_at"),
        )
        if not all(known(v) for v in required):
            return None, "unresolved"
        proposed_id = f"proposed-session:{stable_key(record['source'], source_id)}"
        self.proposed_session_ids[batch_key] = proposed_id
        return proposed_id, "created"

    def resolve_registration(
        self, record: dict[str, Any], customer_id: str, session_id: str
    ) -> tuple[str, str]:
        source_registration_id = text(record["registration"].get("source_id"))
        external = [
            r for r in self.registrations
            if text(r.get("registration_source")) == record["source"]
            and text(r.get("external_registration_id")) == source_registration_id
            and source_registration_id
        ]
        membership = [
            r for r in self.registrations
            if text(r.get("customer_id")) == customer_id
            and text(r.get("class_session_id")) == session_id
        ]
        matches = {text(r["id"]): r for r in external + membership}
        if len(matches) > 1:
            self.duplicates.append({
                "kind": "registration",
                "source": record["source"],
                "source_record_id": record["source_record_id"],
                "candidate_ids": sorted(matches),
            })
            return sorted(matches)[0], "duplicate_candidate"
        if matches:
            return next(iter(matches)), "matched"
        return f"proposed-registration:{stable_key(customer_id, session_id)}", "created"

    def add_facts(
        self, record: dict[str, Any], customer_id: str, session_id: str, registration_id: str
    ) -> dict[str, int]:
        facts = record["facts"]
        added = Counter()
        if known(facts.get("attendance")):
            self.assertion(record, "attendance", facts["attendance"],
                           customer_id=customer_id, registration_id=registration_id, class_session_id=session_id)
            added["attendance"] += 1
        if known(facts.get("completion")):
            completion = facts["completion"]
            if isinstance(completion, dict) and text(completion.get("status")) in ("passed", "failed", "incomplete"):
                self.assertion(record, "completion", completion,
                               customer_id=customer_id, registration_id=registration_id, class_session_id=session_id)
                self.operations.append({"command": "propose_completion", "registration_id": registration_id,
                                        "source": record["source"], "source_record_id": record["source_record_id"],
                                        "value": completion})
                self.counts["completions_reconstructed"] += 1
                added["completion"] += 1
            else:
                self.ambiguities.append({"kind": "completion", "source_record_id": record["source_record_id"],
                                         "reason": "completion lacks explicit passed/failed/incomplete evidence"})
        if known(facts.get("credential")):
            credential = facts["credential"]
            if isinstance(credential, dict) and (
                known(credential.get("credential_number")) or known(credential.get("issued_at"))
            ):
                self.assertion(record, "credential", credential,
                               customer_id=customer_id, registration_id=registration_id, class_session_id=session_id)
                self.operations.append({"command": "propose_credential", "registration_id": registration_id,
                                        "source": record["source"], "source_record_id": record["source_record_id"],
                                        "value": credential})
                self.counts["credentials_cards_reconstructed"] += 1
                added["credential"] += 1
            else:
                self.ambiguities.append({"kind": "credential", "source_record_id": record["source_record_id"],
                                         "reason": "credential lacks number or issuance timestamp"})
        for kind in ("payment", "products", "requirements"):
            if known(facts.get(kind)):
                fact_type = {"products": "product_fulfillment", "requirements": "requirement"}.get(kind, kind)
                self.assertion(record, fact_type, facts[kind],
                               customer_id=customer_id, registration_id=registration_id, class_session_id=session_id)
                added[fact_type] += 1
        inventory = facts.get("inventory_entitlement")
        if known(inventory):
            if not isinstance(inventory, dict):
                self.ambiguities.append({"kind": "inventory_entitlement", "source_record_id": record["source_record_id"],
                                         "reason": "inventory evidence is not an object", "action": "manual_review"})
                return dict(added)
            owner_kind = text(inventory.get("owner_kind"))
            owner_reference = inventory.get("owner_reference") or {}
            requested_pool_key = text(inventory.get("pool_key"))
            existing_pool = self.inventory_pools.get(requested_pool_key) if requested_pool_key else None
            if existing_pool:
                pool_key = requested_pool_key
                pool_id = text(existing_pool.get("id"))
                quantity = inventory.get("quantity_delta")
                event = {
                    "command": "propose_inventory_entitlement_event", "pool_key": pool_key, "pool_id": pool_id,
                    "quantity_delta": quantity, "event_type": inventory.get("event_type", "consumed"),
                    "customer_id": customer_id, "registration_id": registration_id, "class_session_id": session_id,
                    "source": record["source"], "source_record_id": record["source_record_id"],
                    "import_batch_id": self.batch.get("batch_key"),
                }
                if isinstance(quantity, int) and quantity != 0:
                    self.operations.append(event)
                    self.assertion(record, "inventory_entitlement", inventory, customer_id=customer_id,
                                   registration_id=registration_id, class_session_id=session_id)
                    added["inventory_entitlement"] += 1
                else:
                    self.ambiguities.append({"kind": "inventory_entitlement", "source_record_id": record["source_record_id"],
                                             "reason": "non-zero integer quantity_delta is required", "action": "manual_review"})
                return dict(added)
            organization_id = text(inventory.get("owner_organization_id"))
            if owner_kind == "organization" and not organization_id:
                organization_key = text(owner_reference.get("organization_key"))
                owner_matches = [o for o in self.organizations if text(o.get("organization_key")) == organization_key]
                if len(owner_matches) != 1:
                    self.ambiguities.append({"kind": "inventory_owner", "source_record_id": record["source_record_id"],
                                             "reference": owner_reference, "candidate_ids": [text(o.get("id")) for o in owner_matches],
                                             "reason": "canonical organization match must be unique", "action": "manual_review"})
                    return dict(added)
                organization_id = text(owner_matches[0].get("id"))
            product_id = text(inventory.get("product_id"))
            product_reference = inventory.get("product_reference") or {}
            if not product_id:
                product_key = text(product_reference.get("product_key"))
                source_option = text(product_reference.get("source_option"))
                alias_keys = {
                    text(a.get("product_key")) for a in self.product_aliases
                    if text(a.get("source")) == record["source"] and text(a.get("source_value")) == source_option
                }
                product_matches = [p for p in self.products if
                                   (product_key and text(p.get("product_key")) == product_key)
                                   or text(p.get("product_key")) in alias_keys]
                if len(product_matches) != 1:
                    self.ambiguities.append({"kind": "inventory_product", "source_record_id": record["source_record_id"],
                                             "reference": product_reference, "candidate_ids": [text(p.get("id")) for p in product_matches],
                                             "reason": "canonical product match must be unique", "action": "manual_review"})
                    return dict(added)
                product_id = text(product_matches[0].get("id"))
            unit_kind = text(inventory.get("unit_kind"))
            pool_key = requested_pool_key or stable_key(owner_kind, organization_id, product_id, unit_kind)
            quantity = inventory.get("quantity_delta") if isinstance(inventory, dict) else None
            if pool_key and isinstance(quantity, int) and quantity != 0:
                pool = self.inventory_pools.get(pool_key)
                pool_id = text(pool.get("id")) if pool else ""
                if not pool:
                    if owner_kind and product_id:
                        pool_id = f"proposed-pool:{stable_key(pool_key)}"
                        self.operations.append({
                            "command": "propose_inventory_entitlement_pool",
                            "proposed_pool_id": pool_id,
                            "pool_key": pool_key,
                            "owner_kind": owner_kind,
                            "owner_customer_id": customer_id if owner_kind == "customer" else None,
                            "owner_organization_id": organization_id or None,
                            "product_id": product_id,
                            "unit_kind": inventory.get("unit_kind"),
                            "source": record["source"],
                            "source_record_id": record["source_record_id"],
                            "import_batch_id": self.batch.get("batch_key"),
                        })
                        self.inventory_pools[pool_key] = {"id": pool_id, "pool_key": pool_key}
                    else:
                        self.ambiguities.append({
                            "kind": "inventory_entitlement",
                            "source_record_id": record["source_record_id"],
                            "reason": "unknown pool requires owner_kind and product_id",
                        })
                        return dict(added)
                event = {
                    "command": "propose_inventory_entitlement_event",
                    "pool_key": pool_key,
                    "pool_id": pool_id,
                    "quantity_delta": quantity,
                    "event_type": inventory.get("event_type", "consumed"),
                    "customer_id": customer_id,
                    "registration_id": registration_id,
                    "class_session_id": session_id,
                    "source": record["source"],
                    "source_record_id": record["source_record_id"],
                    "import_batch_id": self.batch.get("batch_key"),
                }
                self.operations.append(event)
                self.assertion(record, "inventory_entitlement", inventory,
                               customer_id=customer_id, registration_id=registration_id, class_session_id=session_id)
                added["inventory_entitlement"] += 1
            else:
                self.ambiguities.append({"kind": "inventory_entitlement",
                                         "source_record_id": record["source_record_id"],
                                         "reason": "pool_key and non-zero integer quantity_delta are required"})
        return dict(added)

    def process(self) -> dict[str, Any]:
        records = [canonical_record(r, text(self.batch.get("source") or "unknown"))
                   for r in self.payload.get("records", [])]
        self.counts["source_records_examined"] = len(records)
        for record in records:
            source_key = (record["source"], record["source_record_id"])
            bucket = (
                text(record["session"].get("course_name") or record["session"].get("course_source_id") or "unknown"),
                date_part(record["session"].get("start_at")),
                record["source"],
            )
            self.totals[bucket]["examined"] += 1
            decision = {"source": record["source"], "source_record_id": record["source_record_id"]}

            for item in record.get("review_items") or []:
                self.ambiguities.append({**decision, **item, "action": "manual_review"})

            if not record["source_record_id"] or record.get("exclude_reason"):
                reason = text(record.get("exclude_reason") or "missing source_record_id")
                self.exclusions.append({**decision, "reason": reason})
                self.counts["records_intentionally_excluded"] += 1
                self.totals[bucket]["excluded"] += 1
                continue
            if source_key in self.seen_source_records:
                self.duplicates.append({**decision, "kind": "source_record_replay"})
                self.counts["duplicate_candidates"] += 1
                self.totals[bucket]["duplicates"] += 1
                continue
            self.seen_source_records.add(source_key)

            fingerprint = source_fingerprint(record)
            priors = self.import_records.get((record["source"], record["source_record_id"], "registration"), [])
            exact_prior = next((r for r in priors if
                                text(r.get("source_fingerprint_algorithm")) == SOURCE_FINGERPRINT_ALGORITHM
                                and text(r.get("source_fingerprint")) == fingerprint), None)
            if exact_prior:
                decision["source_record_resolution"] = "matched"
                decision["import_record_id"] = exact_prior.get("id")
                decision["action"] = "idempotent_replay"
                self.decisions.append(decision)
                self.totals[bucket]["idempotent_replay"] += 1
                continue
            if priors:
                self.operations.append({
                    "command": "propose_import_record",
                    "source": record["source"], "source_system": record["source"],
                    "source_record_id": record["source_record_id"], "entity_type": "registration",
                    "import_batch_id": self.batch.get("batch_key"), "original_values": record["raw"],
                    "source_fingerprint": fingerprint,
                    "source_fingerprint_algorithm": SOURCE_FINGERPRINT_ALGORITHM,
                    "reconciliation_status": "ambiguous",
                    "conflicts_with_import_record_ids": [r.get("id") for r in priors],
                    "predecessor_import_record_id": priors[0].get("id") if len(priors) == 1 else None,
                })
                self.ambiguities.append({
                    **decision,
                    "kind": "source_record_conflict",
                    "prior_import_record_ids": [r.get("id") for r in priors],
                    "reason": "source_record_id was previously seen with a different fingerprint",
                    "action": "manual_review",
                })
                decision["source_record_resolution"] = "conflicting_version"
                decision["action"] = "review"
                self.decisions.append(decision)
                self.totals[bucket]["conflicting"] += 1
                continue
            else:
                decision["source_record_resolution"] = "created"
                self.operations.append({
                    "command": "propose_import_record",
                    "source": record["source"],
                    "source_system": record["source"],
                    "source_record_id": record["source_record_id"],
                    "import_batch_id": self.batch.get("batch_key"),
                    "original_values": record["raw"],
                    "source_fingerprint": source_fingerprint(record),
                    "source_fingerprint_algorithm": SOURCE_FINGERPRINT_ALGORITHM,
                })

            customer_id, person_state = self.resolve_person(record)
            decision["person_resolution"] = person_state
            if person_state.startswith("matched"):
                if customer_id not in self.seen_people:
                    self.counts["people_matched"] += 1
                    self.seen_people.add(customer_id or "")
            elif person_state == "created":
                if customer_id not in self.seen_people:
                    self.counts["people_created"] += 1
                    self.seen_people.add(customer_id or "")
                self.operations.append({"command": "register_participant_identity",
                                        "proposed_customer_id": customer_id, "person": record["person"],
                                        "source": record["source"], "source_record_id": record["source_record_id"]})
            else:
                self.counts["unresolved_identities"] += 1
                self.totals[bucket]["unresolved"] += 1
                decision["action"] = "review"
                self.decisions.append(decision)
                continue

            session_id, session_state = self.resolve_session(record)
            decision["session_resolution"] = session_state
            if session_state.startswith("matched"):
                if session_id not in self.seen_sessions:
                    self.counts["sessions_matched"] += 1
                    self.seen_sessions.add(session_id or "")
            elif session_state == "created":
                if session_id not in self.seen_sessions:
                    self.counts["sessions_created"] += 1
                    self.seen_sessions.add(session_id or "")
                self.operations.append({"command": "propose_session", "proposed_session_id": session_id,
                                        "session": record["session"], "source": record["source"],
                                        "source_record_id": record["source_record_id"]})
            else:
                self.totals[bucket]["unresolved"] += 1
                decision["action"] = "review"
                self.decisions.append(decision)
                continue

            registration_id, registration_state = self.resolve_registration(record, customer_id, session_id)
            decision["registration_resolution"] = registration_state
            if registration_state == "matched":
                if registration_id not in self.seen_registrations:
                    self.counts["registrations_matched"] += 1
                    self.seen_registrations.add(registration_id)
            elif registration_state == "created":
                if registration_id not in self.seen_registrations:
                    self.counts["registrations_created"] += 1
                    self.seen_registrations.add(registration_id)
                self.operations.append({
                    "command": "register_participant",
                    "idempotency_key": f"hx:{record['source']}:{record['source_record_id']}",
                    "customer_id": customer_id,
                    "class_session_id": session_id,
                    "source": record["source"],
                    "external_registration_id": record["registration"].get("source_id"),
                    "import_batch_id": self.batch.get("batch_key"),
                })
            else:
                self.counts["duplicate_candidates"] += 1

            reschedule = record.get("reschedule")
            if isinstance(reschedule, dict) and known(reschedule.get("from_session_source_id")):
                origin = [
                    s for s in self.sessions + self.source_sessions
                    if text(s.get("source")) == record["source"]
                    and text(s.get("source_record_id") or s.get("external_class_id"))
                    == text(reschedule["from_session_source_id"])
                ]
                if len(origin) == 1 and known(reschedule.get("reason")):
                    self.operations.append({
                        "command": "move_registration",
                        "idempotency_key": f"hx-move:{record['source']}:{record['source_record_id']}",
                        "customer_id": customer_id,
                        "source_session_id": origin[0]["id"],
                        "target_session_id": session_id,
                        "reason": reschedule["reason"],
                        "source": record["source"],
                        "occurred_at": reschedule.get("occurred_at"),
                        "import_batch_id": self.batch.get("batch_key"),
                    })
                    self.assertion(record, "reschedule", reschedule, customer_id=customer_id,
                                   registration_id=registration_id, class_session_id=session_id)
                    self.counts["reschedules_reconstructed"] += 1
                else:
                    self.ambiguities.append({"kind": "reschedule", "source_record_id": record["source_record_id"],
                                             "reason": "origin session or move reason is unresolved"})

            decision["facts"] = self.add_facts(record, customer_id, session_id, registration_id)
            decision["action"] = "dry_run_only"
            self.decisions.append(decision)
            self.totals[bucket]["reconciled"] += 1

        self.counts["ambiguous_conflicting_facts"] = len(self.ambiguities)
        self.counts["duplicate_candidates"] = len(self.duplicates)
        totals = [
            {"course": course, "date": date, "source": source, **dict(counts)}
            for (course, date, source), counts in sorted(self.totals.items())
        ]
        return {
            "worker": "Hx-Builder",
            "mode": "dry_run",
            "mutation_performed": False,
            "authority": "customers -> registrations -> class_sessions",
            "batch": self.batch,
            "summary": {field: self.counts[field] for field in REPORT_FIELDS},
            "reconciliation_totals_by_course_date_source": totals,
            "decisions": self.decisions,
            "proposed_operations": self.operations,
            "evidence_assertions": self.assertions,
            "unresolved_or_ambiguous": self.ambiguities,
            "duplicate_candidates": self.duplicates,
            "records_intentionally_excluded": self.exclusions,
            "canonicalization_summary": dict(sorted(self.canonicalization.items())),
        }


def replay_reference(reference: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Return an in-memory reference overlay for deterministic dry-run replay tests."""
    overlay = json.loads(json.dumps(reference))
    rows = overlay.setdefault("import_records", [])
    known_keys = {
        (text(r.get("source_system") or r.get("source")), text(r.get("source_record_id")),
         text(r.get("entity_type") or "registration"), text(r.get("source_fingerprint_algorithm")),
         text(r.get("source_fingerprint")))
        for r in rows
    }
    for operation in report.get("proposed_operations", []):
        if operation.get("command") != "propose_import_record":
            continue
        key = (text(operation.get("source_system") or operation.get("source")),
               text(operation.get("source_record_id")), "registration",
               text(operation.get("source_fingerprint_algorithm")), text(operation.get("source_fingerprint")))
        if key in known_keys:
            continue
        rows.append({
            "id": f"dry-run-import:{stable_key(*key)}",
            "source": key[0],
            "source_system": key[0],
            "source_record_id": key[1], "entity_type": key[2],
            "source_fingerprint": operation.get("source_fingerprint"),
            "source_fingerprint_algorithm": operation.get("source_fingerprint_algorithm"),
            "reconciliation_status": "dry_run_overlay",
        })
        known_keys.add(key)
    return overlay


def load_payload(path: Path, adapter: str, seeds: Path) -> dict[str, Any]:
    if adapter == "enrollware-csv":
        return adapt_enrollware_csv(path, seeds)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise ValueError("canonical-json input requires an object with records[]")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan historical ingestion without mutation.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--adapter", choices=("canonical-json", "enrollware-csv"), default="canonical-json")
    parser.add_argument("--seeds", type=Path, default=Path("data/audit/schedule_seeds_preview.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = load_payload(args.input, args.adapter, args.seeds)
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    report = HxBuilder(payload, reference).process()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
