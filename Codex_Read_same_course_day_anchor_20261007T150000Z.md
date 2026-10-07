# Codex read receipt — same-course starred day anchor

Round ID: `20261007T150000Z-I349-R4`

Reviewed `Codex_Reply_same_course_day_anchor.md` and the referenced production path.

## Review

- Root cause confirmed: retained `seated_class` rows with unknown roster counts were projected independently from calculated offers, while prior consolidation was scoped to paid/count-known anchors and individual availability windows. This allowed a real starred class and calculated offers for the same course ID on the same day.
- PR #358 (`0b593aec24a9103ef03c38078f0b170c8c28b6bb`, merged as `ed8f3deaf2a85e132fed2244daef1804e2b85c09`) applies the narrow publication fix in `scripts/layered_publication_adapter.py`.
- The fix preserves every real class and suppresses only non-seated offers matching the exact `(date, courseId)` of a retained seated class. Different formats/course IDs and other days remain eligible.
- Targeted regression covers full and skills formats, unknown counts, same-day suppression, different-course survival, and next-day survival. The handoff reports 59 passing targeted tests; PR checks and Cloudflare preview were green.
- Production artifact generated 2026-10-07 10:54 ET verified:
  - Oct. 19: real 9:00 AM BLS Initial remains; same-course 11:00 AM alternative is absent.
  - Oct. 20: real 11:45 AM BLS Initial remains; same-course 9:15 AM, 8:00 PM, and 9:00 PM alternatives are absent.
  - Legal HeartCode and Renewal offers remain on both days.
  - BLS totals are 88 dates, 1,486 starts, and 3,898 offers with 205/205 windows evaluated, zero failures, and zero uncertainty issues.
- Final Pages deployment `37640712642` succeeded.
- Closed incident #349 was updated with this post-close hardening proof.

## Disposition

The handoff is accepted and fully processed. No further repository dispatch and no Brian-only action are required for this correction.
