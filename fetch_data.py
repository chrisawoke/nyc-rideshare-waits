"""
Pulls one month of NYC high-volume for-hire trips (Uber, Lyft) from the Taxi and
Limousine Commission's public trip records, keeping only the columns the analysis uses,
and the taxi-zone lookup that names each pickup zone.

One month, not a year: each monthly file is about 510MB, and reading only the needed
columns roughly halves that. Run once; everything downstream reads the local copies.

Source: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
"""
from pathlib import Path
import urllib.request

import duckdb

MONTH = "2026-06"
TRIPS_URL = f"https://d37ci6vzurychx.cloudfront.net/trip-data/fhvhv_tripdata_{MONTH}.parquet"
ZONES_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

COLUMNS = [
    "hvfhs_license_num",   # HV0003 = Uber, HV0005 = Lyft
    "request_datetime",    # rider asks for a ride
    "on_scene_datetime",   # driver arrives at the pickup point
    "pickup_datetime",     # rider is in the car; request to pickup is the whole wait
    "PULocationID",
    "DOLocationID",
    "trip_miles",
    "trip_time",           # seconds
    "base_passenger_fare", # fare before tolls, taxes, fees and tips
    "tips",
    "driver_pay",          # what the driver is paid, before tips
    "shared_request_flag",
]

DATA = Path("data")
DATA.mkdir(exist_ok=True)

if __name__ == "__main__":
    out = DATA / f"trips_{MONTH}.parquet"
    if not out.exists():
        con = duckdb.connect()
        con.execute("INSTALL httpfs; LOAD httpfs;")
        cols = ", ".join(COLUMNS)
        con.execute(
            f"COPY (SELECT {cols} FROM read_parquet('{TRIPS_URL}')) "
            f"TO '{out.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)"
        )
    zones = DATA / "taxi_zone_lookup.csv"
    if not zones.exists():
        urllib.request.urlretrieve(ZONES_URL, zones)

    n = duckdb.sql(f"SELECT count(*) FROM '{out.as_posix()}'").fetchone()[0]
    print(f"{out}: {n:,} trips, {out.stat().st_size / 1e6:.0f} MB on disk")
