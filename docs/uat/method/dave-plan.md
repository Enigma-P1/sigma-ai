I’m Dave Mercer, the evening operations supervisor at a regional food-service warehouse. We pick and load cases of frozen and dry food for restaurants, schools, and nursing homes. The building is about 90,000 square feet. I have 18 warehouse employees reporting to me on the evening shift, including pickers, forklift drivers, and loaders. There are about 70 people across all shifts. I’ve been in warehouse work for 16 years and supervising this operation for the last seven.

The problem I actually want to work on is wrong items being picked onto restaurant orders. Not missing a whole pallet — the annoying stuff where a customer ordered a case of 4-ounce ketchup packets and got 6-ounce packets, or ordered chicken tenders and got chicken patties. The driver doesn’t catch all of it, so the customer calls after delivery.

Our target is less than 0.5% of order lines with an error. We’ve been running between 1.1% and 1.4% for the last few months. In June we shipped about 38,600 order lines and had 487 reported picking errors. That led to 31 redeliveries, credits and replacements totaling around $6,800, and roughly 54 hours of extra work for customer service, drivers, and the warehouse. The money is irritating, but the bigger headache is pulling a driver off his route to take one case of product back across town.

I know it’s a problem because customer service emails me the complaints, and our quality report has a line called “warehouse shorts and mispicks.” Nobody trusts that report completely. It counts what customers report, not every error that happened. Some customers probably don’t notice, and some complaints get entered as shorts even when the item was actually wrong. Still, the number is going up, and I hear about it every Monday morning.

The data I have is a spreadsheet maintained by our inventory clerk. It is not clean. Dates are entered three different ways. Employee names are sometimes initials, sometimes full names. “Wrong item,” “mispick,” and “substitution” are all used for similar things. We have 487 rows for June, but 22 rows are missing a picker name and 11 have no aisle. The spreadsheet columns are:

`Complaint date, Delivery date, Order number, Customer, Picker, Aisle, Item ordered, Item shipped, Error type, Quantity, Credit amount, Notes`

Here are ten example rows from June, with names changed but the kind of entries we really have:

```text
06/03/2026, 06/03/2026, 104882, Green Valley Hospital, JM, 12, Ketchup packets 4 oz, Ketchup packets 6 oz, wrong item, 2, 86.40, customer called
2026-06-04, 6/4/26, 104931, Mill Street Diner, J. Morales, 7, Frozen chicken tenders 10 lb, Frozen chicken patties 10 lb, mispick, 1, 42.15, similar boxes
6/05/26, 06/05/2026, 105004, Northside School, AB, 19, 12-inch flour tortillas, 10-inch flour tortillas, wrong item, 3, 57.00, driver caught it at stop
06/07/2026, 06/07/2026, 105117, County Care Center, TK, 3, Low sodium soup, Regular soup, substitution, 4, 31.80, label looks almost same
06/08/26, 2026-06-08, 105208, Harbor Cafe, JM, , Mozzarella sticks, Onion rings, wrong item, 1, 24.75, picker unknown on paper ticket
06/10/2026, 06/10/2026, 105366, West End Grill, AB, 14, 5 oz burger patties, 4 oz burger patties, wrong item, 2, 63.20, picked from slot above
06/13/2026, 06/13/2026, 105622, Green Valley Hospital, J Morales, 12, Ketchup packets 4 oz, Ketchup packets 6 oz, mispick, 6, 259.20, repeat issue
06/18/2026, 06/18/2026, 105981, Oak Street Elementary, RL, 22, Apple juice 6 x 64 oz, Orange juice 6 x 64 oz, wrong item, 2, 48.60, same color case
06/22/26, 06/22/26, 106244, Mill Street Diner, TK, 7, Frozen chicken tenders 10 lb, Frozen chicken patties 10 lb, wrong item, 1, 42.15, new hire
06/29/2026, 06/29/2026, 106812, Harbor Cafe, JM, 3, Low sodium soup, Regular soup, substitution, 2, 15.90, customer says not approved
```

I also have total lines picked by person from the labor report, but it is a separate spreadsheet. For June it shows:

```text
J. Morales, 8420 lines
A. Brown, 7910 lines
T. King, 6540 lines
R. Lewis, 6025 lines
S. Patel, 4810 lines
Other staff combined, 4895 lines
```

That second file is probably not useful without a lot of cleanup. It also doesn’t tell me who picked an order when two people worked the same batch.

What I want from the software is pretty simple. I want to get past “people need to pay more attention.” I want it to help me see whether these errors are mostly in certain aisles, certain item pairs, certain shifts, or certain people. I also want to know whether the repeat items are a real pattern or just the few complaints I happen to remember.

If I can put in the June numbers and get a plain chart or table that says, for example, “Aisles 3, 7, and 12 account for 61% of reported wrong items,” that would be useful. If it can help me write down possible causes and compare them against the actual complaints, even better. I don’t need a black-box answer telling me that the root cause is “human error.” I already know people make mistakes. I need something that points me toward a change I can try, such as moving similar cases apart, adding a scan check, or changing the pick labels.

I would keep using it if I can understand what I’m looking at, enter data without taking a class, and get something I could show my warehouse manager in ten minutes. I would close it and never open it again if it requires perfectly formatted data before doing anything, uses words like “variance” without explaining them, or gives me a fancy graph that doesn’t tell me what to do next. If I have to manually enter 487 complaints one by one, that’s also a deal breaker. I have an operation to run.

For the next hour, I would try this, in this order:

1. Open the application for the first time and wait to see what the starting screen says. I expect either a welcome screen, a “new project” option, or some example project. I want screenshots of the whole first screen, including any words I don’t understand.

2. Look for a button or menu item that sounds like `New Project`, `Create Project`, or `Start`. If I see one, I will select it. I expect it to ask for a project name or problem description. If there is no obvious starting button, I want to know what the app expects me to click first.

3. If it asks for a project name, I will type exactly:  
   `June 2026 warehouse picking errors`

   I expect this to create a blank project or take me to the next setup screen. I do not want an example project unless the app forces me to choose one.

4. If it asks for a problem statement, I will type:  
   `Restaurant and school orders are receiving wrong items after picking. We had 487 reported errors on 38,600 order lines in June 2026, costing about $6,800 in credits and redeliveries.`

   I expect the app to save that text without making me translate it into technical language.

5. If it asks for a goal, target, or desired result, I will type:  
   `Reduce reported wrong-item errors from 1.26% of order lines to below 0.5% by September 30, 2026.`

   The 1.26% comes from 487 divided by 38,600. I expect the app either to accept the sentence or show separate fields for the current number, target number, and date.

6. I will look for anywhere to add data, such as `Import`, `Data`, `Measurements`, `Table`, or `Upload CSV`. I expect to find some way to bring in a spreadsheet rather than type every complaint. If it only accepts CSV, I will use a small test file containing the ten example rows above and name it `june_picking_errors_test.csv`.

7. If the app lets me paste data into a table, I will paste the ten rows with the column names exactly as shown:  
   `Complaint date, Delivery date, Order number, Customer, Picker, Aisle, Item ordered, Item shipped, Error type, Quantity, Credit amount, Notes`

   I expect it to identify the first row as column headings and show the ten complaints as records. If it complains about the mixed date formats, I want to see the exact error and whether it offers to fix or ignore them.

8. If it requires a clean date format, I will try changing only the dates in the test data to `2026-06-03` through `2026-06-29`, leaving the other messy fields alone. I expect the app to accept the dates and either accept blank aisle and different picker names or tell me which fields are mandatory.

9. I will look for a way to mark fields as categories or numbers. I want `Aisle`, `Picker`, and `Error type` treated as groups, and `Quantity` and `Credit amount` treated as numbers. I expect the app to either detect that automatically or offer a simple choice. If it asks me to define the fields, I will use those exact settings.

10. I will look for a preview, summary, or basic table of the imported data. I expect to see 10 records, 10 order numbers, 1 blank aisle, and the credit amounts totaling $671.15. If the app shows a different total, I want to know whether it counted quantities or dollar amounts incorrectly.

11. I will look for a chart or analysis option and choose the simplest thing available that groups records by `Aisle`. If it asks what measure to count, I will choose the number of records or complaints, not quantity and not credit amount. I expect aisle 12 and aisle 7 to show up near the top in this small sample.

12. I will repeat that analysis using `Picker` as the grouping field. Before doing it, I will see whether the app treats `JM` and `J. Morales` and `J Morales` as three separate people. I expect it probably will, because the data is messy. If there is a way to combine or rename them, I will combine all three as `J. Morales` and note whether that changes the chart.

13. I will group the data by `Error type`. I expect to see `wrong item`, `mispick`, and `substitution` separately at first. I will not combine them unless the app makes that easy. I want to see whether the software warns me that these are inconsistent labels or simply treats them as different categories.

14. I will look for a way to identify repeated item pairs. If there is an option to group by `Item ordered` and `Item shipped`, I will use it. I expect the pair `Ketchup packets 4 oz` to `Ketchup packets 6 oz` to show twice, and `Frozen chicken tenders 10 lb` to `Frozen chicken patties 10 lb` to show twice.

15. I will look for a `Why`, `Causes`, `Root cause`, `Fishbone`, `Cause and effect`, or similar section. If I find one, I will enter these possible causes exactly:
   - `Similar-looking cases stored beside each other`
   - `Old paper pick tickets are hard to read`
   - `No scan confirmation before loading`
   - `New employees are not familiar with look-alike items`
   - `Product slots are not clearly labeled`
   - `Picker is rushed near the end of the shift`

   I expect it to let me save these as a list or arrange them somehow. I am not expecting it to prove which one is true from ten rows.

16. If the app asks me to rate or prioritize those possible causes, I will use a simple high/medium/low choice if available. I will mark `No scan confirmation before loading`, `Similar-looking cases stored beside each other`, and `Product slots are not clearly labeled` as high. I will mark the other three as medium. I expect either a ranked list or some visual showing the choices.

17. I will look for a report, dashboard, or summary page that combines the problem statement, goal, imported data, and the charts. I expect it to show the number of records and at least one useful pattern. If it only shows percentages with no raw counts, I want to know whether I can display both.

18. I will try to export or save the result as a PDF, image, or spreadsheet. I will name it `June picking error review`. I expect the exported version to be something I could print or email to my warehouse manager without the manager needing the application.

19. At the end, I will go back to the data table and see whether I can add one more row manually:
   `2026-06-30, 2026-06-30, 106901, Green Valley Hospital, J. Morales, 12, Ketchup packets 4 oz, Ketchup packets 6 oz, wrong item, 1, 43.20, customer called again`

   I expect the charts or totals to update after I save the row. If they do not update automatically, I want to see what refresh action is required.

20. Before closing, I will look for a save, backup, or reopen option. I expect to close the project, reopen `June 2026 warehouse picking errors`, and still see the imported rows and whatever charts I made. If I cannot reopen the project without losing the work, I’m done with the app.

