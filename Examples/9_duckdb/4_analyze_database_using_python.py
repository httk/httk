#!/usr/bin/env python

try:
    import duckdb
    con = duckdb.connect('sample.duckdb')
    # DuckDB has an efficient integration with e.g. Pandas:
    df = con.execute("SELECT total_energy, k_vrh, g_vrh from result_elasticresult").fetchdf()
    print(df.to_markdown())
except ImportError:
    print("duckdb not installed: `pip install duckdb` (Python 3 only).")

