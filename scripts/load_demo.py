"""Load original, deterministic demo data. No APIs, credentials, or private data."""

import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
REGIONS = ("ISONE", "PJM")
FUELS = ("natural_gas", "coal", "nuclear", "hydro", "wind", "solar")
START = datetime(2026, 1, 1)
FACILITIES = (
    ("F001", "Harbor Compute Lab", "ISONE", "Demo Research Group", START),
    ("F002", "Pine Battery Workshop", "ISONE", "Demo Storage Group", START),
    ("F003", "River Data Center", "PJM", "Demo Compute Group", START),
)


def database_path() -> Path:
    path = Path(os.environ.get("DBT_DUCKDB_PATH", ROOT / "warehouse/energy.duckdb"))
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def load_demo(scenario: str) -> Path:
    """Append new revisions idempotently; never roll a newer scenario backward."""
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    days = 3 if scenario == "baseline" else 4
    generation = []
    loads = []
    for day in range(days):
        for hour in range(24):
            timestamp = START + timedelta(days=day, hours=hour)
            ingested = timestamp + timedelta(hours=1)
            for region_index, region in enumerate(REGIONS):
                amounts = (
                    500 + 180 * region_index + 5 * day
                    + (120 if 17 <= hour <= 21 else 0)
                    - (80 if 10 <= hour <= 15 else 0),
                    50 + 150 * region_index,
                    350 + 100 * region_index,
                    75,
                    160 + 20 * ((hour + day) % 5),
                    round(max(0, 1 - abs(hour - 12) / 6) * 450, 3),
                )
                for fuel, amount in zip(FUELS, amounts):
                    key = f"{region}_{timestamp:%Y%m%d%H}_{fuel}_r1"
                    generation.append((key, region, timestamp, fuel, amount, ingested))
            for index, facility in enumerate(FACILITIES):
                load_kwh = 800 + index * 350 + (300 if 8 <= hour <= 18 else 0) + day * 10
                key = f"{facility[0]}_{timestamp:%Y%m%d%H}_r1"
                loads.append((key, facility[0], timestamp, load_kwh, ingested))

    facilities = list(FACILITIES)
    if scenario == "updated":
        # Old event hour, new ingestion timestamp: incremental must replace it.
        hour = START + timedelta(hours=18)
        arrival = START + timedelta(days=4)
        generation.append(("ISONE_2026010118_natural_gas_r2", "ISONE", hour,
                           "natural_gas", 720, arrival))
        loads.append(("F001_2026010118_r2", "F001", hour, 1350, arrival))
        facilities[0] = ("F001", "Harbor Compute Lab", "ISONE",
                         "Demo Harbor Cooperative", START + timedelta(days=3))

    with duckdb.connect(str(path)) as con:
        con.execute("begin transaction")
        con.execute("create schema if not exists raw")
        con.execute("""create table if not exists raw.generation (
            reading_id varchar primary key, region varchar, hour_utc timestamp,
            fuel_type varchar, generation_mwh double, ingested_at timestamp)""")
        con.execute("""create table if not exists raw.facility_load (
            reading_id varchar primary key, facility_id varchar, hour_utc timestamp,
            load_kwh double, ingested_at timestamp)""")
        con.execute("""create table if not exists raw.facilities (
            facility_id varchar primary key, facility_name varchar, region varchar,
            owner_name varchar, updated_at timestamp)""")
        latest = con.execute("select max(ingested_at) from raw.generation").fetchone()[0]
        if scenario == "baseline" and latest and latest > START + timedelta(days=3):
            raise ValueError("This database already has updated data. Keep using updated, "
                             "or set DBT_DUCKDB_PATH to a new file for a fresh baseline.")
        con.executemany("insert into raw.generation values (?, ?, ?, ?, ?, ?) "
                        "on conflict do nothing", generation)
        con.executemany("insert into raw.facility_load values (?, ?, ?, ?, ?) "
                        "on conflict do nothing", loads)
        con.executemany("""insert into raw.facilities values (?, ?, ?, ?, ?)
            on conflict (facility_id) do update set
                facility_name = excluded.facility_name, region = excluded.region,
                owner_name = excluded.owner_name, updated_at = excluded.updated_at
            where excluded.updated_at > facilities.updated_at""", facilities)
        con.execute("commit")
    print(f"Loaded {scenario} scenario into {path}")
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("baseline", "updated"), default="baseline")
    load_demo(parser.parse_args().scenario)
