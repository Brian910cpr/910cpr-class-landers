"""Deterministic, read-only QBO reconciliation audit engine."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "worker" / "migrations" / "0004_financial_reconciliation.sql"
CONFIDENCE = {"VERIFIED", "HIGH", "MEDIUM", "LOW", "UNKNOWN", "CONFLICTED"}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def stable_id(namespace: str, *parts: object) -> str:
    value = "|".join(str(part or "") for part in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"910cpr:{namespace}:{value}"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def normalize_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def amount_minor(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int((Decimal(str(value).replace(",", "").replace("$", "")) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except InvalidOperation as exc:
        raise ValueError(f"Invalid monetary amount: {value!r}") from exc


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(MIGRATION.read_text(encoding="utf-8"))


def records_from_payload(payload: Any, candidate_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = next((payload[key] for key in candidate_keys if isinstance(payload.get(key), list)), None)
        if records is None:
            records = [payload]
    else:
        raise ValueError("Input JSON must be an object or array")
    if not all(isinstance(record, dict) for record in records):
        raise ValueError("Every imported record must be a JSON object")
    return records


class AuditEngine:
    """Persist source evidence, derive exceptions, and never write to QBO."""

    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.row_factory = sqlite3.Row
        initialize_database(self.db)

    def _source_record(self, system: str, record_type: str, external_id: str, raw: dict[str, Any], reference: str) -> str:
        record_id = stable_id("source", system, record_type, external_id)
        payload = canonical_json(raw)
        stamp = now_iso()
        self.db.execute(
            """INSERT INTO financial_source_records
               (id,source_system,source_type,source_record_id,source_reference,observed_at,ingested_at,checksum_sha256,raw_payload_json)
               VALUES (?,?,?,?,?,?,?,?,?)
               ON CONFLICT(source_system,source_type,source_record_id) DO UPDATE SET
                 source_reference=excluded.source_reference, observed_at=excluded.observed_at,
                 ingested_at=excluded.ingested_at, checksum_sha256=excluded.checksum_sha256,
                 raw_payload_json=excluded.raw_payload_json""",
            (record_id, system, record_type, external_id, reference, raw.get("observed_at") or raw.get("last_updated"), stamp,
             hashlib.sha256(payload.encode("utf-8")).hexdigest(), payload),
        )
        return record_id

    def import_accounts(self, payload: Any, system: str = "qbo", reference: str = "") -> int:
        records = records_from_payload(payload, ("accounts", "Account", "items"))
        stamp = now_iso()
        for index, raw in enumerate(records):
            external_id = str(raw.get("id") or raw.get("Id") or raw.get("account_id") or f"row-{index}")
            source_id = self._source_record(system, "account", external_id, raw, reference)
            name = str(raw.get("name") or raw.get("Name") or raw.get("canonical_name") or "Unknown account").strip()
            account_type = str(raw.get("account_type") or raw.get("AccountType") or raw.get("type") or "unknown").strip().lower()
            qbo_id = external_id if system == "qbo" else raw.get("qbo_account_id")
            account_id = stable_id("account", system, external_id)
            last_four = raw.get("account_last_four") or raw.get("last_four")
            if last_four not in (None, ""):
                last_four = str(last_four)[-4:]
                if not (len(last_four) == 4 and last_four.isdigit()):
                    last_four = None
            self.db.execute(
                """INSERT INTO financial_accounts
                   (id,canonical_name,account_type,business_classification,qbo_account_id,bank_account_id,account_last_four,status,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET canonical_name=excluded.canonical_name,
                     account_type=excluded.account_type, business_classification=excluded.business_classification,
                     qbo_account_id=COALESCE(excluded.qbo_account_id,financial_accounts.qbo_account_id),
                     bank_account_id=COALESCE(excluded.bank_account_id,financial_accounts.bank_account_id),
                     account_last_four=COALESCE(excluded.account_last_four,financial_accounts.account_last_four),
                     status=excluded.status, updated_at=excluded.updated_at""",
                (account_id, name, account_type, raw.get("business_classification", "unknown"), qbo_id,
                 external_id if system in {"novo", "bank"} else raw.get("bank_account_id"), last_four,
                 str(raw.get("status") or "active").lower(), stamp, stamp),
            )
            self.db.execute(
                """INSERT OR REPLACE INTO financial_account_sources
                   (account_id,source_record_id,relationship_type,match_confidence,match_basis) VALUES (?,?,?,?,?)""",
                (account_id, source_id, "origin", "VERIFIED", "explicit source identity"),
            )
            for field in ("current_balance", "statement_balance", "minimum_payment", "due_date", "apr", "late_fee", "grace_period", "autopay_status", "recurring_payment_amount", "statement_period", "consequence_of_nonpayment"):
                if field in raw:
                    self._fact(account_id, field, raw[field], raw.get(f"{field}_confidence", raw.get("confidence", "HIGH")), source_id, raw.get("last_verified_at"))
        self.db.commit()
        return len(records)

    def _fact(self, account_id: str, field: str, value: Any, confidence: str, source_id: str | None, verified: str | None) -> None:
        confidence = str(confidence).upper()
        if confidence not in CONFIDENCE:
            confidence = "UNKNOWN"
        fact_id = stable_id("fact", account_id, field, source_id or "manual")
        self.db.execute("UPDATE financial_facts SET is_current=0 WHERE account_id=? AND field_name=? AND id<>?", (account_id, field, fact_id))
        self.db.execute(
            """INSERT INTO financial_facts
               (id,account_id,field_name,value_json,confidence,source_record_id,effective_at,last_verified_at,is_current,created_at)
               VALUES (?,?,?,?,?,?,?,?,1,?)
               ON CONFLICT(id) DO UPDATE SET value_json=excluded.value_json,confidence=excluded.confidence,
                 effective_at=excluded.effective_at,last_verified_at=excluded.last_verified_at,is_current=1""",
            (fact_id, account_id, field, canonical_json(value), confidence, source_id, verified, verified, now_iso()),
        )

    def import_transactions(self, payload: Any, system: str = "qbo", reference: str = "") -> int:
        records = records_from_payload(payload, ("transactions", "Transaction", "items"))
        stamp = now_iso()
        for index, raw in enumerate(records):
            external_id = str(raw.get("id") or raw.get("Id") or raw.get("transaction_id") or f"row-{index}")
            source_id = self._source_record(system, "transaction", external_id, raw, reference)
            qbo_account_id = str(raw.get("account_id") or raw.get("AccountId") or raw.get("account_ref") or "")
            row = self.db.execute("SELECT id FROM financial_accounts WHERE qbo_account_id=? OR bank_account_id=?", (qbo_account_id, qbo_account_id)).fetchone()
            account_id = row["id"] if row else None
            transaction_id = stable_id("transaction", system, external_id)
            self.db.execute(
                """INSERT INTO financial_transactions
                   (id,source_record_id,source_system,external_id,account_id,transaction_date,posted_at,amount_minor,currency,
                    transaction_type,payee,memo,category_name,category_type,transfer_account_id,raw_payload_json,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(source_system,external_id) DO UPDATE SET account_id=excluded.account_id,
                     transaction_date=excluded.transaction_date,posted_at=excluded.posted_at,amount_minor=excluded.amount_minor,
                     transaction_type=excluded.transaction_type,payee=excluded.payee,memo=excluded.memo,
                     category_name=excluded.category_name,category_type=excluded.category_type,
                     transfer_account_id=excluded.transfer_account_id,raw_payload_json=excluded.raw_payload_json""",
                (transaction_id, source_id, system, external_id, account_id, raw.get("date") or raw.get("TxnDate"),
                 raw.get("posted_at"), amount_minor(raw.get("amount") if "amount" in raw else raw.get("Amount")),
                 str(raw.get("currency") or "USD").upper(), str(raw.get("transaction_type") or raw.get("TxnType") or "").lower(),
                 raw.get("payee") or raw.get("EntityRef"), raw.get("memo") or raw.get("PrivateNote"),
                 raw.get("category_name") or raw.get("AccountRefName"), str(raw.get("category_type") or "").lower(),
                 raw.get("transfer_account_id"), canonical_json(raw), stamp),
            )
        self.db.commit()
        return len(records)

    def detect(self) -> list[dict[str, Any]]:
        self._detect_duplicate_accounts()
        self._detect_unmatched_transactions()
        self._detect_card_payments_as_expense()
        self._detect_transfer_like_income_expense()
        self._detect_missing_material_facts()
        self.db.commit()
        return self.exceptions()

    def _exception(self, code: str, severity: str, rank: int, evidence: dict[str, Any], cause: str,
                   correction: str, question: str = "", account_id: str | None = None,
                   transaction_id: str | None = None, impact: dict[str, Any] | None = None) -> None:
        evidence_json = canonical_json(evidence)
        exception_id = stable_id("exception", code, account_id, transaction_id, evidence_json)
        stamp = now_iso()
        self.db.execute(
            """INSERT INTO financial_reconciliation_exceptions
               (id,detector_code,status,severity,priority_rank,financial_impact_json,account_id,transaction_id,
                source_evidence_json,suspected_cause,safe_proposed_correction,user_clarification_required,
                smallest_user_question,first_detected_at,last_detected_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(id) DO UPDATE SET severity=excluded.severity,priority_rank=excluded.priority_rank,
                 financial_impact_json=excluded.financial_impact_json,last_detected_at=excluded.last_detected_at""",
            (exception_id, code, "open", severity, rank, canonical_json(impact or {}), account_id, transaction_id,
             evidence_json, cause, correction, int(bool(question)), question or None, stamp, stamp),
        )

    def _detect_duplicate_accounts(self) -> None:
        rows = self.db.execute("SELECT * FROM financial_accounts WHERE status='active' ORDER BY id").fetchall()
        groups: dict[tuple[str, str], list[sqlite3.Row]] = {}
        for row in rows:
            key = (normalize_text(row["canonical_name"]), normalize_text(row["account_type"]))
            groups.setdefault(key, []).append(row)
        for key, matches in groups.items():
            if key[0] and len(matches) > 1:
                ids = [row["id"] for row in matches]
                self._exception("DUPLICATE_ACCOUNT_CANDIDATE", "high", 2, {"account_ids": ids, "normalized_key": key},
                                "Multiple active accounts share a normalized name and type.",
                                "Review identifiers and merge only after confirming they represent the same real account.",
                                f"Do these {len(ids)} {matches[0]['canonical_name']} accounts represent the same account?")

    def _detect_unmatched_transactions(self) -> None:
        for row in self.db.execute("SELECT * FROM financial_transactions WHERE account_id IS NULL"):
            self._exception("TRANSACTION_ACCOUNT_UNMATCHED", "high", 1,
                            {"source_system": row["source_system"], "external_id": row["external_id"],
                             "account_reference": (json.loads(row["raw_payload_json"]).get("account_id")
                                                   or json.loads(row["raw_payload_json"]).get("AccountId"))},
                            "The source account identifier has no canonical/QBO account match.",
                            "Map the source account before categorizing or using this transaction in cash reporting.",
                            "Which real account does this transaction belong to?", transaction_id=row["id"],
                            impact={"amount_minor": row["amount_minor"], "currency": row["currency"]})

    def _detect_card_payments_as_expense(self) -> None:
        terms = ("credit card", "capital one", "amex", "american express", "discover", "chase card", "elan", "card payment")
        for row in self.db.execute("SELECT * FROM financial_transactions"):
            haystack = normalize_text(" ".join(str(row[key] or "") for key in ("payee", "memo", "category_name")))
            category = normalize_text(row["category_type"] or row["category_name"])
            if any(term in haystack for term in terms) and any(term in category for term in ("expense", "cost", "income")):
                self._exception("CREDIT_CARD_PAYMENT_AS_EXPENSE", "critical", 1,
                                {"external_id": row["external_id"], "payee": row["payee"], "category": row["category_name"]},
                                "A likely card payment appears categorized as profit-and-loss activity.",
                                "Review as a transfer/liability reduction; leave underlying purchases categorized separately.",
                                "Was this transaction a payment to a 910CPR credit card?", row["account_id"], row["id"],
                                {"amount_minor": row["amount_minor"], "currency": row["currency"]})

    def _detect_transfer_like_income_expense(self) -> None:
        for row in self.db.execute("SELECT * FROM financial_transactions"):
            haystack = normalize_text(" ".join(str(row[key] or "") for key in ("payee", "memo", "transaction_type")))
            category = normalize_text(row["category_type"] or row["category_name"])
            if any(term in haystack for term in ("transfer", "xfer", "online transfer")) and any(term in category for term in ("income", "expense", "revenue", "cost")):
                self._exception("TRANSFER_LIKE_P_AND_L", "high", 1,
                                {"external_id": row["external_id"], "description": haystack, "category": category},
                                "Transfer-like activity is assigned to income or expense.",
                                "Confirm both account legs; reclassify only when internal ownership is established.",
                                "Was this transfer between two 910CPR-controlled accounts?", row["account_id"], row["id"],
                                {"amount_minor": row["amount_minor"], "currency": row["currency"]})

    def _detect_missing_material_facts(self) -> None:
        material_types = ("credit card", "loan", "long term liability", "other current liability")
        for account in self.db.execute("SELECT * FROM financial_accounts WHERE status='active'"):
            if not any(term in normalize_text(account["account_type"]) for term in material_types):
                continue
            known = {row["field_name"] for row in self.db.execute("SELECT field_name FROM financial_facts WHERE account_id=? AND is_current=1 AND value_json NOT IN ('null','\"\"')", (account["id"],))}
            for field, rank in (("current_balance", 1), ("due_date", 1), ("minimum_payment", 1), ("apr", 2)):
                if field not in known:
                    self._exception("MISSING_MATERIAL_FACT", "medium", rank,
                                    {"account": account["canonical_name"], "missing_field": field},
                                    "No current evidence-backed value is stored; missing is not zero.",
                                    "Obtain a current statement or official portal record; do not infer the value.",
                                    f"Can you provide the {field.replace('_', ' ')} for {account['canonical_name']}?",
                                    account["id"])

    def record_correction(self, correction: dict[str, Any]) -> tuple[str, str]:
        required = {"correction_type", "statement", "accounting_treatment", "supplied_by", "targets", "current_treatment", "proposed_treatment", "reason", "incorrect_action_risk"}
        missing = sorted(required - correction.keys())
        if missing:
            raise ValueError(f"Correction missing fields: {', '.join(missing)}")
        correction_id = str(correction.get("id") or uuid.uuid4())
        action_id = stable_id("bookkeeping-action", correction_id)
        stamp = now_iso()
        with self.db:
            self.db.execute(
                """INSERT INTO financial_user_corrections
                   (id,correction_type,statement,accounting_treatment_json,supplied_by,supplied_at,supersedes_correction_id,status)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (correction_id, correction["correction_type"], correction["statement"], canonical_json(correction["accounting_treatment"]),
                 correction["supplied_by"], correction.get("supplied_at") or stamp, correction.get("supersedes_correction_id"), "active"),
            )
            for target in correction["targets"]:
                self.db.execute("INSERT INTO financial_correction_targets (correction_id,target_type,target_id) VALUES (?,?,?)",
                                (correction_id, target["type"], target["id"]))
            self.db.execute(
                """INSERT INTO financial_bookkeeping_actions
                   (id,correction_id,status,current_treatment_json,proposed_treatment_json,reason,affected_records_json,
                    reversal_or_reclassification,incorrect_action_risk,execution_mode,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (action_id, correction_id, "proposed", canonical_json(correction["current_treatment"]),
                 canonical_json(correction["proposed_treatment"]), correction["reason"], canonical_json(correction["targets"]),
                 correction.get("reversal_or_reclassification"), correction["incorrect_action_risk"], "human_review", stamp),
            )
        return correction_id, action_id

    def exceptions(self) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM financial_reconciliation_exceptions WHERE status='open'").fetchall()
        result = [dict(row) for row in rows]
        result.sort(key=lambda row: (row["priority_rank"], SEVERITY_ORDER.get(row["severity"], 9), row["detector_code"], row["id"]))
        return result

    def summary(self) -> dict[str, Any]:
        count = lambda table: self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        exceptions = self.exceptions()
        return {
            "generated_at": now_iso(),
            "mode": "read_only_audit",
            "accounts": count("financial_accounts"),
            "source_records": count("financial_source_records"),
            "transactions": count("financial_transactions"),
            "current_facts": self.db.execute("SELECT COUNT(*) FROM financial_facts WHERE is_current=1").fetchone()[0],
            "open_exceptions": len(exceptions),
            "exceptions_by_detector": dict(self.db.execute("SELECT detector_code,COUNT(*) FROM financial_reconciliation_exceptions WHERE status='open' GROUP BY detector_code").fetchall()),
            "cleanup_queue": exceptions,
        }
