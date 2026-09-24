# Lesson 6 — Incremental models and late corrections

[Course home](../learning_path.md) · [Next: snapshots](07_snapshots.md)

**Goal:** see how a corrected old event reaches an incremental table.
Start with the baseline built and the lookup repaired after Lesson 5.

## 1. Read the incremental configuration

Open [fct_grid_hourly.sql](../../models/marts/fct_grid_hourly.sql). Identify:

- `materialized='incremental'`: maintain an existing table on later runs.
- `unique_key='grid_hour_id'`: identify the existing region/hour to replace.
- `incremental_strategy='delete+insert'`: replace rows for selected keys.
- `is_incremental()`: include the watermark filter when updating an existing
  incremental table, and omit it for the initial build or full refresh.

The unique key config does not itself prove uniqueness. The model's data test
checks that assumption. Inspect the `dbt_utils.generate_surrogate_key` call.

## 2. See the watermark in compiled SQL

```powershell
& $dbt compile --profiles-dir . --select fct_grid_hourly
Get-Content target/learning/compiled/dbt_energy_analytics/models/marts/fct_grid_hourly.sql
& $dbt show --profiles-dir . --inline "select count(*) as grid_hours, max(ingested_at) as watermark from analytics_marts.fct_grid_hourly"
```

**Expect:** **144** rows and watermark **2026-01-04 00:00:00**. The latest baseline
event interval starts at 2026-01-03 23:00 UTC and arrives an hour later.

Find the compiled `where ingested_at >= ...` clause. The inclusive comparison
allows safe replay of records tied at the watermark.

## 3. Land the updated batch

```powershell
& $py scripts/load_demo.py --scenario updated
$sql = @'
select reading_id, generation_mwh, ingested_at
from raw.generation
where region = 'ISONE' and fuel_type = 'natural_gas'
  and hour_utc = timestamp '2026-01-01 18:00:00'
order by ingested_at
'@
& $dbt show --profiles-dir . --inline $sql --limit 10
```

**Expect:** two revisions: 620 MWh originally and 720 MWh arriving on
2026-01-05. Raw data retains both. The latest-revision view chooses the latter.
The source now has 1,153 generation rows, 289 meter rows, and 3 facilities.

The materialized fact has not been updated just by loading raw data. A staging
view can show new data before a downstream table is rebuilt.

## 4. Run dbt and inspect the corrected hour

```powershell
& $dbt build --profiles-dir .
$sql = @'
select generation_mwh, estimated_co2_kg,
       round(production_co2_kg_per_mwh, 3) as kg_per_mwh
from analytics_marts.fct_grid_hourly
where region = 'ISONE' and hour_utc = timestamp '2026-01-01 18:00:00'
'@
& $dbt show --profiles-dir . --inline $sql
```

**Expect:** **1,415 MWh**, **335,500 kg CO2**, about **237.102 kg/MWh**.
The extra 100 MWh of gas adds 40,000 kg in this synthetic calculation.

```powershell
$sql = @'
select 'grid_hours' as model, count(*) as row_count from analytics_marts.fct_grid_hourly
union all
select 'facility_hours', count(*) from analytics_marts.fct_facility_hourly
union all
select 'facility_days', count(*) from analytics_marts.mart_facility_daily
union all
select 'cleaner_windows', count(*) from analytics_marts.mart_cleaner_windows
'@
& $dbt show --profiles-dir . --inline $sql --limit 10
& $dbt show --profiles-dir . --inline "select load_mwh, round(estimated_production_proxy_co2_kg, 3) as estimated_co2_kg from analytics_marts.fct_facility_hourly where facility_id = 'F001' and hour_utc = timestamp '2026-01-01 18:00:00'"
```

**Expect:** counts **192**, **288**, **12**, **8**; corrected facility load
**1.35 MWh** and approximately **320.088 kg CO2**. The facility fact is fully
rebuilt, so both the meter correction and revised grid factor propagate.

## 5. Replay the updated batch

```powershell
& $py scripts/load_demo.py --scenario updated
& $dbt build --profiles-dir .
& $dbt show --profiles-dir . --inline "select count(*) as grid_hours, count(distinct grid_hour_id) as unique_grid_hours from analytics_marts.fct_grid_hourly"
```

**Expect:** **192** for both counts. A rerun should not add another copy.

## 6. Explain the assumptions

The filter uses arrival time rather than event time, so an old event can be
reprocessed. It assumes ingestion timestamps advance monotonically. Backdated
arrival times, hard deletions, or changed reference factors need a backfill/full
refresh strategy. The upstream views still scan source history; incremental
materialization alone does not make the whole pipeline incremental.

**Checkpoint:** "I can show a late correction replacing an old grid hour and
explain the watermark, unique key, replay behavior, and backfill limits."

**Answer aloud:** Why would `hour_utc > max(hour_utc)` miss this correction?
