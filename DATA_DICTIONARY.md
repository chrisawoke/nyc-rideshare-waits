# Data dictionary

## Source

NYC Taxi and Limousine Commission, **High Volume For-Hire Vehicle trip records**, June 2026.
Every trip completed by a company dispatching more than 10,000 trips a day in New York City,
which in this month means Uber and Lyft.
<https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page>

Taxi zones: TLC `taxi_zone_lookup.csv`, 265 zones with borough and name.

## Columns read from the source

| Column | Type | Meaning |
| --- | --- | --- |
| `hvfhs_license_num` | text | Company. `HV0003` Uber, `HV0005` Lyft |
| `request_datetime` | timestamp | Rider requests a ride |
| `on_scene_datetime` | timestamp | Driver arrives at the pickup point |
| `pickup_datetime` | timestamp | Rider is picked up |
| `PULocationID` | integer | Pickup taxi zone. 264 and 265 are "Unknown" and "Outside of NYC" |
| `DOLocationID` | integer | Drop-off taxi zone |
| `trip_miles` | decimal | Distance of the trip itself |
| `trip_time` | integer | Seconds from pickup to drop-off |
| `base_passenger_fare` | decimal | Fare before tolls, taxes, fees and tips, USD |
| `tips` | decimal | Tip, USD |
| `driver_pay` | decimal | Paid to the driver before tips, USD |
| `shared_request_flag` | text | Rider asked for a shared ride |

## Derived columns (table `trips`, built by `sql/01_clean.sql`)

| Column | Definition |
| --- | --- |
| `operator` | `Uber` or `Lyft`, from `hvfhs_license_num` |
| `borough`, `zone_name` | From the zone lookup, on the pickup zone |
| `wait_min` | `pickup_datetime` minus `request_datetime`, in minutes. **The wait.** |
| `to_arrive_min` | `on_scene_datetime` minus `request_datetime`: the driver on the way |
| `at_curb_min` | `pickup_datetime` minus `on_scene_datetime`: driver and rider finding each other |
| `hr` | Hour of the request, 0 to 23 |
| `daytype` | `weekend` for Saturday and Sunday requests, otherwise `weekday` |
| `long_wait` | 1 if `wait_min` is over 10 minutes |

## Terms used in the write-up

| Term | Meaning |
| --- | --- |
| **Long wait** | More than 10 minutes from request to pickup. Tested at 8 and 12 in `sql/06_sensitivity.sql` |
| **Zone-hour** | One pickup zone, at one hour of the day, on weekdays or on weekends. 12,356 occur in the month. The smallest unit an incentive scheme can realistically be switched on for |
| **Top tenth** | The 1,235 zone-hours producing the most long waits |
| **Late night** | Requests from 22:00 to 04:59 |
| **Weekday-evening airports** | JFK (zone 132) and LaGuardia (zone 138), weekday requests 18:00 to 00:59 |
| **Pay per trip-hour** | `driver_pay` divided by `trip_time`. Excludes time driving to a pickup and time waiting for one, which the data does not record |

## Outputs (`outputs/`)

Each CSV is one `out_*` table from the SQL, named without the prefix.

| File | Made by | Holds |
| --- | --- | --- |
| `cleaning_audit.csv` | 01 | Rows removed by each rule |
| `negative_by_operator.csv` | 01 | Negative waits by company |
| `headline.csv` | 02 | Rides, long waits, median and 90th-percentile wait |
| `by_operator.csv` | 02 | Share of rides and long-wait rate by company |
| `by_hour.csv` | 03 | Long-wait rate by hour of request |
| `by_borough.csv` | 03 | Share of rides and of long waits by borough |
| `segments.csv` | 03 | Late night and weekday-evening airports |
| `wait_split.csv` | 04 | Driver arrival against curb time |
| `unsplittable.csv` | 04 | Rides whose wait cannot be split |
| `concentration_curve.csv` | 05 | Cumulative share of long waits by zone-hour, worst first |
| `top_tenth.csv`, `top_tenth_by_borough.csv` | 05 | What the top tenth is made of |
| `pay.csv`, `pay_correlation.csv` | 05 | Driver pay per trip-hour |
| `sensitivity.csv` | 06 | The ranking at 8, 10 and 12 minutes |
