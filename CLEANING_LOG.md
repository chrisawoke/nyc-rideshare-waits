# Cleaning log

Every number here is produced by `sql/01_clean.sql` into `outputs/cleaning_audit.csv` and
checked by `validate.py`. Rules run in this order; each count is what that rule removed and
nothing an earlier rule had already taken.

| Step | Rows | Share of raw |
| --- | ---: | ---: |
| Raw June 2026 trips | 20,775,868 | 100% |
| Pickup zone unknown or outside NYC (264, 265) | 1,241 | 0.01% |
| Request or pickup time missing | 0 | 0% |
| Picked up **before** the request was made | 260,881 | 1.26% |
| Wait over 60 minutes | 954 | 0.005% |
| **Kept** | **20,512,792** | **98.7%** |

## Decisions, and why

**Negative waits are scheduled rides, not errors.** 1.3% of trips show a pickup before the
request. If one company produced most of them it would be a logging fault; instead the rate
is almost identical for both (Uber 1.21%, Lyft 1.37%), and the typical ride is picked up
about six minutes "early" (median 6.1 minutes Uber, 6.4 Lyft). That is the pattern of a ride
booked in advance, where the request time recorded is not when the rider started waiting.
They are removed from the analysis because their wait is not a wait. Source:
`outputs/negative_by_operator.csv`.

**Waits over an hour are removed.** 954 rows. At that length it is far likelier to be a
record left open than a rider standing on a kerb, and at 0.005% of rows it cannot move any
result either way.

**Unknown zones are removed** because every question here is about where. 1,241 rows.

**Rides whose wait cannot be split stay in.** 124,297 kept rides record the driver arriving
before the request or after the pickup. Their total wait is valid, so they count in every
figure except the one that splits a wait into its two parts (`sql/04_why.sql`).

**The 10-minute threshold is a choice.** It is tested at 8 and 12 minutes in
`sql/06_sensitivity.sql`. At both, the top tenth of zone-hours holds 41 to 46% of long waits,
and 93% of the zone-hours chosen are the same ones.

## What cleaning cannot fix

- **Only completed trips are recorded.** A rider who gave up waiting is not in the data, so
  the worst waits are undercounted, and more so where they are worst.
- **Uber and Lyft differ sharply** (13.6% of Uber rides wait over 10 minutes, 7.7% of Lyft).
  Whether that is service or how each company records the request time cannot be told from
  this data, so the analysis treats the market as one.
