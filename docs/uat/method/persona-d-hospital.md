# Mike Kovacs — production supervisor, Food & Nutrition, 290-bed hospital

Gate 2 persona, written 2026-08-13 BEFORE seeing any screen. Their file is
`data/tray times 2025.xlsx` — 70 rows off a clipboard: the meal coded five ways
(L / lunch / D / dinner / B), times written `4:10` and `415pm`, dates as
`3/3/25`, `3/4`, `3/10 Mon` and `3/7 dinner` (the meal leaked into the date
column), one row with no times at all, and an author column of JR / MV / me /
blank. Do not clean it up — they said explicitly they are not cleaning it up for
anybody, and that is the test.

---

My name is Mike Kovacs. I'm the production supervisor in Food & Nutrition at Westfield Memorial Hospital — 290 beds, not-for-profit, one kitchen, we do patient trays, a small cafeteria, and the usual doctor-lounge catering that always shows up as a surprise. Ten people report to me on days: three cooks, two prep, four on the trayline, and a potwash lead who also runs trays when we're in the weeds. I've been in this kitchen seventeen years, supervisor for eight. I can run a trayline in my sleep. I am not a Six Sigma person. Someone said that phrase in a leadership meeting last fall and I nodded like I knew what they meant.

The thing that's been chewing on me for months is lunch. First patient cart is supposed to hit the elevator at 11:40. Last cart by 12:10. That's the deal I have with nursing. We are not hitting it. Most days first cart is 11:52 to 12:05 and last cart is 12:20, 12:30, I've seen 12:40. Food's been sitting under the heat lamps, nursing starts calling at 12:15, patients get pulled for tests before the tray arrives, and then we remake the damn thing at 1:00 when they're back and the original is garbage. I count pink remake slips out of the drawer. Lunch is 12 to 18 remakes on a normal day, 20-plus if the printer jams or it's a new menu. Half of those remakes are "food cold" or "patient not in room." Trayline stays 30 to 45 minutes late, which shoves dinner, so now dinner is late too and I'm paying overtime on both ends. I figure 20, 22 hours of OT a week that's really just lunch bleeding into everything. Average rate on my crew is about $21.50, so call it $450 a week I'm lighting on fire, not counting the food we throw away. Patient Experience sent me the comment dump from February — 23 comments that were some version of cold, late, or never showed up. My director, Patricia Holm, put "meal delivery timeliness" on my evaluation in January and she has not let it go. I know it's a problem because Jorge writes the times on the clipboard by the starter station, nursing emails me in all caps, and Patricia forwards me the comment report every Monday like I haven't already had a shit morning.

The data is bad. There's a clipboard. Jorge or Maria scribble on it if they remember. I typed some of it into a spreadsheet on the shared drive on Fridays when I wasn't covering a call-off. File is called tray times 2025.xlsx. Columns are whatever I made up: date, meal, start, first cart, last cart, trays, remakes, notes, who. It looks like this, and I am not cleaning it up for anybody:

3/3/25 | L | 11:20 | 11:54 | 12:24 | 208 | 14 | tickets late again | JR
3/3/25 | D | 4:10 | 4:38 | 5:09 | 191 | 6 |  | JR
3/4 | B | 6:50 | 7:22 | 7:48 | 176 | 3 | 2 late admits flr 3 | MV
3/4 | lunch | 11:25 | 12:01 | 12:31 | 215 | 17 | new cook on hot line (Derek) | JR
Wed lunch |  |  |  |  | 220 | 11 | forgot times. last cart was after 12:20 I know that | me
3/6/25 | L | 11:18 | 11:49 | 12:19 | 211 | 9 | pretty good day | JR
3/6 | D | 4:00 | 4:44 | 5:20 | 188 | 12 | steam table down 20 min | JR
3/7 | L | 11:35 | 12:08 | 12:36 | 203 | 21 | printer jam + 4 isolation + puree backed up | MV
3/7 dinner | 415pm | 4:50 | 5:18 | 194 | 8 | started late bc lunch | MV
3/10 Mon | L | 11:22 | 11:58 | 12:28 | 219 | 16 | always bad on Mondays?? | JR
3/10 | D | 4:05 | 4:35 | 5:02 | 186 | 5 |  | JR
3/11 | L | 11:19 | 11:47 | 12:15 | 207 | 8 | Patricia was watching lol | JR

That's what I have. I do not have ticket-print times out of CBORD because I don't know how to run that report and IS takes three days to call back. I do not have a timestamp for when the hot line actually plates the entree. I have a clipboard and a Friday spreadsheet.

What I want from this thing is pretty simple. I want to put those numbers in and have it tell me what's actually making lunch late so I can change one thing next week. Tickets printing late? Hot line not ready? Isolation trays? Puree station bottleneck? Mondays? I don't know and I'm tired of guessing in the huddle. I will keep using it if I can walk out with one clear cause I believe and something I can try on the line Wednesday. I will close it and never open it again if it asks me what a sigma is, if it wants a project charter, if it makes me pick a "CTQ," or if the first screen looks like a stats class. Don't make me define a defect in software-speak. A defect is a cart that misses 11:40. That's it.

Next hour, this is what I'm going to try, in order, first time opening the thing:

1. Open the app. I expect a start screen or a blank page or a button that says start or new or something a normal person would click. If it opens on a tutorial I will skip it.
2. Look for a way to start a new thing. If it asks for a name I will type: lunch carts late
3. If it asks what the problem is I will type exactly this: lunch patient carts leaving the kitchen late. first cart should be 11:40 last cart 12:10. we are 15 to 25 minutes late most days.
4. If it asks what "good" looks like I will type: first cart on the elevator at 11:40, last cart by 12:10, fewer than 8 remakes at lunch.
5. If it asks how I measure it I will type: clipboard times for first cart and last cart, and I count pink remake slips.
6. If it wants a target number I will put 11:40 for first cart and 12:10 for last cart. I don't know if it wants minutes-late or clock times. I'll try clock times first. If that pisses it off I'll put minutes late: 0 is the target, 15 is typical, 25 is a bad day.
7. Find wherever you type in data. I expect a table or a form. I am going to type the twelve rows I wrote above, messy, exactly like that, including "Wed lunch" and "415pm" and the blank cells. I am not cleaning my data for a free app.
8. If it refuses the messy rows I will try just the lunch rows that have real times: 3/3, 3/4, 3/6, 3/7, 3/10, 3/11. That's six lunches. Dates 3/3/25, 3/4/25, 3/6/25, 3/7/25, 3/10/25, 3/11/25. First-cart times: 11:54, 12:01, 11:49, 12:08, 11:58, 11:47. Last-cart: 12:24, 12:31, 12:19, 12:36, 12:28, 12:15. Remakes: 14, 17, 9, 21, 16, 8.
9. If it asks for a column name for the main number I will call it minutes late first cart. I'll calculate those: 14, 21, 9, 28, 18, 7. Target is 0. Spec I guess is 0 — wait, they want first cart at 11:40 so anything after that is late. I'll say upper limit 0 minutes late. If it needs a lower limit I don't have one, early is fine.
10. If it asks what a defect is I will type: first cart after 11:40 or last cart after 12:10 or more than 8 remakes.
11. Look for a button that says why, or cause, or analyze, or the thing that tells me what's going on. I expect it to do something with the numbers I typed. I do not expect to already know the name of the tool.
12. If it asks me to list possible causes I will type these, in this order, because these are the things we yell about in the kitchen: tickets printing late, hot line entree not ready, puree and thickened liquids station backed up, isolation trays, late diet changes from nursing, printer jams, new staff on the line, Mondays after the weekend census dump, steam table or equipment down.
13. If it wants me to pick the biggest cause I don't know the biggest cause, that's the whole point, so I will not guess just to make the software happy. If it forces me to pick I will pick tickets printing late because that's what Jorge writes most often.
14. If it has a place for how much this costs I will type: 22 hours overtime a week at 21.50 is about 450 a week, plus remake food about 80 a day, plus the Press Ganey comments Patricia keeps forwarding.
15. Try to get it to use the notes I already have — "tickets late again", "new cook on hot line (Derek)", "printer jam + 4 isolation + puree backed up", "always bad on Mondays??", "Patricia was watching lol". Those notes are the closest thing I have to causes. If it can't read a notes column I will copy them into whatever cause box it gives me.
16. Look for anything that says what to do next or what to try. I expect one or two actions, not a 12-week project plan. If it tells me to form a team and hold a kickoff I am done.
17. Find a way to print or save a single page. I need something I can hold. PDF, print, screenshot, I don't care.
18. If at any point it asks for mean, standard deviation, DPMO, sigma level, or a control limit, I will ignore that screen and go back. I am not calculating a standard deviation on six lunch times in an hour I don't have.
19. If I get stuck I will search inside the app for the word late or the word cause or the word defect. I will not read a help manual.
20. Before I close it I will try one more time to get a sentence out of it that I could actually say out loud in the 9:00 huddle. Something like "lunch is late because of X." If I cannot get that sentence the hour was a waste.

I would have to be holding one printed page that says why our lunch carts are late and what to try first on Wednesday, in words I can say to Patricia without looking like an idiot.

