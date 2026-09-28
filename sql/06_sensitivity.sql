-- 06_sensitivity.sql
-- 10 minutes is a judgement, not a fact. If the conclusion only held at exactly 10, it
-- would not be a conclusion. Rerun the ranking at 8 and 12 and see what moves.

CREATE OR REPLACE TABLE out_sensitivity AS
WITH thresholds AS (SELECT unnest([8, 10, 12]) AS minutes),
cells AS (
    SELECT th.minutes, PULocationID, daytype, hr,
           count(*) AS trips,
           sum((wait_min > th.minutes)::INTEGER) AS long_waits
    FROM trips, thresholds th
    GROUP BY ALL
),
ranked AS (
    SELECT *,
           row_number() OVER (PARTITION BY minutes ORDER BY long_waits DESC, trips) AS rank,
           count(*) OVER (PARTITION BY minutes) AS n_cells
    FROM cells
),
top AS (SELECT * FROM ranked WHERE rank <= floor(n_cells * 0.10)),
overlap AS (
    SELECT a.minutes, count(*) AS shared
    FROM top a
    JOIN top b ON b.minutes = 10
              AND (a.PULocationID, a.daytype, a.hr) = (b.PULocationID, b.daytype, b.hr)
    GROUP BY 1
)
SELECT r.minutes,
       round(100.0 * sum(r.long_waits) / sum(r.trips), 1)                                     AS long_wait_pct,
       round(100.0 * sum(r.long_waits) FILTER (WHERE r.rank <= floor(r.n_cells * 0.10))
                   / sum(r.long_waits), 1)                                                    AS top_tenth_share_pct,
       round(100.0 * max(o.shared) / floor(max(r.n_cells) * 0.10), 0)                        AS same_cells_as_10min_pct
FROM ranked r
JOIN overlap o USING (minutes)
GROUP BY 1
ORDER BY 1;
