# Lesson 7 — Snapshots and ownership history

[Course home](../learning_path.md) · [Next: docs and CI](08_docs_ci.md)

**Goal:** distinguish preserving historical versions from updating a fact table.
Lesson 3 observed the baseline owner; Lesson 6 observed the changed owner.

## 1. Read the snapshot definition

Open [facility_history.yml](../../snapshots/facility_history.yml). Identify the
source relation, stable `facility_id`, timestamp strategy, and `updated_at` field.
The YAML describes how dbt recognizes a newer version of the same facility.

The grid fact replaces a corrected value. The snapshot preserves older metadata
versions and marks when each version was valid.

## 2. Inspect the raw current owner

```powershell
& $dbt show --profiles-dir . --inline "select facility_id, owner_name, updated_at from raw.facilities where facility_id = 'F001'"
```

**Expect:** one row, owner **Demo Harbor Cooperative**, updated on **2026-01-04**.
The raw metadata table stores current state, not all previous owners.

## 3. Inspect the two historical versions

```powershell
$sql = @'
select facility_id, owner_name, dbt_valid_from, dbt_valid_to
from analytics_snapshots.facility_history
where facility_id = 'F001'
order by dbt_valid_from
'@
& $dbt show --profiles-dir . --inline $sql --limit 10
```

**Expect:** the original **Demo Research Group** version starts on 2026-01-01
and closes on 2026-01-04. **Demo Harbor Cooperative** starts on 2026-01-04 and has
null `dbt_valid_to`, marking it current. Timestamp precision/display may vary.

If you only ever built the updated scenario, the original version is absent.
Snapshots preserve changes they observe; they cannot reconstruct unseen history.

## 4. Follow the current dimension

Open [dim_facilities.sql](../../models/marts/dim_facilities.sql). Find its filter
on `dbt_valid_to`. Then query:

```powershell
& $dbt show --profiles-dir . --inline "select count(*) as current_facilities from analytics_marts.dim_facilities"
& $dbt show --profiles-dir . --inline "select count(*) as historical_versions from analytics_snapshots.facility_history"
```

**Expect:** **3** current facilities and **4** historical versions across them.

## 5. Snapshot unchanged data again

```powershell
& $dbt snapshot --profiles-dir . --select facility_history
& $dbt test --profiles-dir . --select assert_one_current_facility
& $dbt show --profiles-dir . --inline "select count(*) as historical_versions from analytics_snapshots.facility_history"
```

**Expect:** still **4** versions and the current-version test passes.

`dbt build --full-refresh` does not erase snapshot history. A model can often be
rebuilt from complete source history; the snapshot itself may be your only copy
of previously observed metadata. [dbt snapshot reference](https://docs.getdbt.com/docs/build/snapshots)

## 6. Identify the reporting choice

The facility fact currently uses the current facility dimension. The fixture's
region never changes. Historical ownership is demonstrated by the snapshot but
is not used to allocate old emissions to an owner. An as-of ownership report
would need an effective-date join to the snapshot intervals.

**Checkpoint:** "I can explain why incremental facts and SCD2 snapshots solve
different problems and show one current plus one closed ownership version."

**Exercise:** sketch the interval join needed to attribute a reading to the owner
at its event time, including what should happen exactly at the change timestamp.
