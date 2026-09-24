# Lesson 9 — Build your own regional mart

[Course home](../learning_path.md) · [Next: Fivetran and Snowflake](10_fivetran_snowflake.md)

**Goal:** make a complete dbt change: SQL, descriptions, data tests, and a commit.
This model is an exercise for you to implement; it is not already in `models/`.

## 1. Define the output before writing SQL

Create a daily grid summary with one row per **region and UTC date**. Include
observed hours, total generation, estimated direct CO2, and generation-weighted
daily intensity. Write down why this weighting differs from facility load weighting.

Start a branch from your current checkout:

```powershell
git status --short
git switch -c codex/learn-region-daily
```

If this branch already exists from an earlier session, switch to it without `-c`.
Keep unrelated local changes separate from the exercise commit.

## 2. Write the model

Create `models/marts/mart_region_daily.sql` in your editor. Try it yourself first;
then compare with this complete example. If the file already exists, review it
instead of overwriting previous work.

```sql
select
    region,
    cast(hour_utc as date) as date_utc,
    count(*) as observed_hours,
    sum(generation_mwh) as generation_mwh,
    sum(estimated_co2_kg) as estimated_co2_kg,
    sum(estimated_co2_kg) / nullif(sum(generation_mwh), 0)
        as generation_weighted_co2_kg_per_mwh
from {{ ref('fct_grid_hourly') }}
group by region, cast(hour_utc as date)
```

The marts folder defaults to a table, so this model needs no materialization
override. `ref()` makes the grid fact its upstream dependency.

## 3. Add descriptions and generic tests

Create `models/marts/region_daily.yml`:

```yaml
version: 2
models:
  - name: mart_region_daily
    description: "Daily regional generation and illustrative direct CO2, one row per region/UTC date."
    data_tests:
      - dbt_utils.unique_combination_of_columns:
          arguments:
            combination_of_columns: [region, date_utc]
    columns:
      - name: region
        description: "Synthetic grid region."
        data_tests: [not_null]
      - name: date_utc
        description: "UTC date of the generation intervals."
        data_tests: [not_null]
      - name: observed_hours
        description: "Hourly grid rows present for this region/date."
      - name: generation_mwh
        description: "Sum of generation over the observed hours."
        data_tests: [not_null, non_negative]
      - name: estimated_co2_kg
        description: "Sum of illustrative direct CO2 estimates."
        data_tests: [not_null, non_negative]
      - name: generation_weighted_co2_kg_per_mwh
        description: "Daily estimated CO2 divided by daily generated MWh."
        data_tests: [not_null, non_negative]
```

Use a new YAML file so you do not have to merge another model into an existing
list while learning the structure. dbt reads both files.

## 4. Add a business-rule test

Create `tests/assert_region_daily_metrics.sql`:

```sql
select *
from {{ ref('mart_region_daily') }}
where observed_hours <> 24
   or generation_mwh <= 0
   or abs(
       estimated_co2_kg
       - generation_weighted_co2_kg_per_mwh * generation_mwh
   ) > 0.000001
```

This checks complete represented days and the relationship among the reported
metrics. The generic `not_null` tests catch nulls that SQL comparisons would
otherwise skip. This still does not detect an entirely absent region-day.

## 5. Compile, build, and inspect

```powershell
& $dbt compile --profiles-dir . --select mart_region_daily
Get-Content target/learning/compiled/dbt_energy_analytics/models/marts/mart_region_daily.sql
& $dbt build --profiles-dir . --select +mart_region_daily
& $dbt show --profiles-dir . --inline "select * from analytics_marts.mart_region_daily order by region, date_utc" --limit 20
```

**Expect:** **8** rows after Lesson 6: two regions across four dates. A baseline-only
warehouse would have 6. Every represented day should have 24 observed hours.
Read the build output to confirm the new tests actually ran.

## 6. Test a mistaken formula

Temporarily change the intensity calculation to
`avg(production_co2_kg_per_mwh)`. Predict whether the business-rule test passes.
Rebuild the selected model and inspect the failure. Restore the ratio-of-sums
formula and rerun until the model and tests pass.

This connects a modeling decision to a test that can catch a plausible mistake.

## 7. Document and commit your work

```powershell
& $dbt docs generate --profiles-dir .
git diff --check
git status --short
git add models/marts/mart_region_daily.sql models/marts/region_daily.yml tests/assert_region_daily_metrics.sql
git diff --cached
git commit -m "Add daily regional energy metrics"
```

Review the staged diff before committing. It should contain only your three
exercise files. Push your branch when ready and open a pull request; other
readers should use their own fork for that step. Check CI for that commit.

**Checkpoint:** "I added a regional mart, chose its grain and weighting, wrote
tests that catch an incorrect formula, and verified its documented output."

**Next exercise:** add a calendar/region spine so an entirely missing day also
fails validation. Write the expected behavior before implementing it.
