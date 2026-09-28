-- 03_when_where.sql
-- When and where do the long waits happen?

CREATE OR REPLACE TABLE out_by_hour AS
SELECT hr,
       count(*)                                    AS trips,
       sum(long_wait)                              AS long_waits,
       round(100.0 * sum(long_wait) / count(*), 1) AS long_wait_pct
FROM trips
GROUP BY 1
ORDER BY 1;

-- Borough is where a reader expects the answer to be, and it is not: the long waits are
-- spread across the four big boroughs roughly in line with how many rides each has.
CREATE OR REPLACE TABLE out_by_borough AS
SELECT borough,
       count(*)                                                       AS trips,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1)             AS share_of_trips_pct,
       round(100.0 * sum(long_wait) / sum(sum(long_wait)) OVER (), 1) AS share_of_long_waits_pct,
       round(100.0 * sum(long_wait) / count(*), 1)                    AS long_wait_pct
FROM trips
GROUP BY 1
ORDER BY share_of_long_waits_pct DESC;

-- The two segments the recommendation names. Late night is requests from 22:00 to 04:59;
-- weekday-evening airports are JFK (132) and LaGuardia (138), weekday requests from
-- 18:00 to 00:59.
CREATE OR REPLACE TABLE out_segments AS
WITH totals AS (SELECT count(*) AS n, sum(long_wait) AS lw FROM trips),
seg AS (
    SELECT 'late_night' AS segment, count(*) AS n, sum(long_wait) AS lw
    FROM trips WHERE hr >= 22 OR hr <= 4
    UNION ALL
    SELECT 'weekday_evening_airports', count(*), sum(long_wait)
    FROM trips
    WHERE PULocationID IN (132, 138) AND daytype = 'weekday' AND (hr >= 18 OR hr = 0)
)
SELECT s.segment,
       s.n                                 AS trips,
       s.lw                                AS long_waits,
       round(100.0 * s.n / t.n, 2)         AS share_of_trips_pct,
       round(100.0 * s.lw / t.lw, 1)       AS share_of_long_waits_pct,
       round(100.0 * s.lw / s.n, 1)        AS long_wait_pct
FROM seg s, totals t;
