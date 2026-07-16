# Inventory Rule Configuration

This directory separates course consumption requirements from availability window permissions.

`course_consumption_rules.json` answers: what does this course require once scheduled?

`availability_window_policies.json` answers: what does this instructor/location/resource window permit?

The resolver must combine both, plus existing reservations and resource constraints, before publishing inventory. Appointment slot intervals only control potential start-time spacing. They do not define how much capacity a scheduled course consumes.

Do not attach block length or inventory consumption behavior to an instructor record. Instructor availability is limited to when the instructor may be used, where they may be used, and which course families they are eligible to teach.

---

## LanderWare physical and credential inventory intake

The same inventory area now also defines a vendor-agnostic model for eCards and future inventoried items.

### Core rule

Inventory should be maintained as a ledger of events, not as a single manually edited balance.

Expected event types:

- `receipt` — purchases and other inbound stock
- `consumption` — issued eCards or consumed physical supplies
- `reservation` — future registrations/classes expected to consume an item
- `release` — cancelled reservations that return forecast capacity
- `adjustment` — audited manual corrections

The displayed balance is derived from the ledger. Forecasting combines current balance, committed reservations, future scheduled demand, and per-item safety stock.

### Current Gmail source

Arch / AED Superstore order-confirmation emails are matched with:

`from:admin@onlineoversight.com subject:"Thank You for Your Order"`

A matching order should create one `receipt` ledger event per recognized line item. The order number and source ID are used for deduplication so rescanning Gmail cannot double-count inventory.

Current observed example:

- Order 114577
- 10 ACLS Provider eCards
- 50 BLS Provider eCards
- 20 Heartsaver First Aid CPR AED eCards

This is a receipt example only and must not be treated as the current on-hand balance without reconciling prior purchases and consumption.

### Consumption sources

For AHA eCards, issued-card result files should create `consumption` events by exact credential type. Course delivery variants can map to the same credential inventory item where they produce the same eCard.

Examples:

- BLS Initial / Renewal / HeartCode Skills -> BLS Provider eCard
- ACLS course variants -> ACLS Provider eCard
- PALS course variants -> PALS Provider eCard

Heartsaver credentials remain separate when the card issued is different.

### Extending to future programs or vendors

Do not add vendor-specific columns to the ledger.

To support a new product:

1. Add a canonical item to `inventory_catalog.json`.
2. Add aliases used by vendor emails, exports, or files.
3. Map the program/course to the credential or supply item that it consumes.

To support a new source:

1. Add a source rule to `source_rules.json`.
2. Define how the source is identified and parsed.
3. Emit standard ledger events.

Unknown items should be quarantined for review instead of silently ignored or guessed.

### Dashboard behavior

The dashboard should eventually show, per item:

- on hand
- committed/reserved
- projected consumption over the configured lookahead window
- safety stock
- recommended reorder quantity
- source freshness / last receipt

The Admin Inbox remains the universal manual intake path for files. Gmail and other connected feeds can populate the same ledger automatically.
