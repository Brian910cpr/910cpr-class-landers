# PR353 Heartsaver CPR/AED duration

Owner specified in-person Heartsaver CPR/AED (existing course344085): 90 instruction minutes plus15 cleanup,105 total consumption. Existing catalog already specifies90; cleanup now15. Production V2 course_duration_overrides carries evidenced per-course duration without replacing other full/skills defaults or rewriting booked source bounds. Invalid overrides fail explicitly.

Validation:62 adapter/publication/customer-render/cache tests passed; regression verifies10:15/13:00 edges beside a12:00–13:00 booking for105-minute consumption while standard full remains09:30/13:00. Syntax and config parse checked. No generator or booking mutation. Online/blended skills course209808 unchanged.

Not deployed: release hold persists. Real-source probe dispatched after push; result pending.
