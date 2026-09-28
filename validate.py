"""
Checks, in three layers, that the numbers in the write-up are the numbers the data gives.

1. Integrity: the pipeline's own tables agree with each other (exclusions add up to the raw
   count, hourly totals add up to the month, the two parts of a wait add up to the wait).
2. Independent recount: the headline is recomputed straight from the raw parquet by a
   different query, so a mistake in 01_clean.sql cannot confirm itself.
3. Every figure quoted on the project page, listed below with where it comes from, is
   compared against outputs/. Change a query and a quoted number goes stale: this fails.

    python validate.py        # after run_analysis.py
"""
from pathlib import Path

import duckdb
import pandas as pd

OUT = Path("outputs")
failures = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{f'  ({detail})' if detail else ''}")
    if not ok:
        failures.append(name)


def csv(name):
    return pd.read_csv(OUT / f"{name}.csv")


def row(name, key=None, value=None):
    df = csv(name)
    return (df if key is None else df[df[key] == value]).iloc[0]


print("1. Integrity")
audit = row("cleaning_audit")
removed = audit.unknown_zone + audit.missing_time + audit.negative_wait + audit.wait_over_60
check("exclusions plus kept rows equal the raw count", removed + audit.kept == audit.raw_trips,
      f"{removed:,} + {audit.kept:,} = {audit.raw_trips:,}")
head = row("headline")
check("headline counts every kept row", head.trips == audit.kept)
hours = csv("by_hour")
check("hourly rows add up to the month", hours.trips.sum() == head.trips and hours.long_waits.sum() == head.long_waits)
check("24 hours present", len(hours) == 24)
check("borough shares add up to 100%", abs(csv("by_borough").share_of_trips_pct.sum() - 100) < 0.3)
ops = csv("by_operator")
check("operator rows add up to the month", ops.trips.sum() == head.trips)
curve = csv("concentration_curve")
check("concentration curve rises monotonically to 100%",
      curve.pct_of_long_waits.is_monotonic_increasing and abs(curve.pct_of_long_waits.iloc[-1] - 100) < 1e-6)
top = row("top_tenth")
check("top tenth is exactly 10% of zone-hours, rounded down", top.cells == top.all_cells // 10)
split = row("wait_split", "group_name", "All rides")
check("every kept ride is either split or counted as unsplittable",
      split.trips + row("unsplittable").trips_not_split == head.trips)

con = duckdb.connect("data/rideshare.duckdb", read_only=True)
gap = con.sql("""SELECT max(abs(to_arrive_min + at_curb_min - wait_min)) FROM trips
                 WHERE on_scene_datetime IS NOT NULL""").fetchone()[0]
check("driver arrival plus curb time equals the wait, ride by ride", gap < 1e-9, f"largest gap {gap:.2e} min")

print("2. Independent recount from the raw file")
raw = duckdb.sql("""
    SELECT count(*), count(*) FILTER (WHERE epoch(pickup_datetime) - epoch(request_datetime) > 600)
    FROM 'data/trips_2026-06.parquet'
    WHERE PULocationID < 264
      AND epoch(pickup_datetime) - epoch(request_datetime) BETWEEN 0 AND 3600
""").fetchone()
check("kept rides match", raw[0] == head.trips, f"{raw[0]:,}")
check("long waits match", raw[1] == head.long_waits, f"{raw[1]:,}")

print("3. Every figure the page quotes")
seg = lambda s: row("segments", "segment", s)
bor = lambda b: row("by_borough", "borough", b)
hr = lambda h: row("by_hour", "hr", h)
op = lambda o: row("by_operator", "operator", o)
sens = lambda m: row("sensitivity", "minutes", m)
pay = csv("pay").set_index("top_tenth")["pay_per_trip_hour"]
long_split = row("wait_split", "group_name", "Long waits, all")
airport_split = row("wait_split", "group_name", "Long waits, airports")

PAGE = {
    # quoted on the page            : (value on the page, value in outputs/)
    "rides analysed":                 (20_512_792, head.trips),
    "long waits":                     (2_470_360, head.long_waits),
    "share waiting over 10 min":      (12.0, head.long_wait_pct),
    "median wait, min":               (4.8, head.median_wait_min),
    "90th percentile wait, min":      (10.75, head.p90_wait_min),
    "long wait: driver arriving, min": (12.9, long_split.to_arrive_min),
    "long wait: at the curb, min":    (1.2, long_split.at_curb_min),
    "long wait: share driver arriving": (91.7, long_split.to_arrive_share_pct),
    "airport long wait: share driver arriving": (90.0, airport_split.to_arrive_share_pct),
    "top tenth: share of long waits": (43.7, top.share_of_long_waits_pct),
    "top tenth: share of rides":      (30.0, top.share_of_trips_pct),
    "top tenth: long-wait rate":      (17.6, top.long_wait_pct),
    "top tenth: zone-hours":          (1_235, top.cells),
    "all zone-hours":                 (12_356, top.all_cells),
    "top tenth: late-night cells":    (358, top.late_night_cells),
    "top tenth: airport cells":       (66, top.airport_cells),
    "late night: share of rides":     (21.31, seg("late_night").share_of_trips_pct),
    "late night: share of long waits": (29.9, seg("late_night").share_of_long_waits_pct),
    "late night: long-wait rate":     (16.9, seg("late_night").long_wait_pct),
    "airports: share of rides":       (1.21, seg("weekday_evening_airports").share_of_trips_pct),
    "airports: share of long waits":  (3.9, seg("weekday_evening_airports").share_of_long_waits_pct),
    "airports: long-wait rate":       (38.8, seg("weekday_evening_airports").long_wait_pct),
    "4am long-wait rate":             (21.1, hr(4).long_wait_pct),
    "10am long-wait rate":            (6.1, hr(10).long_wait_pct),
    "Brooklyn share of long waits":   (28.2, bor("Brooklyn").share_of_long_waits_pct),
    "Manhattan share of long waits":  (27.9, bor("Manhattan").share_of_long_waits_pct),
    "Queens share of long waits":     (25.9, bor("Queens").share_of_long_waits_pct),
    "Bronx share of long waits":      (15.7, bor("Bronx").share_of_long_waits_pct),
    "pay per trip-hour, top tenth":   (65.4, pay.loc[True]),
    "pay per trip-hour, the rest":    (63.7, pay.loc[False]),
    "pay vs long-wait correlation":   (0.28, row("pay_correlation").corr_long_wait_rate_vs_pay),
    "8 min: top tenth share":         (41.4, sens(8).top_tenth_share_pct),
    "12 min: top tenth share":        (45.9, sens(12).top_tenth_share_pct),
    "8 min: same zone-hours":         (93, sens(8).same_cells_as_10min_pct),
    "12 min: same zone-hours":        (93, sens(12).same_cells_as_10min_pct),
    "negative waits excluded":        (260_881, audit.negative_wait),
    "Uber share of rides":            (73.5, op("Uber").share_of_trips_pct),
    "Uber long-wait rate":            (13.6, op("Uber").long_wait_pct),
    "Lyft long-wait rate":            (7.7, op("Lyft").long_wait_pct),
}
for name, (quoted, actual) in PAGE.items():
    check(name, abs(float(quoted) - float(actual)) < 1e-9, f"page {quoted}, data {actual}")

print(f"\n{len(failures)} failed" if failures else "\nall checks pass")
raise SystemExit(1 if failures else 0)
