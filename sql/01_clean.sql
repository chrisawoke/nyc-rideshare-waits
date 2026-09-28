-- 01_clean.sql
-- From the raw month of trips to the table every later query reads.
-- Each exclusion is counted in `out_cleaning_audit`, so CLEANING_LOG.md quotes numbers
-- the pipeline produced rather than numbers someone typed.

CREATE OR REPLACE TABLE zones AS
SELECT * FROM read_csv_auto('data/taxi_zone_lookup.csv');

CREATE OR REPLACE TABLE raw AS
SELECT *,
       date_diff('second', request_datetime, pickup_datetime) AS wait_s
FROM read_parquet('data/trips_2026-06.parquet');

-- The audit runs the rules in the same order as the filter below, so each row counts
-- only what that rule removed and nothing an earlier rule had already taken.
CREATE OR REPLACE TABLE out_cleaning_audit AS
WITH steps AS (
    SELECT
        count(*)                                                                    AS raw_trips,
        count(*) FILTER (WHERE PULocationID IN (264, 265))                          AS unknown_zone,
        count(*) FILTER (WHERE PULocationID NOT IN (264, 265) AND wait_s IS NULL)   AS missing_time,
        count(*) FILTER (WHERE PULocationID NOT IN (264, 265) AND wait_s < 0)       AS negative_wait,
        count(*) FILTER (WHERE PULocationID NOT IN (264, 265) AND wait_s > 3600)    AS wait_over_60,
        count(*) FILTER (WHERE PULocationID NOT IN (264, 265)
                           AND wait_s BETWEEN 0 AND 3600)                           AS kept
    FROM raw
)
SELECT * FROM steps;

-- Negative waits split by operator: if one company produced most of them it would be a
-- data fault; roughly equal shares point to a product feature (scheduled rides) instead.
CREATE OR REPLACE TABLE out_negative_by_operator AS
SELECT CASE hvfhs_license_num WHEN 'HV0003' THEN 'Uber' WHEN 'HV0005' THEN 'Lyft' ELSE 'Other' END AS operator,
       count(*)                                   AS trips,
       count(*) FILTER (WHERE wait_s < 0)         AS negative_wait,
       round(100.0 * count(*) FILTER (WHERE wait_s < 0) / count(*), 2) AS negative_pct,
       round(median(-wait_s / 60.0) FILTER (WHERE wait_s < 0), 1)      AS median_minutes_early
FROM raw
WHERE PULocationID NOT IN (264, 265)
GROUP BY 1
ORDER BY trips DESC;

CREATE OR REPLACE TABLE trips AS
SELECT
    CASE r.hvfhs_license_num WHEN 'HV0003' THEN 'Uber' WHEN 'HV0005' THEN 'Lyft' ELSE 'Other' END AS operator,
    r.request_datetime,
    r.on_scene_datetime,
    r.pickup_datetime,
    r.PULocationID,
    z.Borough                                                          AS borough,
    z."Zone"                                                           AS zone_name,
    r.trip_time,
    r.driver_pay,
    r.wait_s / 60.0                                                    AS wait_min,
    date_diff('second', r.request_datetime, r.on_scene_datetime) / 60.0 AS to_arrive_min,
    date_diff('second', r.on_scene_datetime, r.pickup_datetime) / 60.0  AS at_curb_min,
    hour(r.request_datetime)                                           AS hr,
    -- DuckDB numbers Sunday 0 and Saturday 6.
    CASE WHEN dayofweek(r.request_datetime) IN (0, 6) THEN 'weekend' ELSE 'weekday' END AS daytype,
    (r.wait_s > 600)::INTEGER                                          AS long_wait
FROM raw r
JOIN zones z ON z.LocationID = r.PULocationID
WHERE r.PULocationID NOT IN (264, 265)
  AND r.wait_s BETWEEN 0 AND 3600;

DROP TABLE raw;
