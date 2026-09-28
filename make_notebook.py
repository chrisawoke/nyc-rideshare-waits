"""
Builds analysis.ipynb from the cells below and runs it, so the copy on GitHub shows its
output. The notebook reads outputs/ and charts/, which are committed, so it runs on a fresh
clone without the 400MB download. Edit here, not in the .ipynb.
"""
import nbformat
from nbclient import NotebookClient

md = nbformat.v4.new_markdown_cell
code = nbformat.v4.new_code_cell

cells = [
    md("""# Where New York's ride-hail riders wait too long

**The scenario.** A ride-hail marketplace team in New York has a fixed monthly budget for
driver incentives and one question: where, and when, should it be spent to cut long waits?
The team is hypothetical. The data is not: every Uber and Lyft trip in New York City in
June 2026, 20.8 million of them, from the Taxi and Limousine Commission.

**The answer.** Concentrate it. A tenth of the city's zone-hours produce 44% of all long
waits, mostly late at night and at the airports on weekday evenings. And spend it on getting
drivers *there*, not on the ride: 92% of a long wait is the driver still on the way.

This notebook follows the argument. The SQL that produces each table is in `sql/`, and
`validate.py` checks every figure quoted here."""),
    code("""import pandas as pd
from IPython.display import Image, display

pd.set_option("display.float_format", "{:,.2f}".format)
read = lambda name: pd.read_csv(f"outputs/{name}.csv")"""),

    md("""## 1. What was kept

Scheduled rides show up as pickups *before* the request, at almost the same rate for both
companies, and are removed because their wait is not a wait. See `CLEANING_LOG.md`."""),
    code("""read("cleaning_audit").T.rename(columns={0: "rows"})"""),
    code("""read("negative_by_operator")"""),

    md("""## 2. How long do people wait?

Most rides are quick. The median wait is under five minutes. But one ride in eight waits
more than ten, which across a month is 2.5 million rides."""),
    code("""read("headline")"""),
    code("""read("by_operator")"""),
    md("""Uber rides wait long far more often than Lyft rides. That could be service, or it could
be that the two companies record the request time differently. The data cannot tell those
apart, so everything below treats the market as one."""),

    md("""## 3. When and where?

**Not a borough problem.** No borough owns it: each of the four big ones holds between 16%
and 28% of long waits, and Manhattan, with a third of all rides, holds less than its share.
A borough-level scheme would spend money everywhere."""),
    code("""read("by_borough")"""),
    md("""**A time problem.** The long-wait rate is 21% at 4am and 6% at 10am."""),
    code("""display(Image("charts/by_hour.png", width=800))"""),
    md("""Two segments stand out. Late night (22:00 to 04:59) is a fifth of rides and nearly a
third of long waits. Weekday-evening airport pickups are about 1% of rides, but almost four
in ten of them wait over ten minutes."""),
    code("""read("segments")"""),

    md("""## 4. Why is a long wait long?

A wait has two parts: the driver on the way, and the two of them finding each other at the
curb. The fixes are different, so which dominates decides the recommendation.

The expectation going in was that airports would be a curb problem: terminals, pickup
zones, riders who cannot find the car. They are not. At the airports as everywhere else,
around nine-tenths of a long wait is the driver still on the way. **This is a supply
problem.**"""),
    code("""display(Image("charts/wait_split.png", width=800))
read("wait_split")"""),
    md("""Is it that drivers are paid too little to go there? Not obviously. Pay per hour of trip
time is slightly *higher* in the worst zone-hours, and across zone-hours the long-wait rate
correlates weakly and positively with pay. Pay alone is not the lever: the scheme should
pay for **being available** in the right place at the right hour, not more per ride."""),
    code("""display(read("pay"), read("pay_correlation"))"""),

    md("""## 5. Can a fixed budget reach it?

Rank every zone-hour by how many long waits it produces. The top tenth, 1,235 of 12,356,
hold 44% of all long waits while carrying 30% of rides."""),
    code("""display(Image("charts/concentration.png", width=800))
display(read("top_tenth"), read("top_tenth_by_borough"))"""),

    md("""## 6. Does it depend on the ten-minute line?

No. At 8 or 12 minutes the top tenth holds 41 to 46% of long waits, and 93% of the
zone-hours it picks are the same."""),
    code("""read("sensitivity")"""),

    md("""## Recommendation

1. **Concentrate the budget** on the top tenth of zone-hours, starting with late nights and
   weekday-evening airport arrivals.
2. **Pay for availability, not rides.** A guaranteed hourly minimum for drivers online in a
   target zone-hour addresses the part of the wait that is the problem.
3. **Prove it before scaling it.** A four-week test: the scheme switched on in half the
   target zone-hours, chosen at random, the other half left as they are.

**Measured by:** the share of rides waiting over ten minutes in the target zone-hours, the
median time for a driver to arrive, and the cost of each long wait avoided.

## Limits

- One month. Seasonality, holidays and weather are not covered.
- Completed trips only. Riders who gave up are missing, so the worst waits are undercounted.
- Uber and Lyft combined: this is the market, not one operator's own view.
- There is no incentive in the data to measure the effect of one. That is what the test is for.
- Pay per trip-hour leaves out the time drivers spend reaching a pickup or waiting for one.
- Taxi zones are coarse. A real scheme would target finer areas."""),
]

nb = nbformat.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}})
NotebookClient(nb, timeout=120, kernel_name="python3").execute()
nbformat.write(nb, "analysis.ipynb")
print("wrote analysis.ipynb")
