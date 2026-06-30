# Class bridge page copy cleanup

Updated customer-visible internal bridge-page wording while preserving registration behavior and HSI BLS Challenge warnings.

## Replacements
- `Mapped course details` -> `Important class details`
- `Structured course metadata is shown before schedule alternatives.` -> `Please review the class details before continuing to registration.`
- `The page uses structured course metadata for certifying body, course family, delivery type, and registration routing.` -> `Please review the class details, date, location, and registration path before continuing.`

## Source and rendered output
- Source/template fixed: `scripts/build_landers.py`
- Rendered class pages updated: 205
- Bridge pages scanned: 296
- HSI BLS Challenge warning preserved: not removed by this change

## Remaining markup notes
`ForwardToEnrollware` remains in href/JavaScript routing because it is the bridge trigger, not customer-visible button copy.

## HSI Challenge warning note
The current rendered `docs/classes/13601272.html` contains the HSI BLS Challenge label, but the expanded assessment-only/no-remediation/no-refund warning set is not present in the current page content. This cleanup did not remove warning copy; adding fuller challenge warnings should be handled as a separate content task.
