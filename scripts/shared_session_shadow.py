"""Issue #359 pure shadow session-capacity contract; never used by publication.

Resource legality remains the existing layered engine's responsibility. Callers
supply only starts already accepted by that engine. This is not a booking API.
"""
from dataclasses import dataclass


ARC_SESSION_CAPACITIES = {"ARC_GENERAL_SKILLS": 4, "ARC_BLS": 4}


def positive(value):
    return type(value) is int and value > 0


@dataclass(frozen=True)
class Session:
    session_id: str
    family: str
    capacity: int
    # Each tuple retains exact product identity and its active seats/holds.
    items: tuple
    revision: int
    state: str = "open"


def remaining(session, product_families):
    """Unknown/malformed occupancy fails closed; no inferred product mappings."""
    if not session.session_id or not positive(session.capacity):
        raise ValueError("explicit session identity and capacity required")
    if type(session.revision) is not int or session.revision < 0:
        raise ValueError("invalid session revision")
    if session.state != "open":
        return 0
    total = 0
    for product, count in session.items:
        if product_families.get(product) != session.family:
            raise ValueError("unknown or incompatible product: " + product)
        if type(count) is not int or count < 0:
            raise ValueError("unknown or invalid occupancy")
        total += count
    return max(0, session.capacity - total)


def options(product, sessions, legal_starts, product_families, capacities):
    """Prefer compatible planted seats; full sessions never create a day ban.

    Sessions must already be scoped to the requested resource/time horizon and
    qualified for this product. legal_starts are accepted layered-core results.
    This function makes no claim to establish resource or enrollment legality.
    """
    family = product_families.get(product)
    if not family or not positive(capacities.get(family)):
        raise ValueError("explicit product family and family capacity required")
    ids = [session.session_id for session in sessions]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate session identity")
    planted = []
    for session in sessions:
        if session.family != family:
            continue
        seats = remaining(session, product_families)
        if seats:
            planted.append(dict(mode="planted", session_id=session.session_id,
                                product=product, remaining_seats=seats,
                                revision=session.revision))
    if planted:
        return planted
    return [dict(mode="new_session", product=product, family=family,
                 start=start, capacity=capacities[family]) for start in legal_starts]


def revalidate(session, product, seats, expected_revision, product_families):
    """Pure precondition for an eventual transaction, NOT atomic reservation.

    A real booking service must lock session, read current seats/holds, evaluate
    all current resource constraints, call this check, persist seats and advance
    revision in the SAME transaction. A Python precheck alone prevents no race.
    """
    return (positive(seats) and session.revision == expected_revision
            and product_families.get(product) == session.family
            and remaining(session, product_families) >= seats)
