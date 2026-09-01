# Enrollware crawl progress

Research mode: strictly read-only. No settings, records, messages, payments, imports, bulk actions, or other state-changing controls will be submitted.

Last updated: 2026-09-01

## Authentication

- ✓ Enrollware Admin — authenticated by owner
- ✓ Accessible role/permission scope — administrator menus and User Edit roles inspected; no lower-privilege impersonation performed

## Admin coverage

```text
Dashboard
  ~ Dashboard not used as authoritative workflow evidence; functional branches inspected directly

Courses
  ✓ Course List — 86 rows; discipline, add-ons, price, shipping, eCard, XLSX export, sorting
  ✓ Existing Course Edit — delivery mode, appointments, pricing/deposits, add-ons, shipping, keycode bank, certifying body, CEUs, communications, QuickBooks mapping, archive
      ✓ Self-reschedule price, reschedule insurance, prevent-reschedule window
      ✗ Update / Delete — mutation boundaries

Classes / Schedules
  ✓ Upcoming Classes — multi-dimensional filters and capacity/enrollment projection
      ✗ Bulk Delete Classes — mutation boundary
  ✓ Existing Class Detail — roster, communications, exports, payments, scores, cards, certificates, notes, documents, instructor signature
      ✓ Course/location/instructors, multi-day time, capacity, manikin ratio, listing, close-registration window, certificate dates
      ✗ Import / Quick Add / Add Student / Delete / Finalize / Print Cards / Repeat / Save — mutation boundaries

Students / Registrations
  ✓ Student Search — by name, email, phone, or label
  ✓ Existing Registration Edit — durable class association, reschedule target, charges/payments/balance, labels, products/options, insurance, client, delivery, status, check-in, score, remediation, credential code
      ✓ Notes, email log, text-message log, earlier-class history
      ✗ Update, resend, send, reschedule, delete, payment actions — mutation boundaries
  ✓ Unscheduled Students — holding area preserves registrations without a committed class

Instructors
  ✓ Instructor Records — active/inactive, disciplines/certifications, documents, bulk email/export
  ✓ Expiring Certifications — training site, discipline, expiration, export
  ✓ User/Instructor Edit — identifiers, active/read-only status, notification preferences, bidding, roles, documents

Locations
  ✓ Location List — 343 records, archived-location toggle, XLS export, import
  ✓ Existing Location Edit — name/abbreviation/directions, default, call-to-schedule exclusion, archive, print-on-card, direct links, QuickBooks mapping
      ✓ Archive help text: no longer schedule classes at this location
      ✗ Import / New / Update — mutation boundaries

Organizations / Corporate Customers
  ✓ Client List and tracking
  ✓ Existing Client Edit — organization/contact identity, default location/address, confirmation CCs, shared/internal notes, documents
  ✓ Client Activity Report

Products / Books / Inventory
  ✓ Product Add-ons — code, description, order, price, shippable/non-shippable/keycode, QuickBooks mapping, default selection
  ✓ Online Keycode Banks — total and unused inventory, multi-bank course association supported
  ✓ Keycode Sales — buyer/class/code/status projection
  ✓ Shipping — pending fulfillment queue; canceled registrations excluded per announcement history

Payments / Refunds / Invoices
  ✓ Payment Report and Funding Report entry points
  ✓ Virtual Terminal — non-registration payment capability; process boundary not crossed
  ✓ QuickBooks Sync — transaction history, ignored items, matching/sync controls; mutations not invoked
  ✓ Refund/void/partial-refund lifecycle reviewed through help and announcement evidence

eCards / Certificates
  ✓ Card Settings — printing profiles, card type, training center/location, alignment, default profile
  ✓ Certificate templates/list
  ✓ eCard issuance/export/duplicate-assignment/manual reconciliation concepts reviewed in UI/help/history

Communications / Notifications / Documents
  ✓ Email Campaigns — sequenced messages by day; inactive campaign state
  ✓ Text Messaging — number, quota, auto-reply, forwarding, scheduled messages
  ✓ File Manager and cross-client Download Documents
  ✓ Per-registration email/text logs and per-class communications

Reports
  ✓ Activity, Class, Product Add-on, Promo Code, Registration, Student Export
  ✓ Student Self Reschedule Log, Event Log, Client Activity, Payment/Funding, Download Documents

Users / Permissions / Security
  ✓ User Manager and User Edit
  ✓ Active/read-only, training-site admin, instructor, assistant, view restriction and notification concepts
  ✓ Site security controls: MFA, strict AVS, chargeback IP evidence, admin-only page restrictions, CAPTCHA on communications

Imports / Exports / Bulk Operations
  ✓ Student, class roster, instructor, location and document export/import entry points inventoried
  ✓ Bulk delete, bulk registration/private class, mass import and external roster/card formats identified
      ✗ All import/export downloads and bulk mutations intentionally not executed

Archives / History / Integrations / Settings / Advanced / Legacy
  ✓ Site Settings — integrations, registration toggles, schedule presentation, communications, analytics, audit trail
  ✓ Appointments — availability window, slot/capacity model, existing-class conflict consideration, scheduling blackout
  ✓ Promo Codes — client/course scope, date range, amount/percent, usage limit, email-domain restriction evidence
  ✓ QuickBooks, Zapier, AHA, HSI, ARC, iCal and payment integrations identified
  ✓ Archive states for courses, locations and users; historical event/reschedule/email/text logs

Feature Notifications
  ✓ `Admin > Notifications` — all 30 available entries reviewed (12/19/2024–8/31/2026)
  ✓ `Help > What's New` — 345 dated product changes inventoried; history extends well before 2018
```

## Help-system coverage

```text
Enrollware Help Center
  ✓ Complete category/article tree — 200 articles across 8 categories
  ✓ 68 high-value workflow, edge-case, security, integration and troubleshooting articles reviewed in full
```

## Mutation boundaries encountered

- Class: Import, Quick Add, Add Student, Delete Students, Finalize Roster, Print Cards, Repeat Class, Update Class, Save Comment.
- Course: New Course Type, Sort Courses, Update Course Type, Delete.

## Skipped or blocked

- No authentication block currently.
- Participant contact details were visible during class inspection but are intentionally excluded from audit artifacts.
- EnrollwarePay Portal client-side subnavigation was not forced when normal links exposed no navigable URL.
- Subscription Billing setup and all state-changing configuration flows were intentionally not entered.
- Lower-privilege behavior was not tested because no impersonation or alternate account was authorized.

## Final coverage totals

- Approximately 45 distinct Admin list/detail/settings/report screens visited.
- 200 Help articles inventoried; 68 high-value articles reviewed in full.
- 30 tenant notifications reviewed; 345 dated What's New entries inventoried.
- Approximately 214 meaningful controls/actions harvested and deduplicated into 40 operational concepts.
- Zero mutations, messages, payments, card actions, imports, uploads or settings changes.
