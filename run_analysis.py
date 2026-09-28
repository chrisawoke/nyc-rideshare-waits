"""
Runs the SQL in sql/ in order against a local DuckDB file, then writes every table named
out_* to outputs/ as CSV. Those CSVs are what the charts, the notebook and the checks read,
so every number in the write-up traces back to one query in one file.

    python fetch_data.py      # once: downloads the month (about 400MB)
    python run_analysis.py    # a few minutes on a laptop
"""
from pathlib import Path

import duckdb

SQL = sorted(Path("sql").glob("*.sql"))
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)

if __name__ == "__main__":
    con = duckdb.connect("data/rideshare.duckdb")
    for f in SQL:
        print(f"running {f.name}")
        con.execute(f.read_text(encoding="utf-8"))

    tables = [r[0] for r in con.sql(
        "SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'out\\_%' ESCAPE '\\' ORDER BY 1"
    ).fetchall()]
    for t in tables:
        df = con.sql(f"SELECT * FROM {t}").df()
        # DuckDB sums integers into HUGEINT, which pandas receives as float: 129444.0.
        for c in df.select_dtypes("float").columns:
            if (df[c].dropna() % 1 == 0).all() and not c.endswith(("_pct", "_min", "_hour")):
                df[c] = df[c].astype("Int64")
        df.to_csv(OUT / f"{t.removeprefix('out_')}.csv", index=False)
    print(f"wrote {len(tables)} tables to {OUT}/")
