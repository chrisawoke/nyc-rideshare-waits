-- 05_concentration.sql
-- Could a fixed budget reach most of the problem? A "zone-hour" is one pickup zone at one
-- hour of the day on either weekdays or weekends: the smallest unit an incentive scheme
-- can realistically be switched on for. Ranked by how many long waits each one produces,
-- because a budget is spent on volume of the problem, not on its rate.

CREATE OR REPLACE TABLE zone_hours AS
SELECT PULocationID, borough, zone_name, daytype, hr,
       count(*)                  AS trips,
       sum(long_wait)            AS long_waits,
       sum(driver_pay)           AS driver_pay,
       sum(trip_time) / 3600.0   AS trip_hours
FROM trips
GROUP BY ALL;

CREATE OR REPLACE TABLE zone_hours_ranked AS
SELECT *,
       row_number() OVER (ORDER BY long_waits DESC, trips) AS rank,
       count(*) OVER ()                                    AS n_cells
FROM zone_hours;

-- The whole curve, for the chart: after the top k cells, what share of long waits is covered.
CREATE OR REPLACE TABLE out_concentration_curve AS
SELECT rank,
       round(100.0 * rank / n_cells, 3)                                                   AS pct_of_zone_hours,
       round(100.0 * sum(long_waits) OVER (ORDER BY rank) / sum(long_waits) OVER (), 3)   AS pct_of_long_waits,
       round(100.0 * sum(trips) OVER (ORDER BY rank) / sum(trips) OVER (), 3)             AS pct_of_trips
FROM zone_hours_ranked
ORDER BY rank;

-- The top tenth, described: what a targeted scheme would actually be switched on for.
CREATE OR REPLACE TABLE out_top_tenth AS
WITH t AS (SELECT sum(long_waits) lw, sum(trips) n FROM zone_hours),
top AS (SELECT * FROM zone_hours_ranked WHERE rank <= floor(n_cells * 0.10))
SELECT count(*)                                                AS cells,
       max(n_cells)                                            AS all_cells,
       round(100.0 * sum(long_waits) / max(t.lw), 1)           AS share_of_long_waits_pct,
       round(100.0 * sum(top.trips) / max(t.n), 1)             AS share_of_trips_pct,
       round(100.0 * sum(long_waits) / sum(top.trips), 1)      AS long_wait_pct,
       count(*) FILTER (WHERE PULocationID IN (132, 138))      AS airport_cells,
       count(*) FILTER (WHERE hr >= 22 OR hr <= 4)             AS late_night_cells,
       count(*) FILTER (WHERE daytype = 'weekday')             AS weekday_cells
FROM top, t;

CREATE OR REPLACE TABLE out_top_tenth_by_borough AS
SELECT borough, count(*) AS cells, sum(long_waits) AS long_waits
FROM zone_hours_ranked
WHERE rank <= floor(n_cells * 0.10)
GROUP BY 1
ORDER BY cells DESC;

-- Is it that drivers are paid too little to be there? Pay per hour of trip time, top tenth
-- against the rest, and the correlation between a cell's long-wait rate and its pay.
-- Trip time only: time spent driving to a pickup or waiting for one is not in the data.
CREATE OR REPLACE TABLE out_pay AS
SELECT (rank <= floor(n_cells * 0.10))                     AS top_tenth,
       round(sum(driver_pay) / sum(trip_hours), 1)         AS pay_per_trip_hour
FROM zone_hours_ranked
GROUP BY 1
ORDER BY 1 DESC;

CREATE OR REPLACE TABLE out_pay_correlation AS
SELECT round(corr(long_waits * 1.0 / trips, driver_pay / trip_hours), 2) AS corr_long_wait_rate_vs_pay
FROM zone_hours
WHERE trips >= 100 AND trip_hours > 0;
