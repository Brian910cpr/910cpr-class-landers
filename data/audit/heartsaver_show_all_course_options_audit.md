# Heartsaver Show All Course Options Audit

Show all course options now exposes all six valid AHA Heartsaver options with scheduler rules and public offers. USCG 253768 remains excluded by policy and is not configured.

## Summary

- `known_heartsaver_courses`: 7
- `visible_by_default_count`: 3
- `visible_with_show_all_count`: 6
- `excluded_count`: 1

## Visible By Default

- `344085` AHA Heartsaver CPR AED (IP), offers `512`
- `209809` AHA Heartsaver First Aid CPR AED (IP), offers `483`
- `251545` AHA Heartsaver Pediatric First Aid CPR AED Online (BL), offers `512`

## Visible With Show All

- `344085` AHA Heartsaver CPR AED (IP), offers `512`
- `209808` AHA Heartsaver CPR AED Online (BL), offers `512`
- `209809` AHA Heartsaver First Aid CPR AED (IP), offers `483`
- `329495` AHA Heartsaver First Aid CPR AED - Blended (BL), offers `512`
- `351632` AHA Heartsaver Pediatric First Aid / CPR / AED (IP), offers `483`
- `251545` AHA Heartsaver Pediatric First Aid CPR AED Online (BL), offers `512`

## Excluded

- `253768` USCG Elementary First Aid | CPR (AHA Heartsaver) (ILT)
  - Reasons: `not configured, disabled by policy, no public offers`
  - Not listed in data/config/block_schedule_pages.json for the Heartsaver page.
  - Blocked by public_offer_policy disabled course ID/family rules.
  - Not enabled by public_offer_policy enabled IDs/families.
  - Current Heartsaver block schedule report generated zero public-selectable offers for this course ID.
