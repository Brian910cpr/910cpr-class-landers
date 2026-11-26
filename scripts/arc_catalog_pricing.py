"""Offline ARC commercial quote projection; never activates booking or fulfillment."""
from decimal import Decimal, ROUND_HALF_UP


def quote(course: dict, choice: str) -> dict:
    route = course["commercial_choices"][choice]
    sku = route["fulfillment_sku"]
    cost = course.get(route["source_cost_field"], "UNKNOWN")
    if sku == "UNKNOWN" or cost == "UNKNOWN":
        return {"state": "BLOCKED", "reason": "unconfirmed_arc_fulfillment", "total_usd": None}
    rule = course["pricing_rule"]
    service = Decimal(str(course[rule["service_charge_field"]]))
    fee = (Decimal(str(cost)) * Decimal(str(course[rule["fee_multiplier_field"]]))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return {
        "state": "CATALOG_QUOTE_ONLY",
        "fulfillment_sku": sku,
        "source_cost_usd": str(Decimal(str(cost)).quantize(Decimal("0.01"))),
        "pass_through_usd": str(fee),
        "service_charge_usd": str(service.quantize(Decimal("0.01"))),
        "total_usd": str((service + fee).quantize(Decimal("0.01"))),
        "currency": rule["currency"],
    }
