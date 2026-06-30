# BLS cap ordering recommendation

Recommendation: C. Add a BLS-specific cap preference layer.

This has been implemented only for reviewed AHA BLS course IDs `209806`, `359474`, and `210549`. It sorts cap candidates by the BLS preferred time order from `data/config/seed_strategy_policy.json` before weekly/day/course caps are consumed.

Why not increase caps: the current issue is ordering, not proven lack of capacity. Increasing caps would expose more generated rows without first choosing better rows inside existing limits.

Residual issue: after preferred-time rows survive public-sellable caps, seed selection still chooses the first BLS family/course-priority row per date. That currently favors AHA BLS Provider Initial over Renewal. Fixing Initial/Renewal balance should be a separate seed-selector policy change, not a public-sellable cap change.
