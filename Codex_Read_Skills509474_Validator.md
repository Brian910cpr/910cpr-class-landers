# Native skills publication validation

The public inventory validator now recognizes course 509474's native scheduling destination without requiring an Enrollware appointment container. It checks the page, instructor, resource, source trace, exact instruction/cleanup interval, current lease and matching native URL parameters. Existing Enrollware requirements remain unchanged.

Validation: 10 focused validator tests pass. Native skills CI also validates all three freshly generated public selectors using this production validator.
