# Archived Location Export Evidence Review

The workbook contains **343 rows**, **338 distinct names**, and durable Enrollware location IDs plus abbreviations/directions. It does not contain an active/archive status column, so it cannot safely assign current scheduling status by itself.

It exactly supports 124 of the 126 previously proposed historical location identities, covering 3,778 historical rows. It also provides enough exact evidence for three additional safe resolutions:

- `19 Oak Ridge Dr, Colchester, CT` — source ID `100332`, 40 rows; historical-location candidate.
- `Balfour Beatty US - Office` — source ID `93866`, 29 rows; historical-location candidate with a stated Wilmington address.
- `Geosyntec Consultants of NC P.C.` — source ID `128163`, 15 rows; exact-address alias to the existing Geosyntec canonical location.

Those three reviewed mappings would reduce unresolved location rows from **421 to 337**, raise fully canonicalized sessions from **3,439 to 3,458**, and raise sessions accepted under the historical contract from **3,570 to 3,589**. They were simulated only; no production records or aliases were created.

The workbook does not justify resolving generic labels such as `CT - Colchester`, `Camp Lejeune`, or `910CPR's Office`, and it does not change the source-only classification for placeholders or private one-time locations without sufficient reusable-location evidence.

## Archive behavior clarified

Admin “Archive location” should be an audited transition to `inactive`. Inactive and `historical_only` locations must be excluded from future-session pickers and appointment generation. Existing sessions/classes must continue to display and retain the location relationship regardless of the location's current status. A separate admin view can include archived locations and explicitly reactivate them.
