# Enrollware weird options — owner review

These are not automatic build requirements. Each is evidence that a repeated exception became operationally important. Owner decision should be **use**, **never use**, **automate**, or **retain as advanced escape hatch**.

| # | Weird/interesting option | Likely reason it exists | LanderWare treatment to consider |
|---:|---|---|---|
| 1 | Reschedule insurance | Customers resist or abuse move fees; policy becomes a purchasable product | Policy-driven entitlement, not a checkbox |
| 2 | Prevent reschedule within N days | Late moves strand seats and instructors | Derived cutoff with audited override |
| 3 | Cross-course reschedule | Real corrections do not always stay inside one course | Preserve supersession plus price/requirement delta |
| 4 | “Will call to schedule” | Payment/intake can precede a committed session | First-class unscheduled registration state |
| 5 | Linked classes use the same seats | Several listings may consume one physical capacity | Shared capacity resource |
| 6 | Consider existing classes when offering appointment slots | Flexible scheduling can double-book resources | Automatic conflict engine |
| 7 | 24-hour appointment availability | Some corporate/shift operations happen outside normal windows | Explicit exceptional availability policy |
| 8 | Hide empty and appointment classes | Operational lists become noisy at scale | Saved/derived view preference |
| 9 | Close registration days plus hours before class | Day-only cutoff is too coarse | Single computed close instant |
| 10 | Student-to-manikin ratio | Capacity depends on equipment, not just room seats | Resource constraint on session |
| 11 | Multiple keycode banks per course | Inventory may differ by owner, SKU, version or acquisition batch | Canonical pools and event ledger |
| 12 | Recycle/unassign a keycode | Mistaken issuance must restore inventory without erasing evidence | Reversal event with reason/actor |
| 13 | Existing manual ownership during registration | Required material may already be owned and current | Requirement satisfaction evidence |
| 14 | Print location on card | Credential output rules vary by customer/body | Credential-profile rule derived by issuer/course |
| 15 | Default product preselected | Upsell convenience can become accidental purchase | Avoid default purchase unless explicitly justified |
| 16 | Email-domain-restricted promo | Corporate eligibility may be inferred from email domain | Prefer organization relationship; domain only as hint |
| 17 | Strict AVS | Fraud/chargeback pressure can outweigh conversion loss | Risk-tiered payment policy |
| 18 | Capture IP for chargeback | Processor evidence may be needed months later | Privacy-limited payment evidence with retention policy |
| 19 | Green/gray card checkmark workaround | Vendor truth and local projection can diverge | Explicit external reconciliation state |
| 20 | Unlock a finalized roster | Legitimate corrections occur after operational close | Privileged reopen with reason and immutable audit |
| 21 | Receipt sent to another address | Payer, participant and recipient are distinct | Model roles explicitly |
| 22 | Read-only instructor | Former/limited staff may need visibility without mutation | Field/action RBAC |
| 23 | Instructor bidding | Assignment may be an offer rather than a command | Optional staffing workflow, likely P3 |
| 24 | Course-specific sidebar/confirmation CC | Each course/client accumulates communication exceptions | Template/rule inheritance with minimal overrides |
| 25 | Prevent archived location from new scheduling while retaining classes | History must remain visible after a venue closes | Already supported better via scheduling status |

## Owner questions

1. Which of reschedule insurance, late-move fees and cross-course moves are actually used at 910CPR?
2. Are shared-capacity/linked classes needed, or can one canonical session own all listings?
3. Which inventory pools are owned by 910CPR versus a corporate customer?
4. Do instructors ever bid, or is direct assignment sufficient?
5. Which payment/refund actions must Customer Service perform without owner approval?
6. Is participant-provided manual ownership accepted without staff verification?
7. Which historical Enrollware settings are legacy clutter and should be deliberately unsupported?

