from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("America/New_York")
DEFAULT_CSV = ROOT / "data" / "inventory" / "910cpr_inventory_events.csv"
DEFAULT_OUT = ROOT / "docs" / "data"
DEFAULT_DASHBOARD = ROOT / "docs" / "internal" / "inventory.html"
SCHEDULE_FUTURE = ROOT / "docs" / "data" / "schedule_future.json"

EXPECTED_COLUMNS = {
    "timestamp",
    "event_type",
    "source",
    "student_name",
    "student_email",
    "class_name",
    "class_datetime",
    "location",
    "option_number",
    "product_name_raw",
    "product_key",
    "remaining",
    "inventory_delta",
    "status",
    "needs_assignment",
    "parse_confidence",
    "raw_option_text",
    "email_subject",
}

REQUIRED_COLUMNS = {"product_key"}
CONSUMPTION_TYPES = {"CONSUMPTION", "REGISTRATION", "ENROLLWARE_REGISTRATION", "SALE", "ASSIGNMENT"}
RESTOCK_TYPES = {"RESTOCK", "VITALI_RESTOCK", "ORDER_RECEIVED", "ADJUSTMENT_ADD"}
STATUS_ORDER = {"OUT": 0, "CRITICAL": 1, "LOW": 2, "WATCH": 3, "OK": 4}


def now_iso() -> str:
    return datetime.now(TZ).isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def parse_timestamp(value: Any) -> datetime | None:
    text = clean(value)
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        for fmt in (
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%m/%d/%y %H:%M",
            "%m/%d/%Y",
            "%Y-%m-%d",
        ):
            try:
                dt = datetime.strptime(text, fmt)
                break
            except ValueError:
                dt = None
        if dt is None:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def parse_number(value: Any) -> int | None:
    text = clean(value)
    if not text:
        return None
    match = re.search(r"[-+]?\d+", text.replace(",", ""))
    if not match:
        return None
    try:
        return int(match.group(0))
    except ValueError:
        return None


def parse_float(value: Any) -> float | None:
    text = clean(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_bool(value: Any) -> bool:
    text = clean(value).lower()
    return text in {"1", "true", "yes", "y", "needs_assignment", "needs assignment"}


def normalize_event_type(row: dict[str, Any]) -> str:
    event_type = clean(row.get("event_type")).upper().replace(" ", "_")
    source = clean(row.get("source")).lower()
    status = clean(row.get("status")).upper()
    raw_text = clean(row.get("raw_option_text")).upper()
    delta = parse_number(row.get("inventory_delta"))

    if event_type:
        if event_type in {"ENROLLWARE_REGISTRATION", "REGISTRATION"}:
            return "CONSUMPTION"
        if event_type in {"VITALI_RESTOCK"}:
            return "RESTOCK"
        return event_type
    if source == "vitali_restock":
        return "RESTOCK"
    if source == "enrollware_registration":
        return "CONSUMPTION"
    if delta is not None:
        return "RESTOCK" if delta > 0 else "CONSUMPTION" if delta < 0 else "ADJUSTMENT"
    if status == "OUT" and parse_number(row.get("remaining")) == 0:
        return "CONSUMPTION"
    if "NEEDS TO BE ASSIGNED" in raw_text:
        return "CONSUMPTION"
    return "UNKNOWN"


def infer_delta(row: dict[str, Any], event_type: str) -> int | None:
    explicit = parse_number(row.get("inventory_delta"))
    if explicit is not None:
        return explicit

    source = clean(row.get("source")).lower()
    remaining = parse_number(row.get("remaining"))
    status = clean(row.get("status")).upper()

    if source == "vitali_restock" and remaining is not None:
        return remaining
    if event_type in RESTOCK_TYPES and remaining is not None and clean(row.get("remaining")).startswith("+"):
        return remaining
    if source == "enrollware_registration":
        return -1
    if event_type in CONSUMPTION_TYPES:
        return -1
    if status == "OUT" and remaining == 0:
        return -1
    return None


def load_rows(csv_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if not csv_path.exists():
        warnings.append(f"Input CSV not found: {csv_path}. Wrote empty inventory outputs.")
        return [], warnings

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing_required = sorted(REQUIRED_COLUMNS - fieldnames)
        missing_optional = sorted(EXPECTED_COLUMNS - fieldnames - REQUIRED_COLUMNS)
        if missing_required:
            warnings.append(f"Missing required column(s): {', '.join(missing_required)}.")
        if missing_optional:
            warnings.append(f"Missing optional column(s): {', '.join(missing_optional)}.")
        if missing_required:
            return [], warnings
        rows = [dict(row) for row in reader]
    return rows, warnings


def normalize_rows(raw_rows: list[dict[str, Any]], warnings: list[str]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    skipped_without_key = 0
    timestamp_parse_failures = 0

    for index, row in enumerate(raw_rows, start=2):
        product_key = clean(row.get("product_key"))
        if not product_key:
            skipped_without_key += 1
            continue

        dt = parse_timestamp(row.get("timestamp"))
        if clean(row.get("timestamp")) and dt is None:
            timestamp_parse_failures += 1

        event_type = normalize_event_type(row)
        remaining = parse_number(row.get("remaining"))
        delta = infer_delta(row, event_type)
        raw_option_text = clean(row.get("raw_option_text"))
        needs_assignment = parse_bool(row.get("needs_assignment")) or "NEEDS TO BE ASSIGNED" in raw_option_text.upper()

        normalized.append(
            {
                "row_number": index,
                "timestamp": dt,
                "timestamp_raw": clean(row.get("timestamp")),
                "event_type": event_type,
                "source": clean(row.get("source")),
                "student_name": clean(row.get("student_name")),
                "student_email": clean(row.get("student_email")),
                "class_name": clean(row.get("class_name")),
                "class_datetime": clean(row.get("class_datetime")),
                "location": clean(row.get("location")),
                "option_number": clean(row.get("option_number")),
                "product_name_raw": clean(row.get("product_name_raw")),
                "product_key": product_key,
                "remaining": remaining,
                "inventory_delta": delta,
                "status": clean(row.get("status")).upper(),
                "needs_assignment": needs_assignment,
                "parse_confidence": parse_float(row.get("parse_confidence")),
                "raw_option_text": raw_option_text,
                "email_subject": clean(row.get("email_subject")),
            }
        )

    if skipped_without_key:
        warnings.append(f"Skipped {skipped_without_key} row(s) without product_key.")
    if timestamp_parse_failures:
        warnings.append(f"Could not parse timestamp on {timestamp_parse_failures} row(s); those rows are kept but excluded from dated windows.")
    return normalized


def event_sort_key(event: dict[str, Any]) -> tuple[str, int]:
    dt = event.get("timestamp")
    return (dt.isoformat() if dt else "", int(event.get("row_number") or 0))


def event_public(event: dict[str, Any]) -> dict[str, Any]:
    payload = dict(event)
    dt = payload.pop("timestamp", None)
    payload["timestamp"] = dt.isoformat() if dt else payload.pop("timestamp_raw", "")
    payload.pop("timestamp_raw", None)
    return payload


def count_events_since(events: list[dict[str, Any]], now: datetime, days: int) -> int:
    cutoff = now - timedelta(days=days)
    return sum(1 for event in events if event.get("timestamp") and event["timestamp"] >= cutoff)


def consumption_since(events: list[dict[str, Any]], now: datetime, days: int) -> int:
    cutoff = now - timedelta(days=days)
    total = 0
    for event in events:
        dt = event.get("timestamp")
        if not dt or dt < cutoff:
            continue
        delta = event.get("inventory_delta")
        if delta is not None and delta < 0:
            total += abs(delta)
        elif event.get("event_type") in CONSUMPTION_TYPES:
            total += 1
    return total


def restock_since(events: list[dict[str, Any]], now: datetime, days: int) -> int:
    cutoff = now - timedelta(days=days)
    total = 0
    for event in events:
        dt = event.get("timestamp")
        delta = event.get("inventory_delta")
        if dt and dt >= cutoff and delta is not None and delta > 0:
            total += delta
    return total


def days_remaining(inventory: int | None, daily_burn: float | None) -> float | None:
    if inventory is None or daily_burn is None or daily_burn <= 0:
        return None
    return round(max(0, inventory) / daily_burn, 1)


def status_for(inventory: int | None, latest_remaining: int | None, days_14: float | None, projected_shortfall: bool | None) -> str:
    basis = inventory if inventory is not None else latest_remaining
    if (inventory is not None and inventory <= 0) or latest_remaining == 0:
        return "OUT"
    if basis is not None and 1 <= basis <= 5:
        return "CRITICAL"
    if basis is not None and 6 <= basis <= 10:
        return "LOW"
    if (days_14 is not None and days_14 <= 14) or projected_shortfall:
        return "WATCH"
    return "OK"


def suggested_action(status: str, service_failure_risk: bool) -> str:
    if service_failure_risk:
        return "Customer may be waiting on an unassigned code. Resolve immediately."
    if status == "OUT":
        return "Immediate order required."
    if status == "CRITICAL":
        return "Order within 24 hours."
    if status == "LOW":
        return "Add to next order batch."
    if status == "WATCH":
        return "Monitor closely. Forecast suggests possible shortage."
    return "No immediate action."


def latest_value(events: list[dict[str, Any]], key: str) -> Any:
    for event in sorted(events, key=event_sort_key, reverse=True):
        value = event.get(key)
        if value not in (None, ""):
            return value
    return None


def latest_reported_remaining_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        event
        for event in events
        if event.get("remaining") is not None
        and (event.get("event_type") in CONSUMPTION_TYPES or clean(event.get("source")).lower() == "enrollware_registration")
    ]
    if not candidates:
        return None
    return sorted(candidates, key=event_sort_key, reverse=True)[0]


def load_schedule_placeholders(warnings: list[str]) -> dict[str, Any]:
    if not SCHEDULE_FUTURE.exists():
        return {
            "schedule_future_loaded": False,
            "expected_usage_next_7_days": None,
            "expected_usage_next_14_days": None,
            "projected_shortfall_7_days": None,
            "projected_shortfall_14_days": None,
        }
    try:
        json.loads(SCHEDULE_FUTURE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"Could not safely read {SCHEDULE_FUTURE}: {exc}. Forecast fields set to null.")
        loaded = False
    else:
        loaded = True
    return {
        "schedule_future_loaded": loaded,
        "expected_usage_next_7_days": None,
        "expected_usage_next_14_days": None,
        "projected_shortfall_7_days": None,
        "projected_shortfall_14_days": None,
    }


def build_products(events: list[dict[str, Any]], warnings: list[str]) -> list[dict[str, Any]]:
    now = datetime.now(TZ)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[event["product_key"]].append(event)

    schedule_fields = load_schedule_placeholders(warnings)
    products: list[dict[str, Any]] = []

    for product_key, product_events in sorted(grouped.items()):
        sorted_events = sorted(product_events, key=event_sort_key)
        delta_sum = sum(event["inventory_delta"] for event in sorted_events if event.get("inventory_delta") is not None)
        remaining_event = latest_reported_remaining_event(sorted_events)
        latest_remaining = remaining_event.get("remaining") if remaining_event else None
        restocks_after_remaining = 0
        calculated_inventory = delta_sum if delta_sum or delta_sum == 0 else None
        mismatch_note = ""

        if remaining_event is not None:
            remaining_dt = remaining_event.get("timestamp")
            remaining_row = int(remaining_event.get("row_number") or 0)
            for event in sorted_events:
                delta = event.get("inventory_delta")
                if delta is None or delta <= 0:
                    continue
                event_dt = event.get("timestamp")
                event_row = int(event.get("row_number") or 0)
                happened_after = False
                if remaining_dt and event_dt:
                    happened_after = event_dt > remaining_dt
                elif not remaining_dt or not event_dt:
                    happened_after = event_row > remaining_row
                if happened_after:
                    restocks_after_remaining += delta
            calculated_inventory = int(latest_remaining) + restocks_after_remaining
            if delta_sum != calculated_inventory:
                mismatch_note = (
                    f"Latest reported remaining {latest_remaining} from row {remaining_row} plus later restocks "
                    f"({restocks_after_remaining}) gives {calculated_inventory}; ledger delta sum is {delta_sum}."
                )

        burn_7 = round(consumption_since(sorted_events, now, 7) / 7, 3)
        burn_14 = round(consumption_since(sorted_events, now, 14) / 14, 3)
        burn_30 = round(consumption_since(sorted_events, now, 30) / 30, 3)
        days_7 = days_remaining(calculated_inventory, burn_7)
        days_14 = days_remaining(calculated_inventory, burn_14)
        days_30 = days_remaining(calculated_inventory, burn_30)
        projected_shortfall_7 = schedule_fields["projected_shortfall_7_days"]
        projected_shortfall_14 = schedule_fields["projected_shortfall_14_days"]
        service_failure = any(event.get("needs_assignment") for event in sorted_events)
        status = status_for(calculated_inventory, latest_remaining, days_14, projected_shortfall_14)
        latest_event = sorted(sorted_events, key=event_sort_key, reverse=True)[0]

        product = {
            "product_key": product_key,
            "product_name_raw_latest": latest_value(sorted_events, "product_name_raw") or product_key,
            "latest_remaining_reported": latest_remaining,
            "calculated_inventory": calculated_inventory,
            "latest_status": status,
            "last_seen_timestamp": latest_event["timestamp"].isoformat() if latest_event.get("timestamp") else latest_event.get("timestamp_raw", ""),
            "events_last_7_days": count_events_since(sorted_events, now, 7),
            "events_last_14_days": count_events_since(sorted_events, now, 14),
            "events_last_30_days": count_events_since(sorted_events, now, 30),
            "consumption_last_7_days": consumption_since(sorted_events, now, 7),
            "consumption_last_14_days": consumption_since(sorted_events, now, 14),
            "consumption_last_30_days": consumption_since(sorted_events, now, 30),
            "restock_last_30_days": restock_since(sorted_events, now, 30),
            "estimated_daily_burn_7d": burn_7,
            "estimated_daily_burn_14d": burn_14,
            "estimated_daily_burn_30d": burn_30,
            "days_remaining_7d": days_7,
            "days_remaining_14d": days_14,
            "days_remaining_30d": days_30,
            "needs_assignment_count": sum(1 for event in sorted_events if event.get("needs_assignment")),
            "service_failure_risk": service_failure,
            "parse_confidence_latest": latest_value(sorted_events, "parse_confidence"),
            "suggested_action": suggested_action(status, service_failure),
            "inventory_mismatch": bool(mismatch_note),
            "inventory_mismatch_note": mismatch_note or None,
            **schedule_fields,
        }
        products.append(product)

    return sorted(products, key=lambda item: (STATUS_ORDER.get(item["latest_status"], 9), item["product_key"]))


def build_alerts(products: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    alerts: list[dict[str, Any]] = []
    product_by_key = {product["product_key"]: product for product in products}

    for product in products:
        if product["latest_status"] != "OK":
            alerts.append(
                {
                    "alert_type": product["latest_status"],
                    "severity": product["latest_status"],
                    "product_key": product["product_key"],
                    "product_name_raw_latest": product["product_name_raw_latest"],
                    "calculated_inventory": product["calculated_inventory"],
                    "latest_remaining_reported": product["latest_remaining_reported"],
                    "days_remaining_14d": product["days_remaining_14d"],
                    "suggested_action": product["suggested_action"],
                }
            )
        if product["service_failure_risk"]:
            alerts.append(
                {
                    "alert_type": "SERVICE_FAILURE_RISK",
                    "severity": "SERVICE_FAILURE_RISK",
                    "product_key": product["product_key"],
                    "product_name_raw_latest": product["product_name_raw_latest"],
                    "needs_assignment_count": product["needs_assignment_count"],
                    "suggested_action": "Customer may be waiting on an unassigned code. Resolve immediately.",
                }
            )

    for event in events:
        if not event.get("needs_assignment"):
            continue
        product = product_by_key.get(event["product_key"], {})
        alerts.append(
            {
                "alert_type": "SERVICE_FAILURE_EVENT",
                "severity": "SERVICE_FAILURE_RISK",
                "product_key": event["product_key"],
                "product_name_raw_latest": product.get("product_name_raw_latest") or event.get("product_name_raw") or event["product_key"],
                "timestamp": event["timestamp"].isoformat() if event.get("timestamp") else event.get("timestamp_raw", ""),
                "student_name": event.get("student_name"),
                "student_email": event.get("student_email"),
                "class_name": event.get("class_name"),
                "raw_option_text": event.get("raw_option_text"),
                "suggested_action": "Customer may be waiting on an unassigned code. Resolve immediately.",
            }
        )

    summary = Counter(alert["severity"] for alert in alerts)
    return {
        "generated_at": now_iso(),
        "summary": dict(sorted(summary.items())),
        "alerts": alerts,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp_path.replace(path)


def render_dashboard() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>910CPR Inventory</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f8fb;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #667085;
      --line: #d7dee8;
      --out: #b42318;
      --critical: #c2410c;
      --low: #a16207;
      --watch: #1769aa;
      --ok: #157347;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.4;
    }
    main {
      width: min(1180px, calc(100% - 28px));
      margin: 0 auto;
      padding: 24px 0 40px;
    }
    header {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }
    h1, h2 { margin: 0; letter-spacing: 0; }
    h1 { font-size: clamp(1.6rem, 3vw, 2.4rem); }
    h2 { font-size: 1rem; }
    .muted { color: var(--muted); }
    .grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 16px;
    }
    .metric, section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .metric {
      min-height: 86px;
      padding: 14px;
    }
    .metric strong {
      display: block;
      font-size: 1.8rem;
      line-height: 1.1;
      margin-top: 6px;
    }
    section {
      margin: 12px 0;
      overflow: hidden;
    }
    section > .section-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
      background: #fbfcfe;
    }
    .table-wrap { overflow-x: auto; }
    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 760px;
    }
    th, td {
      padding: 11px 14px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
      font-size: 0.93rem;
    }
    th {
      color: var(--muted);
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0;
      white-space: nowrap;
    }
    tr:last-child td { border-bottom: 0; }
    .badge {
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 3px 8px;
      border-radius: 999px;
      font-weight: 700;
      font-size: 0.78rem;
      color: #fff;
      white-space: nowrap;
    }
    .OUT { background: var(--out); }
    .CRITICAL { background: var(--critical); }
    .LOW { background: var(--low); }
    .WATCH { background: var(--watch); }
    .OK { background: var(--ok); }
    .SERVICE_FAILURE_RISK, .SERVICE_FAILURE_EVENT { background: #6f2c91; }
    .empty { padding: 18px 16px; color: var(--muted); }
    @media (max-width: 760px) {
      header { display: block; }
      .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      main { width: min(100% - 18px, 1180px); padding-top: 16px; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>910CPR Inventory</h1>
        <div class="muted">Internal operator dashboard</div>
      </div>
      <div class="muted" id="updated">Loading...</div>
    </header>

    <div class="grid" id="metrics"></div>
    <div id="alert-sections"></div>

    <section>
      <div class="section-head">
        <h2>Latest Inventory by Product</h2>
        <span class="muted" id="product-count"></span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Status</th>
              <th>Product</th>
              <th>Calculated</th>
              <th>Reported</th>
              <th>Days Remaining</th>
              <th>Burn 14d</th>
              <th>Suggested Action</th>
              <th>Last Seen</th>
            </tr>
          </thead>
          <tbody id="products"></tbody>
        </table>
      </div>
    </section>
  </main>

  <script>
    const statusOrder = ["OUT", "CRITICAL", "LOW", "WATCH"];

    function fmt(value) {
      return value === null || value === undefined || value === "" ? "n/a" : value;
    }

    function badge(label) {
      return `<span class="badge ${label}">${label.replaceAll("_", " ")}</span>`;
    }

    function tableRows(items, columns) {
      if (!items.length) return `<div class="empty">No items.</div>`;
      const rows = items.map(item => `<tr>${columns.map(col => `<td>${col(item)}</td>`).join("")}</tr>`).join("");
      return `<div class="table-wrap"><table><tbody>${rows}</tbody></table></div>`;
    }

    Promise.all([
      fetch("/data/inventory_status.json").then(r => r.json()),
      fetch("/data/inventory_alerts.json").then(r => r.json())
    ]).then(([status, alerts]) => {
      const products = status.products || [];
      document.getElementById("updated").textContent = `Last updated ${fmt(status.generated_at)}`;
      document.getElementById("product-count").textContent = `${products.length} products`;

      const counts = status.summary?.status_counts || {};
      const riskCount = status.summary?.service_failure_risk_count || 0;
      document.getElementById("metrics").innerHTML = [
        ["OUT", counts.OUT || 0],
        ["CRITICAL", counts.CRITICAL || 0],
        ["LOW", counts.LOW || 0],
        ["WATCH", counts.WATCH || 0],
        ["SERVICE FAILURE RISK", riskCount]
      ].map(([label, value]) => `<div class="metric"><span class="muted">${label}</span><strong>${value}</strong></div>`).join("");

      document.getElementById("alert-sections").innerHTML = statusOrder.map(name => {
        const items = products.filter(product => product.latest_status === name);
        return `<section><div class="section-head"><h2>${name} Items</h2><span class="muted">${items.length}</span></div>${
          tableRows(items, [
            item => badge(item.latest_status),
            item => `<strong>${fmt(item.product_name_raw_latest)}</strong><br><span class="muted">${fmt(item.product_key)}</span>`,
            item => fmt(item.calculated_inventory),
            item => fmt(item.latest_remaining_reported),
            item => fmt(item.days_remaining_14d),
            item => fmt(item.suggested_action)
          ])
        }</section>`;
      }).join("") + `<section><div class="section-head"><h2>Service Failure Risk Items</h2><span class="muted">${riskCount}</span></div>${
        tableRows(products.filter(product => product.service_failure_risk), [
          item => badge("SERVICE_FAILURE_RISK"),
          item => `<strong>${fmt(item.product_name_raw_latest)}</strong><br><span class="muted">${fmt(item.product_key)}</span>`,
          item => fmt(item.needs_assignment_count),
          item => fmt(item.suggested_action)
        ])
      }</section>`;

      document.getElementById("products").innerHTML = products.map(item => `<tr>
        <td>${badge(item.latest_status)}</td>
        <td><strong>${fmt(item.product_name_raw_latest)}</strong><br><span class="muted">${fmt(item.product_key)}</span></td>
        <td>${fmt(item.calculated_inventory)}</td>
        <td>${fmt(item.latest_remaining_reported)}</td>
        <td>${fmt(item.days_remaining_14d)}</td>
        <td>${fmt(item.estimated_daily_burn_14d)}</td>
        <td>${fmt(item.suggested_action)}</td>
        <td>${fmt(item.last_seen_timestamp)}</td>
      </tr>`).join("") || `<tr><td colspan="8" class="empty">No inventory events loaded.</td></tr>`;
    }).catch(error => {
      document.getElementById("updated").textContent = "Unable to load inventory JSON.";
      document.getElementById("products").innerHTML = `<tr><td colspan="8" class="empty">${error}</td></tr>`;
    });
  </script>
</body>
</html>
"""


def build_payloads(csv_path: Path, out_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    warnings: list[str] = []
    raw_rows, load_warnings = load_rows(csv_path)
    warnings.extend(load_warnings)
    events = normalize_rows(raw_rows, warnings)
    products = build_products(events, warnings)
    status_counts = Counter(product["latest_status"] for product in products)
    service_failure_count = sum(1 for product in products if product["service_failure_risk"])

    status_payload = {
        "generated_at": now_iso(),
        "source_csv": str(csv_path),
        "google_sheet_url": "https://docs.google.com/spreadsheets/d/1FLM1RPeoU30IXAMgaJjo1FehH8bRlrInvcHifB0Hlkg/edit",
        "summary": {
            "total_rows_read": len(raw_rows),
            "total_events_processed": len(events),
            "total_products_processed": len(products),
            "status_counts": {key: status_counts.get(key, 0) for key in ["OUT", "CRITICAL", "LOW", "WATCH", "OK"]},
            "service_failure_risk_count": service_failure_count,
        },
        "warnings": warnings,
        "products": products,
    }
    latest_events_payload = {
        "generated_at": now_iso(),
        "source_csv": str(csv_path),
        "total_events": len(events),
        "events": [event_public(event) for event in sorted(events, key=event_sort_key, reverse=True)[:250]],
    }
    alerts_payload = build_alerts(products, events)
    alerts_payload["warnings"] = warnings
    return status_payload, latest_events_payload, alerts_payload, warnings


def print_summary(status_payload: dict[str, Any], alerts_payload: dict[str, Any], files_written: list[Path]) -> None:
    summary = status_payload["summary"]
    counts = summary["status_counts"]
    print("Inventory status build complete")
    for warning in status_payload.get("warnings", []):
        print(f"WARNING: {warning}")
    print(f"Total rows read: {summary['total_rows_read']}")
    print(f"Total products processed: {summary['total_products_processed']}")
    print(f"OUT count: {counts.get('OUT', 0)}")
    print(f"CRITICAL count: {counts.get('CRITICAL', 0)}")
    print(f"LOW count: {counts.get('LOW', 0)}")
    print(f"WATCH count: {counts.get('WATCH', 0)}")
    print(f"SERVICE FAILURE RISK count: {summary['service_failure_risk_count']}")
    print(f"Alert summary: {alerts_payload.get('summary', {})}")
    print("Files written:")
    for path in files_written:
        print(f"- {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build 910CPR internal inventory status JSON and dashboard.")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="Path to local CSV export of 910CPR Inventory Events.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output directory for inventory JSON files.")
    parser.add_argument("--dashboard", default=str(DEFAULT_DASHBOARD), help="Output path for internal dashboard HTML.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv)
    out_dir = Path(args.out)
    dashboard_path = Path(args.dashboard)
    if not csv_path.is_absolute():
        csv_path = ROOT / csv_path
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    if not dashboard_path.is_absolute():
        dashboard_path = ROOT / dashboard_path

    status_payload, latest_events_payload, alerts_payload, _warnings = build_payloads(csv_path, out_dir)
    files = [
        out_dir / "inventory_status.json",
        out_dir / "inventory_events_latest.json",
        out_dir / "inventory_alerts.json",
        dashboard_path,
    ]
    write_json(files[0], status_payload)
    write_json(files[1], latest_events_payload)
    write_json(files[2], alerts_payload)
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text(render_dashboard(), encoding="utf-8")

    print_summary(status_payload, alerts_payload, files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
