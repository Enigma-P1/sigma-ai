# Mike Alvarez — day-shift production supervisor, plastics plant (injection moulding)

Gate 2 persona, written 2026-08-13 BEFORE seeing any screen. Deliberately not
warehousing: the first two testers were both order-picking, and re-testing the
same domain would only prove we fixed that domain. His file is
`data/M4_Daily_Production.xlsx` — 80 rows, mixed date formats, Y/yes/YES/no/N/blank
in one column, percentages written both `4.77%` and `.0211`, three spellings of
each operator, free-text reasons that mean the same thing, and rows where the
quantities do not add up because a counter was reset.

---

My name is Mike Alvarez. I’m the day-shift production supervisor at a small plastics plant that makes caps and closures for detergent and cleaning-product companies. We have 48 people in the plant. Twelve operators report directly to me, and I’ve been here 11 years, with the last four as supervisor.

The problem I actually have is startup scrap on Injection Molding Machine 4. Every time we change from one resin colour to another, we throw away a pile of parts while the operator gets the colour and weight back into spec. It is worse on the first job after the weekend, but it happens during the week too.

The target is less than 1% scrap. On Machine 4 we have been more like 3% to 5%. That sounds small until you do the math. A normal run is 18,000 caps. At 4% scrap, that is 720 caps gone. The material itself is about $85, but the bigger cost is the machine running and somebody sorting or regrinding the bad parts. I figure it costs us around $250 to $400 per bad changeover. We average three or four colour changes a week, so I’m losing roughly 10 to 14 hours a month and probably $4,000 to $6,000 a year. Twice last month we also had to run overtime to make up the good quantity.

I know it is a problem because the production report comes to me every morning and I see the scrap percentage. The operators also complain about it. Their version is usually, “The first 20 minutes were garbage again.” Maintenance says the machine is fine. Quality says the colour was out of tolerance. The operator says the previous shift left the barrel at the wrong temperature. Everybody has a theory and nobody has shown me which one actually lines up with the bad runs.

The data I have is a spreadsheet called `M4_Daily_Production.xlsx`. One of the leads updates it, but not always on the same day. It has one row per production run and these columns:

`Date`, `Shift`, `Machine`, `Job/Part`, `Colour`, `Operator`, `Planned Qty`, `Good Qty`, `Scrap Qty`, `Scrap %`, `Changeover?`, `Startup Scrap`, `Downtime Min`, and `Reason`.

Some people type “yes,” some type “Y,” and some leave the changeover column blank. Scrap percentage is sometimes typed as `4.2%` and sometimes as `0.042`. The reason column is free text. “Color,” “colour,” “shade,” and “off colour” all mean roughly the same thing. There are about 80 rows from the last six weeks. These are ten rows copied from it, with the same sort of mess in them:

```text
Date       Shift  Machine  Job/Part  Colour  Operator  Planned Qty  Good Qty  Scrap Qty  Scrap %  Changeover?  Startup Scrap  Downtime Min  Reason
6/3/26     D      M4       C-118     Blue    J. Patel   18000         17142     858        4.77%    Yes           620             18             off colour
06-04-2026 D      M4       C-118     Blue    J Patel    18000         17620     380        .0211    Y             240             9              colour slow to settle
6/5/26      D      M4       C-204     White   R. Singh   16000         15890     110        0.69%    no            0               4              normal run
6/8/26      D      M4       C-331     Green   L. Morris  20000         19110     890        4.45%    yes           710             22             resin purge / colour
6/9/26      D      M4       C-118     Red     J. Patel   18000         17795     205        1.14%    Y             130             7              startup pieces
6/10/26     D      M4       C-204     White   R Singh    16000         15540     460        2.875%   Yes           390             12             machine temp?
6/11/26     D      M4       C-331     Green   L Morris   20000         19880     120        0.6%     N             0               3              -
6/15/26     D      M4       C-118     Blue    J.Patel    18000         16950     1050       5.83%    yes           800             27             shade out / waited for QA
6/16/26     D      M4       C-204     White   R. Singh   16000         15780     220        1.38%    blank         180             8              colour change maybe
6/17/26     D      M4       C-118     Red     T. Gomez   18000         17430     570        3.17%    YES           450             15             first run after clean
```

The dates above are just examples, not the full file. There are also a few rows where Good Qty plus Scrap Qty does not exactly equal Planned Qty because the operator stopped early or the counter was reset. I don’t want to spend the whole hour pretending the spreadsheet is cleaner than it is.

What I want from the software is fairly simple. I want to get this file in, make the columns understandable, and see whether startup scrap is actually worse after a colour change, by colour, operator, shift, or reason. I would like something I can point at and say, “These 11 changeovers account for most of the waste, and this is what they have in common.” If it can help me clean up “yes,” “Y,” and “blank,” that would be useful too.

I do not need it to tell me that variation is bad. I need a picture or table that helps me decide what to try on Monday. For example, maybe we need a standard purge amount for blue resin, or maybe the problem only happens when the barrel has been cleaned. If the software gives me a bunch of statistical terms without telling me what to click or what the result means, I’ll close it. If it refuses the file because one percentage is written as `4.77%` and another as `.0211`, I’ll probably never open it again. Same if I have to manually enter all 80 rows.

For the first hour, this is what I would try:

1. I will open the app for the first time and look for something that sounds like a new analysis, project, worksheet, or import. I expect to see some obvious way to start with a spreadsheet. If the first screen is just a blank technical diagram with no explanation, I will already be annoyed.

2. I will make a new project called `Machine 4 Startup Scrap - June 2026`. I expect the app to give me a blank project or workspace and let me name it.

3. If it asks what I am trying to improve, I will type exactly: `Reduce startup scrap after colour changes on Injection Molding Machine 4`. I expect that text to be saved somewhere visible, not disappear after I move to the next screen.

4. I will import `M4_Daily_Production.xlsx`. If it asks which sheet, I will choose the sheet named `Daily Production`. I expect it to show me a preview of the rows before importing them.

5. In the preview, I will check whether it recognizes these as columns: `Date`, `Shift`, `Machine`, `Job/Part`, `Colour`, `Operator`, `Planned Qty`, `Good Qty`, `Scrap Qty`, `Scrap %`, `Changeover?`, `Startup Scrap`, `Downtime Min`, and `Reason`. I expect it to either recognize the numbers or tell me which columns it cannot read.

6. If it asks me to identify the type of each column, I will set Date to date, Shift/Machine/Job/Part/Colour/Operator/Changeover?/Reason to text or category, and Planned Qty/Good Qty/Scrap Qty/Startup Scrap/Downtime Min to number. I will set Scrap % to percentage. I expect the app to show me how it interpreted `4.77%` and `.0211`; both should become about 4.77% and 2.11%, not 477% and 0.0211%.

7. If there is a cleaning or find-and-replace screen, I will try to combine the obvious changeover entries. I will replace `Y`, `yes`, and `YES` with `Yes`, and `N` and `no` with `No`. I will leave the blanks alone for now rather than guessing. I expect to see how many rows were changed.

8. I will look for a summary of the imported data. I want to see the number of rows, missing values, and any columns with text where the app expected numbers. I expect it to flag the blank Changeover cells and the inconsistent reason wording instead of quietly making bad assumptions.

9. I will find whatever screen makes a chart or summary, and make `Scrap %` the result I am looking at. If the app asks for a measure, I will choose `Scrap %`; if it asks for a grouping, I will first choose `Changeover?`. I expect to see scrap for Yes versus No, preferably with the number of runs behind each result.

10. I will then filter Machine to `M4`, because I do not want another machine muddying this question. I expect the chart or table to update and show only Machine 4.

11. I will filter the date to June 3 through June 30, 2026, or use the whole imported file if the date filter is easier. I expect the software to tell me how many rows remain after filtering.

12. I will compare `Changeover? = Yes` with `Changeover? = No` using Scrap % and Startup Scrap. I expect the Yes group to be noticeably worse, around 3% to 5%, and the No group to be closer to 1%. If it gives me only an average with no run count, I will not trust it much.

13. I will look for a way to break the Yes group down by `Colour`. I expect Blue and Green to show more startup scrap than White, because that is what the production reports seem to suggest. I want both the average scrap percentage and the total startup scrap count.

14. I will make another view grouped by `Reason`. Before doing anything complicated, I will see whether “off colour,” “colour slow to settle,” “resin purge / colour,” and “colour change maybe” appear as separate categories. I expect to discover that the messy wording makes the result less useful. If there is a simple way to combine them as `Colour/colour settling`, I will try it and note how many rows are included.

15. I will look for a Pareto, ranked bar chart, or plain sorted table of scrap by reason. I will type `Rank reasons for startup scrap on M4` if the app has a question box or analysis prompt. I expect the largest reasons to be listed first, with the amount of scrap and number of runs, not just a colourful chart with no labels.

16. I will check whether the app can compare `Operator` and `Shift` without making that look like an accusation. I will type or select `Compare startup scrap by shift and operator, but show run count`. I expect it to warn me if one operator only has one or two runs, because that would not be a fair comparison.

17. I will look at `Downtime Min` alongside `Startup Scrap`. I expect to find out whether the bad runs also take longer. A useful result would be something like, “Changeovers with more than 15 minutes downtime average 4.8% scrap, versus 1.2% under 15 minutes.” I am not expecting a fancy explanation, just a clear comparison.

18. I will try to save or export the most useful result as a report or image. The result I want saved is a simple page titled `M4 Colour Change Startup Scrap`, showing total runs, average scrap for changeovers versus non-changeovers, the top colour or reason, and the number of rows used. I expect to be able to print it or send it as a PDF.

19. If there is a notes, comments, or conclusion area, I will type: `Trial standard purge and barrel-temperature check on M4 for Blue and Green changeovers. Record first 20 minutes separately for two weeks.` I expect the project to retain that note with the analysis.

20. Before closing, I will reopen the project or return to its main page to make sure the imported file, cleaned values, chart, and note are still there. I expect not to lose the work just because I clicked to another screen.

At the end of the hour, I need to be holding one plain-English page showing whether colour-change runs really have higher startup scrap on Machine 4, which colour or reason is worst, and how many runs support that conclusion; I would show it to my plant manager and the quality lead.

---

