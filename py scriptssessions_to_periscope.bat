py scripts\sessions_to_periscope.py         :: builds docs/periscope_full.json + docs/data/session-times.json + docs/sessions/index.html
py scripts\build_indexes.py                 :: refresh sitemap/robots (+ hide empty indexes)
git add -A
git commit -m "build: sessions → periscope + sitemap"
git push
