# Lesson 2 — Ingestion and raw data

[Course home](../learning_path.md) · [Next: models](03_models.md)

**Goal:** identify what enters the warehouse before dbt transforms anything.
Keep Lesson 1's PowerShell settings active.

## 1. Read the loader

Open [load_demo.py](../../scripts/load_demo.py). Find the two regions, six fuels,
three facilities, and day/hour loops. Then find the three raw tables and the
primary keys and `on conflict` behavior that make repeated ingestion safe.

This script fills the extraction/loading role. dbt starts with the tables it
creates. In a cloud extension, a connector performs the landing step.

## 2. Load the baseline

```powershell
& $py scripts/load_demo.py --scenario baseline
```

**Expect:** a message containing your `learning*.duckdb` path. Check that path.

## 3. Count the raw rows

```powershell
$sql = @'
select 'generation' as source_table, count(*) as row_count from raw.generation
union all
select 'facility_load', count(*) from raw.facility_load
union all
select 'facilities', count(*) from raw.facilities
'@
& $dbt show --profiles-dir . --inline $sql --limit 10
```

**Expect:** generation **864**, facility load **216**, facilities **3**.
Explain the counts: `2 * 6 * 72` generation rows and `3 * 72` load rows.
`dbt show` previews a query; it does not create a stored model.

## 4. Inspect one hour

```powershell
$sql = @'
select region, hour_utc, fuel_type, generation_mwh, ingested_at
from raw.generation
where region = 'ISONE' and hour_utc = timestamp '2026-01-01 18:00:00'
order by fuel_type
'@
& $dbt show --profiles-dir . --inline $sql --limit 10
```

**Expect:** coal 50, hydro 75, natural gas 620, nuclear 350, solar 0, wind 220 MWh.
The solar row is an observed zero in the fixture, not a missing reading.

`hour_utc` identifies the interval; `ingested_at` identifies arrival time. The raw
grain includes a revision ID. Multiple revisions can describe one region/hour/fuel.

## 5. Repeat the load

```powershell
& $py scripts/load_demo.py --scenario baseline
& $dbt show --profiles-dir . --inline "select count(*) as row_count from raw.generation"
```

**Expect:** still **864**, not 1,728. Locate the loader statement that makes this
true. Ingestion idempotency is separate from dbt incremental-model behavior.

**Checkpoint:** "I can explain the landing tables, their grain and units, and
why replaying this input batch does not duplicate raw data."

**Answer aloud:** Why should a correction have a new revision ID and arrival
time instead of silently erasing the original raw record?
