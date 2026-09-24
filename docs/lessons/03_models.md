# Lesson 3 — Seeds, staging, macros, and dependencies

[Course home](../learning_path.md) · [Next: metrics](04_metrics.md)

**Goal:** turn landed data into a dbt graph and inspect the SQL that runs.

## 1. Load the reference seed

Open [demo_emission_factors.csv](../../seeds/demo_emission_factors.csv).
These are invented direct-CO2 factors for this demonstration.

```powershell
& $dbt seed --profiles-dir .
& $dbt show --profiles-dir . --inline "select * from analytics_reference.demo_emission_factors order by fuel_type" --limit 10
```

**Expect:** six rows. A seed suits a small, versioned lookup; a large or changing
operational feed belongs in an ingestion process.

## 2. Find `source()` and `ref()`

Open [sources.yml](../../models/staging/sources.yml) and
[stg_generation.sql](../../models/staging/stg_generation.sql).
`source('raw_energy', 'generation')` resolves a declared raw relation and adds
source metadata and lineage. It does not ingest data.

Open [int_generation_latest.sql](../../models/intermediate/int_generation_latest.sql).
`ref('stg_generation')` resolves a dbt resource and declares a dependency.
Instead of maintaining job order separately, dbt derives it from references.

## 3. Compile the staging models before running them

```powershell
& $dbt compile --profiles-dir . --select stg_generation stg_facility_load stg_facilities
Get-Content target/learning/compiled/dbt_energy_analytics/models/staging/stg_facility_load.sql
```

Compare [stg_facility_load.sql](../../models/staging/stg_facility_load.sql) with
the compiled output. Find the physical relation and division by 1,000.

The source calls [kwh_to_mwh.sql](../../macros/kwh_to_mwh.sql), a Jinja macro.
The database receives expanded SQL; it does not execute Jinja. This is the dbt
equivalent of a reusable SQL template in a Python pipeline.

## 4. Create the staging views

```powershell
& $dbt run --profiles-dir . --select path:models/staging
& $dbt show --profiles-dir . --inline "select load_mwh from analytics_staging.stg_facility_load where facility_id = 'F001' and hour_utc = timestamp '2026-01-01 18:00:00'"
```

**Expect:** three staging views and **1.1 MWh** for that interval. The source was
1,100 kWh.

`run` executes models. `build` also handles selected seeds, snapshots, and tests
in dependency order. An upstream test failure can skip downstream resources;
inspect the first failure rather than treating each skip as a separate bug.

## 5. Preview the dependency selection

```powershell
& $dbt ls --profiles-dir . --select +fct_facility_hourly --resource-type model
```

A leading `+` selects ancestors and the named model; a trailing `+` selects
descendants. This resource filter displays models only. The full graph also has
sources, seeds, tests, and a snapshot.

## 6. Build the entire baseline

```powershell
& $dbt build --profiles-dir .
& $py scripts/query_demo.py
```

**Expect:** 11 models, one seed, one snapshot, and 81 data tests succeed in the
unmodified starter. The report has 9 facility-day rows and 6 window rows. Log
formatting can vary; there should be no errors or skipped resources.

Inspect physical materializations:

```powershell
& $dbt show --profiles-dir . --inline "select table_schema, table_name, table_type from information_schema.tables where table_schema in ('analytics_staging', 'analytics_marts') order by table_schema, table_name" --limit 20
```

**Expect:** staging relations are views. Marts, including the incremental fact,
are physical tables. Incremental describes how a table is maintained.

**Checkpoint:** "I can trace dependencies, compile a macro into SQL, and explain
why this project uses views, tables, and an incremental table."

**Answer aloud:** What happens if a downstream model runs before its upstream
relations exist? How does a leading `+` help?
