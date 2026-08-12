# Mike Thompson — warehouse ops supervisor, aftermarket auto parts

Written in persona, from this tester's own screenshots and run log — 17 planned steps, driven for real on 2026-08-12. Not edited. See `README.md` for the method and the triage.

---

## xai · `grok-4.3`
*tokens: 71566 in / 2026 out*

**Here's the straight write-up on what happened.**

I opened it cold like I said. First screen said “Sigma AI” and “A guided Green Belt DMAIC flow.” There was a box for Project name* and a Create project button that was greyed out until I typed “Picking Errors Sept.” The folder ID filled itself in as “picking-errors-sept.” No “New Project” button anywhere. Shots 01-open-and-create-01-cold-start.png and 01-open-and-create-04-typed-project-name.png show exactly that.

Clicked Create project and it made the thing in about a second and a half. What I got was not a blank table or dashboard. I got a long rail on the left with 26 tools split into seven phases: INTAKE, DEFINE, MEASURE, ANALYZE, IMPROVE, CONTROL, WRAP. Every phase except Intake said “Needs earlier steps (can override).” The main pane landed on T-01 with five Yes/No questions about scope and whether a process owner cares. Sixty clickable things on that screen. Shots 01-open-and-create-05-after-create.png and 01-open-and-create-06-after-create-full.png.

I hunted for import. Nothing on the main project screen. No “import,” no “upload,” no Excel or CSV wording at all. I had to open every one of the 26 tools. Only T-11 (“Data Collection Plan (+ sample-size guidance)”) had a file box, and even then the tab just said “Import Data.” I picked ErrorLog_Sept.xlsx. It took it in about 2.7 seconds, said 69 rows, and showed a quality scan that listed 59 issues (8 missing order numbers, 4 missing right parts, 47 missing notes). It kept the duplicate header row from my spreadsheet as actual data and never told me. The column-type dropdowns all defaulted to “text” even for the part numbers and order numbers. Sample values for Date showed both date formats side by side. Shot 03-import-excel-04-type-question.png.

I could not type the two test rows in by hand. The data table on T-11 is read-only. Clicking a cell did nothing. No add-row button anywhere on that screen. The closest thing was T-08 Check Sheet / Tally, which only wants category names and counts. I stuck the two wrong part numbers in as categories and put a count of 1 on the first one. No place for date, no place for order number, no place for the right part. Steps 6 and 7 were flat impossible. Shots 05-manual-rows-01-t11-saved-state-full.png and 05b-manual-rows-tally-02-t08-transcribe-full.png.

No “Analyze” button and no “Find Patterns” button. ANALYZE is just a phase header on the rail and it is not clickable. The “I’m stuck” pop-up said the routing tree for Intake hasn’t shipped yet. The three tools under ANALYZE are all manual forms; none of them looked at my imported file. Shot 06-analyze-button-01-home-hunting-analyze-full.png.

T-14 is the only tool with charts. I picked my dataset and set the category column to Wrong Part. It drew a Pareto and said “Vital few: 22187, 44521, 31104, 78802, 59310 account for 87.0% of 69.” Bars sorted by count, cumulative line. That is the first thing that actually gave me something I can use. When I switched it to Date it treated my two date formats as separate categories and gave a long list. Nothing anywhere mentions shift or time of day. The histogram and run chart panels just sat on “Waiting on the engine’s descriptive statistics…” because every column was typed text. Shots 07-analyze-tools-and-chart-06-t14-result-full.png and 08-pareto-and-filter-01-pareto-by-part.png.

No filter box, no search box. The only free-text field was inside the collapsed Advisor panel (“Ask about this project…”). I typed “show me only errors on first shift” and nothing happened to the chart. The advisor is off until somebody puts an API key in settings.json. Shot 08-pareto-and-filter-04-typed-filter-phrase.png.

Notes only live on whole tool forms, not on rows. I typed “bin A-14 keeps messing up” into T-01’s notes box and could not save it because five intake questions were still unanswered. No way to attach anything to specific errors.

Exports worked. I got a PNG of the Pareto, a Measure pack PDF, and a project record PDF. The PNG has the part numbers plotted as numbers on the x-axis (20k, 30k, etc.) so the bars have no labels and you cannot tell which bar is 22187. The cumulative line zigzags because of that. The on-screen version was fine; the downloaded picture is not. Shot 09-notes-and-export-03-after-exports-full.png and the file newplot.png.

Closed and reopened. The project and the 69 rows were still there. T-11 still showed the saved dataset with the timestamp. The Pareto rebuilt the same vital-few line. The chart settings themselves did not come back; I had to pick the dataset and column again. Shots 10-reopen-and-target-01-reopened-welcome-full.png and 13-final-reopen-06-final-pareto.png.

The Target box in the charter did nothing when I typed 20. The whole charter form stayed “Not saved yet” with a long list of missing fields. No defect-rate calculation anywhere.

Clicking a bar on the Pareto only popped up a label with the number as “(22.187k, 17).” No drill-down, no subset view. The word “brake” never appears because my spreadsheet has no part-type column.

No undo anywhere. No delete project, no archive, no trash. Right-click on the project card did nothing. Hover did nothing. Shot 12-undo-delete-01-step16-project-screen.png.

### What I could not do and how much I care
- Manually add or fix rows in the imported data. I care a lot. My ErrorLog is half garbage; I need to clean it without going back to Excel every time.
- Filter or slice the data (shift, time of day, picker, bin). I care a lot. That is exactly why I wanted the tool.
- Attach a note to specific rows. Medium. Nice to have but not the blocker.
- Delete a project or undo something. Low for now, but if I keep using it I will eventually create junk.

### Words and numbers I did not understand
“Vital few” and “cumulative share” on the Pareto banner. The screen explained it in plain words right under the chart, so that one was fine once I looked. SHA-256 fingerprint on the save message. DMAIC phase names and the constant “Needs earlier steps (can override)” banners. The advisor settings line about “Layer 2” and “plain text in settings.json.” None of it was explained on the screen; it just assumed I already knew.

### Did I get closer to the actual problem?
Yes, on one narrow thing. The Pareto told me five part numbers (22187, 44521, 31104, 78802, 59310) make up 87 % of the 69 logged errors. I can take that list to the shift lead Monday morning and say “move these five bins or double-label them.” That is something concrete I can act on. Everything else—the forms, the phases, the missing steps warnings, the charter that would not save—did not help me with picking mistakes. I would have nothing else to show my manager.

### Parts that were genuinely good
The Pareto in T-14 actually read my messy file and gave a ranked list of the real error parts with a clear percentage. It handled the duplicate header without crashing and still produced the number. The project and the saved dataset survived close/reopen without losing the 69 rows. Those two things worked the way I needed.

### Would I open it again?
I would open T-14 again if someone else had already imported the file, because the vital-few list is useful. I would not put my own data in it tomorrow for day-to-day work. Too many dead ends on the things I actually need (editing, filtering, simple notes). I would not tell another supervisor to try it unless they only wanted the one Pareto screen and were willing to ignore the rest.

### Three or four things I would want changed, in order
1. Let me edit or add rows directly to an imported dataset, or at least give a simple “add row” that matches the columns I already have. My log is never clean on the first try; fixing it in the same place I analyze it would save real time on the floor.

2. A plain filter or search box on the data view and on the Pareto so I can say “first shift only” or “bin A-14” and see the subset. Half my errors are shift-specific; without that split the vital-few list is only half useful.

3. Make the downloaded Pareto PNG actually show the part numbers as labels on the bars instead of treating them as numbers on a 20k–80k scale. The screen version is readable; the picture I would email or print is not.

4. Strip the constant “Needs earlier steps (can override)” banners and the five-question intake form off the tools I actually use. I do not need a DMAIC gatekeeper to look at my error log; I just need the chart.

That is everything I saw and everything that mattered to the job I actually do.

