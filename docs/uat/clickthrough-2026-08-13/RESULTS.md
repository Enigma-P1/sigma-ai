# Gate 1 cold-start click-through — driven run, 2026-08-13

The v0.2.0 checklist from `docs/RELEASE-v0.2.md` Gate 1, performed by
`desktop/uat-smoke/clickthrough.mjs` against the production bundle at the
release commit (`69b170c`) and a real engine on a fresh projects root.
Method: the UAT harness (`docs/uat/method/harness.mjs`) — production
`dist`, real cross-origin engine calls, real downloads.

The install/launch half of Gate 1 was verified separately by Shawn on real
Windows hardware the same day: the released .msi installed, launched past
SmartScreen, and rendered the on-disk project list (which requires a live
engine). The macOS build is machine-verified only (CI engine smoke inside
the .app) — no human has run the installed Mac app; the release notes must
say so.

| Step | Result |
|---|---|
| Create a project | PASS — DMAIC phases rendered |
| Import `ErrorLog_Sept.xlsx` | PASS — saved; rows view offered |
| Pareto from the imported file | PASS — `Wrong Part`: 5 of 7 carry 87.0% of 69 rows |
| Download chart as picture | PASS — real PNG, 122 KB (`pareto.png` here) |
| One-page summary | PASS — real PDF, 116 KB (`summary.pdf` here), gaps named, provenance footer |
| Quit + relaunch (engine killed and restarted) | PASS — project listed on disk and reopens |

Also observed, working as designed: with a meaningless category column
(`Order #`, all-unique) the Pareto banner says so in plain words instead of
drawing a fake vital-few.

Leftovers noted for the next build (none block v0.2.0):
- window title still reads "Sigma AI — Packaging Spike" (`tauri.conf.json`)
- engine package version string still `0.1.0` (PDF footers print
  "engine v0.1.0"); bumping it requires a golden refreeze, so it is a
  deliberate v0.3 item, not a quick edit
- the Mac dmg filename said `0.1.0` — fixed in `release.yml` in this commit
