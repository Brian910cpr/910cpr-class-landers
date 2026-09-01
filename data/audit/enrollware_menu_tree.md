# Enrollware Admin menu tree

Observed read-only on 2026-09-01 using the authenticated 910CPR Admin UI. ✓ visited; ◐ inventoried but not opened deeply; ✗ stopped at mutation boundary.

```text
Classes and Students
  ✓ Upcoming Classes
      ✓ Existing Class Detail
          ✓ Student roster
          ✓ Communications / exports / payments / scores / certificates / documents
          ✗ Import / Quick Add / Add Student / Delete / Finalize / Print Cards / Update
  ✗ Schedule a Class — create boundary
  ✓ Past Classes
  ✓ Appointment Classes
  ✓ Instructor Bidding
      ✗ Save Bids / Email Instructors / Manage Bids
  ✓ Keycode Sales
  ✓ Student Search
  ✓ Unscheduled Students
  ✓ Shipping

Clients
  ✓ Manage Clients
      ✓ Existing Client Detail
      ✗ New / Update / Delete
  ✓ Client Activity Report

Instructors
  ✓ Instructor Records
      ✓ Existing User/Instructor Detail
      ✗ Add / Update / import / bulk email
  ✓ Expiring Certifications
  ◐ Instructor Export — download not triggered

Reports
  ✓ Activity Report
  ✓ Class Report
  ✓ Product Add-on Report
  ✓ Promo Code Report
  ✓ Registration Report
  ✓ Student Export
  ✓ Student Self Reschedule Log
  ✓ Event Log
  ✓ Download Documents

EnrollwarePay
  ◐ Merchant Capital Advance
  ✓ Payment Report / Funding Report
  ✓ Virtual Terminal
      ✗ Process Payment
  ✓ QuickBooks Sync
      ✗ Sync / Ignore / Disconnect
  ✓ EnrollwarePay Help

EnrollwarePay Portal
  ◐ Payment Dashboard
  ◐ Transaction Search
  ◐ Payment Reports
  ◐ Terminal Management
  ◐ Capital
  Note: menu items had no ordinary navigable href in the inspected Admin DOM.

Settings
  ✓ Course Types
      ✓ Existing Course Detail
      ✗ New / Sort / Update / Delete
  ✓ Appointments
      ✓ Existing Appointment Detail
      ✗ Create / Update / Delete
  ✓ Product Add-ons
      ✓ Existing Add-on Detail
      ✗ New / Update / Delete
  ✓ Online Keycodes
      ◐ Bank details not opened because recycle/assignment controls are mutation-adjacent
  ✓ Promo Codes
      ✓ Existing Promo Detail
      ✗ New / Update / Delete
  ✓ Locations
      ✓ Existing Location Detail
      ✓ Archived-location visibility control identified
      ✗ Import / New / Update
  ✓ File Manager
      ✗ Upload / change boundary
  ✓ Site Settings
      ✗ Update / DNS validation / reset
  ✓ Card Settings
      ✗ Test / Save
  ✓ Certificates
      ✗ Upload
  ✓ Email Campaigns
      ✗ New / edit / add email
  ✓ Text Messaging
      ✗ Save / add / edit
  ✓ Users
      ✓ Existing User Detail
      ✗ Add / update
  ◐ Subscription Billing Info

Help
  ✓ Search Help — complete 200-article tree inventoried
  ◐ Support Request — submission boundary
  ✓ What's New — 345 dated entries inventoried
  ◐ Quick Start PDF
  ✓ Keycode Guide
  ✓ Email Campaign Guide

Global
  ✓ Notifications — all 30 available entries reviewed
  ◐ My Account — account mutation surface not inspected deeply
  ✗ Log Out — not invoked
```

The UI strongly supports a shared-workspace interpretation: class, registration, client, instructor, location, payment, credential and document data are interlinked, while role settings mainly change what actions and records are surfaced.
