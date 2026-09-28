-- 02_how_long.sql
-- How long do riders wait, and how many wait too long?
-- "Too long" is more than 10 minutes from request to pickup. 06_sensitivity.sql tests
-- whether the conclusions change at 8 or 12.

CREATE OR REPLACE TABLE out_headline AS
SELECT
    count(*)                                         AS trips,
    sum(long_wait)                                   AS long_waits,
    round(100.0 * sum(long_wait) / count(*), 1)      AS long_wait_pct,
    round(median(wait_min), 1)                       AS median_wait_min,
    round(quantile_cont(wait_min, 0.9), 2)           AS p90_wait_min
FROM trips;

CREATE OR REPLACE TABLE out_by_operator AS
SELECT operator,
       count(*)                                           AS trips,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS share_of_trips_pct,
       round(100.0 * sum(long_wait) / count(*), 1)        AS long_wait_pct
FROM trips
GROUP BY 1
ORDER BY trips DESC;
