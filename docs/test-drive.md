# Test drive: 20 minutes, real answers, see every tool work

Copy-paste answers that produce a genuinely good Green Belt project — not
filler. They're lifted from the Coffee Bar worked example, so the numbers
line up across tools and the app's honesty checks behave the way they
would on a real project.

**The story:** a campus coffee bar. Espresso orders take ~8.4 minutes from
register to handoff during the 7–10am weekday rush. People walk away, drinks
get comped and remade, staff burn overtime clearing the backlog. Goal: get to
5 minutes by October 31.

**Before you start — grab the data file.** Two tools (Baseline, Charts) need a
real dataset. On GitHub: open the repo → `demo` → `coffee-bar` → `measure` →
click **`wait-times.csv`** → the **Download raw file** button (top right of the
file view). Save it somewhere easy. 120 rows of real-shaped timing data.

---

## 1. Create the project

- **Project name:** `Coffee Bar wait time`
- Folder ID fills itself in. Click **Create project**.

---

## 2. T-01 Project Picker — "should this even be a project?"

Answer **Yes** to all five, with these details:

- **Narrow scope:** Espresso-drink orders during the weekday 7:00–10:00 morning peak at the campus coffee bar — not food, not drip-only, not weekends.
- **Measurable outcome:** Order-to-handoff time in minutes per order, lower is better. The register stamps the order time; handoff comes from a tally sheet at the pickup counter.
- **Data obtainable:** The register exports order timestamps to CSV daily; the shift lead trialed a phone-stopwatch handoff tally for two mornings in June and it held up during rush.
- **Owner engaged:** Priya Shah, morning shift lead, runs the counter and asked for the project. Cafe manager Dana Ellis sponsors it.
- **Impact plausible:** Q2 records put walk-aways, comped drinks, remakes, and peak-end overtime near $4,000 for the quarter — roughly $16,000 a year.

**Watch for:** it routes you to **full DMAIC**. If you'd answered "no" to
measurable outcome, it would have refused to route you into a full project —
that refusal is the tool working, not breaking.

---

## 3. T-03 Charter — the one that shows off the honesty checks

**Problem statement (four fields):**
- **What:** Espresso-drink orders take too long from register to handoff during the weekday morning peak, producing walk-aways, comped drinks, remakes, and peak-end overtime.
- **Where:** Campus coffee bar, front counter and espresso station.
- **When:** Weekday mornings, 7:00–10:00 peak; observed throughout Q2 2026.
- **Magnitude:** `8.4` / `minutes average order-to-handoff` / `Q2 2026, weekday 7:00-10:00 peak`

**Goal:**
- **Statement:** Reduce average order-to-handoff time during the weekday 7:00–10:00 peak from 8.4 minutes to 5.0 minutes by October 31, 2026.
- **Metric name:** Average order-to-handoff time, weekday 7:00–10:00 peak
- **Baseline:** `8.4`  **Target:** `5.0`  **Unit:** `minutes`  **Date:** `2026-10-31`
- **Consequential metrics:** `Drink remake rate (remakes per 100 orders)` and `Barista labor hours per morning shift`

**Scope:**
- **In:** Espresso-drink orders placed at the register during the weekday 7:00–10:00 peak: order-taking, drink preparation, and handoff.
- **Out:** Food orders, drip-only orders, mobile pre-orders, weekend service, the library cart, menu changes, and pricing.

**Business impact:** `16084` / `dollars per year` / basis: `COPQ calculator Q2 2026 total ($4,021) x 4 -- Q2 actuals x 4`

**Team:** Priya Shah (Morning shift lead, project lead) · Marcus Webb (Barista, morning shift) · Dana Ellis (Cafe manager, sponsor)

### Try breaking it on purpose (30 seconds, worth it)

Before saving the good version, temporarily put this in **What**:

> We need to buy a second espresso machine because orders take too long.

Save it and look at the checks strip. It flags a **solution-shaped problem
statement** — you've named the fix, not the problem, which is the single most
common Green Belt mistake. Put the real text back and watch the flag clear.
That's the whole design philosophy in one screen.

---

## 4. T-02 COPQ — where the $16,084 actually comes from

Four rows. Enter quantity and rate; the app does every multiplication:

| Category | Quantity | Rate | Basis |
|---|---|---|---|
| Rework | `320` | `1.1` | Remade drinks from the barista waste sheet, Q2 2026 |
| Custom — "Comped drinks (long-wait apologies)" | `210` | `4.8` | POS comp log, reason code 'wait' |
| Lost business *(tick "estimate")* | `378` | `5.25` | 10-morning walk-away tally extrapolated to 63 Q2 mornings |
| Overtime | `41` | `16.5` | Time-clock export, morning-shift overtime code |

Period on each: `Q2 2026`

**Watch for:** the total lands at **$4,021** for the quarter, which is exactly
the ×4 basis you typed into the charter. There's a cross-check that compares
the two and complains if they disagree — the numbers are supposed to tie out,
and the app enforces it. Also note the estimate row stays visibly marked as an
estimate rather than blending in with the receipts.

---

## 5. T-04 SIPOC — 5 minutes, gives the process a shape

**Process steps:** 1) Take order and payment at the register · 2) Mark the cup
and place it in the drink queue · 3) Prepare the drink at the espresso station
· 4) Finish the drink (syrup, lid, sleeve) · 5) Call the name and hand off

**Suppliers:** Coffee roaster · Dairy distributor · Cup/lid supplier
**Inputs:** Espresso beans · Milk · Cups, lids, sleeves · Customer order
**Outputs:** Finished espresso drink · Receipt
**Customers:** Students and staff buying espresso drinks in the morning rush

---

## 6. T-05 VoC → CTQ — turning a complaint into a number

- **Customer statement:** "I skip the line when it's out the door — I can't be late to a 9am."
- **Need:** A predictable, short wait during the morning rush.
- **CTQ:** Order-to-handoff time under 5 minutes during the 7:00–10:00 peak.

**Watch for:** the CTQ is the same metric as the charter goal. That thread —
complaint → need → measurable characteristic → charter metric → baseline — is
the thing the whole app is built to keep honest.

---

## 7. T-11 Data import → the fun part

Import the **`wait-times.csv`** you downloaded. Pick the `wait_minutes` column.

You'll see a quality scan: missing values, non-numeric entries, duplicates —
all zero here.

---

## 8. T-13 Baseline — the money screen

Run it against the imported data with **upper spec limit `5.0`** (the customer
promise), no lower limit.

**What you should see, and why it's the best demo in the app:**
- Mean **8.41 minutes**, 120 points
- **Stable** — no out-of-control signals
- **Cpk about −1.14** — deeply negative

That combination is the teaching moment: the process is perfectly
*predictable* and predictably *terrible*. "In control" and "meeting the
customer's need" are two different questions, and most people conflate them.
The app refuses to let you claim capability without stability, and here it
gives you stability with awful capability.

---

## 9. T-14 Charts — histogram, run chart, Pareto

Same dataset. The run chart shows time order; the histogram shows the spread
against your 5.0 line. Real Plotly charts, zoomable.

---

## 10. Diagnostics (top right) — proof the math is real

Runs a reference dataset with certified published values through the engine
and compares. If it says the computed and certified values match, the
statistics engine on your machine is provably correct — not "trust me."

---

## What to look at while you're in there

- **The helper panel on every tool** — what it is, when to use it, when *not*
  to, what good looks like, common mistakes. That's the teaching layer, and
  it's the same rubric the app grades against.
- **The checks strip under each form** — plain-English pass/flag on the
  rule-checkable parts.
- **The phase rail** on the left — gates between phases. Try jumping ahead and
  see it soft-block with a reason (you can override, but it makes you say why).

## Going further

The Improve and Control tools (pilot design, before/after proof, control
charts, control plan, A3) need "after" data, so they're best explored with the
full worked example in `demo/coffee-bar/` rather than typed fresh.
