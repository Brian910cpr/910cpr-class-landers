from scripts.anchor_state import ANCHOR_SYMBOL, annotate_offer, promote_seated_sessions, same_course_anchor


def session(**overrides):
    value = {
        "session_id": "13833211",
        "course_id": "359474",
        "start_at": "2026-08-05T09:30:00-04:00",
        "end_at": "2026-08-05T11:30:00-04:00",
        "location_name": ":: Wilmington; Shipyard Blvd - B",
        "lead_instructor_name": "Brian Ennis",
        "registered_count": 1,
    }
    value.update(overrides)
    return value


def test_first_seat_promotes_any_real_course_to_anchor():
    anchors = promote_seated_sessions([session()])
    assert len(anchors) == 1
    anchor = anchors[0]
    assert anchor["schedule_role"] == "anchor"
    assert anchor["schedule_symbol"] == ANCHOR_SYMBOL
    assert anchor["promotion_reason"] == "first_confirmed_seat"
    assert anchor["landing_page_required"] is True
    assert anchor["external_publication_eligible"] is True


def test_empty_session_is_not_promoted():
    assert promote_seated_sessions([session(registered_count=0)]) == []


def test_barnacle_with_first_seat_promotes_on_next_refresh():
    prior_offer = annotate_offer(
        {
            "course_id": "210549",
            "start_at": "2026-08-05T11:30:00-04:00",
        },
        attached_to=promote_seated_sessions([session()])[0],
    )
    assert prior_offer["schedule_role"] == "barnacle"
    assert prior_offer["schedule_symbol"] == ""

    newly_seated = session(
        session_id="13818252",
        course_id="210549",
        start_at="2026-08-05T11:30:00-04:00",
        end_at="2026-08-05T12:30:00-04:00",
        registered_count=1,
    )
    promoted = promote_seated_sessions([newly_seated])[0]
    assert promoted["schedule_role"] == "anchor"
    assert promoted["schedule_symbol"] == ANCHOR_SYMBOL


def test_existing_same_course_anchor_wins_before_new_time():
    anchors = promote_seated_sessions([
        session(),
        session(
            session_id="later",
            start_at="2026-08-05T14:00:00-04:00",
            end_at="2026-08-05T16:00:00-04:00",
        ),
    ])
    selected = same_course_anchor(
        course_id="359474",
        date="2026-08-05",
        location=":: Wilmington; Shipyard Blvd - B",
        anchors=anchors,
    )
    assert selected is not None
    assert selected["session_id"] == "13833211"
    assert selected["start_at"].startswith("2026-08-05T09:30:00")


def test_wrong_course_does_not_reuse_anchor():
    anchors = promote_seated_sessions([session()])
    selected = same_course_anchor(
        course_id="210549",
        date="2026-08-05",
        location=":: Wilmington; Shipyard Blvd - B",
        anchors=anchors,
    )
    assert selected is None
