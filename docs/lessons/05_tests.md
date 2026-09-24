# Lesson 5 — Data tests and a controlled failure

[Course home](../learning_path.md) · [Next: incremental models](06_incremental.md)

**Goal:** learn what a dbt data test checks, see a real failure, and repair it.
Complete Lesson 3's build first. Use only your `learning*.duckdb` database here.

## 1. Read one generic and one singular test

Open [staging/schema.yml](../../models/staging/schema.yml). Find the relationship
test between `stg_generation.fuel_type` and `demo_emission_factors.fuel_type`.
It checks that every non-null fuel key resolves to a factor.

Open [assert_complete_grid_days.sql](../../tests/assert_complete_grid_days.sql).
This singular test returns region-days that do not have 24 distinct hours.
For these data tests, zero returned failure rows means success.

Open [non_negative.sql](../../macros/non_negative.sql). This custom generic test
can be applied to multiple columns. Notice that its `< 0` comparison does not
catch nulls; a separate `not_null` test handles those.

## 2. Run the staging tests on good data

```powershell
& $dbt test --profiles-dir . --select stg_generation
```

**Expect:** all nine tests selected on that model pass.
Data tests inspect warehouse contents. They are different from unit tests that
provide input fixtures and compare a model's output with explicit expectations.

## 3. Remove one factor from the learning warehouse

This deliberately changes the database lookup, not the tracked CSV. Read the
database path and guard before running the snippet:

```powershell
@'
import os
from pathlib import Path
import duckdb

path = Path(os.environ["DBT_DUCKDB_PATH"])
if not path.name.startswith("learning"):
    raise SystemExit("Use a learning*.duckdb database for this exercise.")
with duckdb.connect(str(path)) as con:
    con.execute("delete from analytics_reference.demo_emission_factors where fuel_type = 'coal'")
print(f"Removed the coal lookup from {path}")
'@ | & $py -
```

The raw coal readings still exist. Predict the failing test before proceeding.

## 4. Observe the intentional failure

```powershell
& $dbt test --profiles-dir . --select stg_generation
```

**Expect a failure here:** the fuel relationship test fails. Eight other tests
pass. This is the intended exercise, not an installation problem.

dbt reports a count of failing test rows, which is not necessarily the number of
raw records. The relationship test can group the missing key. Focus on the
unresolved `coal` key and inspect its compiled SQL under `target/learning`.

## 5. Repair the lookup and verify recovery

```powershell
& $dbt seed --profiles-dir . --select demo_emission_factors
& $dbt test --profiles-dir . --select stg_generation
```

**Expect:** all nine tests pass again. Reseeding restores the tracked CSV's six
rows. Do this recovery before leaving the lesson or building other models.

## 6. Identify a gap in the current coverage

The day-completeness test catches a represented day with missing hours. It cannot
catch a region-day that is entirely absent: there is no group to test. A calendar
and expected-region spine would make that missing day visible.

**Checkpoint:** "I can demonstrate a test failing for a real data defect,
explain the failure, restore the input, and identify a defect it cannot catch."

**Exercise:** Why would replacing a missing factor with zero make this pipeline
look healthy while producing an incorrect result?
