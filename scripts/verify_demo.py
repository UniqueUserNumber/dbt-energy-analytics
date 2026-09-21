"""Integration checks in a temporary warehouse; the user's demo is untouched.

Run dbt deps first. Includes corrections, reruns, snapshot history, full-refresh
equivalence, and deliberate missing-factor/missing-hour failures.
"""

import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import duckdb

from load_demo import ROOT, load_demo


def dbt(*args, expect_failure=False):
    result = subprocess.run(
        [sys.executable, "-c", "from dbt.cli.main import cli; cli()",
         *args, "--profiles-dir", str(ROOT)], cwd=ROOT,
        text=True, capture_output=True, env=os.environ.copy(),
    )
    if expect_failure:
        if result.returncode != 1 or "FAIL" not in result.stdout:
            raise AssertionError(f"Expected a data-test failure:\n{result.stdout}\n{result.stderr}")
    elif result.returncode:
        raise RuntimeError(f"dbt {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}")
    summaries = [line for line in result.stdout.splitlines()
                 if "PASS=" in line or "Completed" in line]
    print(f"dbt {' '.join(args)}: " + " / ".join(summaries), flush=True)


def rows(path, sql):
    with duckdb.connect(str(path)) as con:
        return con.execute(sql).fetchall()


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}", flush=True)


def compare_exports(path, exports, expected):
    """Allow only floating-point aggregation noise, never keys/history changes."""
    max_delta = 0.0
    for name, query in exports.items():
        actual = rows(path, query)
        if len(actual) != len(expected[name]):
            raise AssertionError(f"{name}: row count changed")
        for index, (actual_row, expected_row) in enumerate(zip(actual, expected[name])):
            for column, (actual_value, expected_value) in enumerate(zip(actual_row, expected_row)):
                if isinstance(actual_value, float) and isinstance(expected_value, float):
                    if not math.isclose(actual_value, expected_value, rel_tol=1e-12, abs_tol=1e-9):
                        raise AssertionError(f"{name}[{index}][{column}]: {actual_value} != {expected_value}")
                    max_delta = max(max_delta, abs(actual_value - expected_value))
                elif actual_value != expected_value:
                    raise AssertionError(f"{name}[{index}][{column}]: {actual_value} != {expected_value}")
    print(f"Maximum floating-point difference: {max_delta:.3g}", flush=True)


def verify(path):
    load_demo("baseline")
    dbt("build")
    check(rows(path, "select count(*) from analytics_marts.fct_grid_hourly") == [(144,)],
          "baseline contains 2 regions x 72 grid hours")
    check(rows(path, "select count(*) from analytics_marts.fct_facility_hourly") == [(216,)],
          "baseline contains 3 facilities x 72 hours")
    # Independently calculated fixture: 620 gas, 50 coal, 350 nuclear,
    # 75 hydro, 220 wind, and zero solar at ISONE 2026-01-01 18:00 UTC.
    before = rows(path, """select generation_mwh, estimated_co2_kg,
        production_co2_kg_per_mwh from analytics_marts.fct_grid_hourly
        where region = 'ISONE' and hour_utc = '2026-01-01 18:00:00'""")[0]
    check(before[:2] == (1315.0, 295500.0), "known hour has correct generation and CO2 units")
    check(abs(before[2] - 295500 / 1315) < 1e-8, "intensity is generation weighted")
    check(rows(path, """select extract(hour from best_start_hour_utc)
        from analytics_marts.mart_cleaner_windows
        where region = 'ISONE' and date_utc = '2026-01-01'""") == [(11,)],
          "known cleanest 3-hour window starts at 11:00 UTC")

    load_demo("updated")
    dbt("build")
    check(rows(path, "select count(*) from analytics_marts.fct_grid_hourly") == [(192,)],
          "incremental adds day 4 without duplicate keys")
    corrected = rows(path, """select generation_mwh, estimated_co2_kg,
        production_co2_kg_per_mwh from analytics_marts.fct_grid_hourly
        where region = 'ISONE' and hour_utc = '2026-01-01 18:00:00'""")[0]
    check(corrected[:2] == (1415.0, 335500.0), "late correction updates an old grid hour")
    facility = rows(path, """select load_mwh, estimated_production_proxy_co2_kg
        from analytics_marts.fct_facility_hourly
        where facility_id = 'F001' and hour_utc = '2026-01-01 18:00:00'""")[0]
    check(facility[0] == 1.35 and abs(facility[1] - 1.35 * 335500 / 1415) < 1e-8,
          "load correction and revised grid factor both reach facility estimates")
    history = rows(path, """select owner_name, dbt_valid_from, dbt_valid_to
        from analytics_snapshots.facility_history where facility_id = 'F001'
        order by dbt_valid_from""")
    check(len(history) == 2 and history[0][2] == history[1][1]
          and history[1][2] is None and history[1][0] == "Demo Harbor Cooperative",
          "snapshot preserves old owner and opens one new current version")
    exports = {
        "grid": "select * from analytics_marts.fct_grid_hourly order by grid_hour_id",
        "facility": "select * from analytics_marts.fct_facility_hourly order by facility_hour_id",
        "daily": "select * from analytics_marts.mart_facility_daily order by facility_id, date_utc",
        "windows": "select * from analytics_marts.mart_cleaner_windows order by region, date_utc",
        "history": "select * from analytics_snapshots.facility_history order by dbt_scd_id",
    }
    expected = {name: rows(path, query) for name, query in exports.items()}
    load_demo("updated")
    dbt("build")
    compare_exports(path, exports, expected)
    print("PASS: repeated ingestion and incremental build are idempotent", flush=True)
    dbt("build", "--full-refresh")
    compare_exports(path, exports, expected)
    print("PASS: incremental results equal full rebuild; snapshot history survives", flush=True)

    # The tests must fail for data defects, not just pass for good fixtures.
    rows(path, "delete from analytics_reference.demo_emission_factors where fuel_type = 'coal'")
    dbt("test", "--select", "stg_generation", expect_failure=True)
    dbt("seed")
    rows(path, """delete from analytics_marts.fct_grid_hourly
        where region = 'ISONE' and hour_utc = '2026-01-01 01:00:00'""")
    dbt("test", "--select", "assert_complete_grid_days", expect_failure=True)
    print("PASS: missing factors and missing grid hours are detected", flush=True)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="dbt-energy-verify-") as directory:
        path = Path(directory) / "verification.duckdb"
        os.environ.update({
            "DBT_DUCKDB_PATH": str(path),
            "DBT_TARGET_PATH": str(Path(directory) / "target"),
            "DBT_LOG_PATH": str(Path(directory) / "logs"),
            "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
            "DBT_USE_COLORS": "false",
        })
        verify(path)
    print("All integration checks passed.")
