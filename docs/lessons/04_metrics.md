# Lesson 4 — Trace the business calculations

[Course home](../learning_path.md) · [Next: tests](05_tests.md)

**Goal:** explain a reported number from source rows through the final mart.
Use baseline data; complete this lesson before loading the updated scenario.

## 1. Reconstruct one grid hour

Read [int_grid_hourly.sql](../../models/intermediate/int_grid_hourly.sql) and
[fct_grid_hourly.sql](../../models/marts/fct_grid_hourly.sql).
Using Lesson 2's fuel rows:

```text
Generation MWh = 50 + 75 + 620 + 350 + 0 + 220 = 1,315
Estimated CO2 kg = 50 * 950 + 620 * 400 = 295,500
Production intensity kg/MWh = 295,500 / 1,315 = about 224.715
Carbon-free MWh = 75 + 350 + 0 + 220 = 645
Carbon-free share = 645 / 1,315 = about 49.05%
```

Check the model:

```powershell
$sql = @'
select generation_mwh, estimated_co2_kg,
       round(production_co2_kg_per_mwh, 3) as kg_per_mwh,
       round(carbon_free_share * 100, 2) as carbon_free_percent
from analytics_marts.fct_grid_hourly
where region = 'ISONE' and hour_utc = timestamp '2026-01-01 18:00:00'
'@
& $dbt show --profiles-dir . --inline $sql
```

## 2. Follow it into one facility hour

Read [fct_facility_hourly.sql](../../models/marts/fct_facility_hourly.sql).
The join matches the facility region and exact UTC interval.

```powershell
$sql = @'
select facility_id, region, load_mwh,
       round(estimated_production_proxy_co2_kg, 3) as estimated_co2_kg
from analytics_marts.fct_facility_hourly
where facility_id = 'F001' and hour_utc = timestamp '2026-01-01 18:00:00'
'@
& $dbt show --profiles-dir . --inline $sql
```

**Expect:** 1.1 MWh and approximately **247.186 kg CO2**.
Check the units: `MWh * kg/MWh = kg`.

## 3. Inspect the daily metric

Read [mart_facility_daily.sql](../../models/marts/mart_facility_daily.sql).

```powershell
$sql = @'
select observed_hours, matched_grid_hours, load_mwh,
       round(estimated_production_proxy_co2_kg, 2) as estimated_co2_kg,
       round(load_weighted_co2_kg_per_mwh, 2) as weighted_kg_per_mwh
from analytics_marts.mart_facility_daily
where facility_id = 'F001' and date_utc = date '2026-01-01'
'@
& $dbt show --profiles-dir . --inline $sql
```

**Expect:** 24 observed and matched hours, **22.5 MWh**, approximately
**4,318.27 kg CO2**, and **191.92 kg/MWh**.

Daily intensity is `sum(hourly emissions) / sum(hourly load)`. It is load
weighted. An unweighted average gives low-load and high-load hours equal
influence. Find the code that suppresses a daily total when a factor is missing.

## 4. Inspect the cleaner-window calculation

Read [mart_cleaner_windows.sql](../../models/marts/mart_cleaner_windows.sql).
Follow its CTEs: candidate windows, complete windows, ranking, and baseline.

```powershell
$sql = @'
select best_start_hour_utc, job_energy_mwh,
       round(illustrative_co2_difference_kg, 2) as estimated_difference_kg
from analytics_marts.mart_cleaner_windows
where region = 'ISONE' and date_utc = date '2026-01-01'
'@
& $dbt show --profiles-dir . --inline $sql
```

**Expect:** start **11:00 UTC**, a **3 MWh** job, and approximately **248.79 kg**
difference versus an 18:00 UTC start. Find why three consecutive hours are
required, how ties are broken, and why a window cannot cross midnight.

## 5. Explain the limits

These synthetic, generation-based estimates do not trace imports/exports, use
marginal emissions, forecast conditions, or match contracts. A lower estimate
does not establish actual avoided emissions. Read [the methodology](../methodology.md).

**Checkpoint:** "I can reconstruct the calculation, explain its weighting and
units, and state what the cleaner-window result means."

**Exercise:** What goes wrong if you join only on date instead of region and
hour? Name a test that would detect the resulting problem.
