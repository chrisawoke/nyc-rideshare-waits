-- 04_why.sql
-- Why is a long wait long? Every wait splits into two parts:
--   to_arrive: request to the driver arriving (a supply problem: no driver close by)
--   at_curb:   driver arriving to the rider getting in (a pickup problem: finding each other)
-- They call for different fixes, so which one dominates decides the recommendation.

-- Rows where the driver is logged as arriving before the request, or after the pickup,
-- cannot be split honestly. They stay in every other figure and are left out of this one.
CREATE OR REPLACE VIEW splittable AS
SELECT * FROM trips
WHERE on_scene_datetime IS NOT NULL AND to_arrive_min >= 0 AND at_curb_min >= 0;

CREATE OR REPLACE TABLE out_unsplittable AS
SELECT (SELECT count(*) FROM trips) - (SELECT count(*) FROM splittable) AS trips_not_split;

CREATE OR REPLACE TABLE out_wait_split AS
SELECT group_name,
       count(*)                                                     AS trips,
       round(avg(to_arrive_min), 1)                                 AS to_arrive_min,
       round(avg(at_curb_min), 1)                                   AS at_curb_min,
       round(100.0 * avg(to_arrive_min) / avg(to_arrive_min + at_curb_min), 1) AS to_arrive_share_pct
FROM (
    SELECT *, 'All rides' AS group_name FROM splittable
    UNION ALL
    SELECT *, 'Long waits, city' FROM splittable WHERE long_wait = 1 AND PULocationID NOT IN (132, 138)
    UNION ALL
    SELECT *, 'Long waits, airports' FROM splittable WHERE long_wait = 1 AND PULocationID IN (132, 138)
    UNION ALL
    SELECT *, 'Long waits, all' FROM splittable WHERE long_wait = 1
)
GROUP BY 1
ORDER BY 1;
