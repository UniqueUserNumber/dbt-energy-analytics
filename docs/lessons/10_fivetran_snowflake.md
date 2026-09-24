# Lesson 10 — Fivetran and Snowflake extension

[Course home](../learning_path.md)

**Goal:** learn each cloud component with a small, observable result before
attempting the whole pipeline. This is an optional implementation exercise.
Cloud connections and the full Snowflake port have not been run or configured
for you. Lessons 1-9 remain the verified local path.

The stages are: a fixture CSV in S3, a Fivetran sync into Snowflake, one dbt
staging model, then the full transformation graph. Use the known fixture first
to learn the plumbing. A documented real energy source is the next extension.

## 1. Prepare the accounts and destination

You need access to AWS S3, Fivetran, and Snowflake. Review the plans and usage
settings in your own accounts before enabling recurring work. Avoid assuming
a trial will cover an indefinite running pipeline.

Follow the [Fivetran Snowflake destination guide](https://fivetran.com/docs/destinations/snowflake/setup-guide)
to provision a dedicated loader identity, its permissions, and key-pair
authentication. Use a small warehouse with auto-suspend for the learning load.
Configure the destination in Fivetran and run its connection test.

For the examples below, choose database `ENERGY_LEARNING` and warehouse
`ENERGY_LEARNING_WH`, or substitute the actual names everywhere. Keep private
keys outside the repository. A separate dbt identity will need read access to
landed data and permission to create and update its output schemas.

**Done when:** Fivetran's Snowflake destination test succeeds. This proves the
destination connection, not an ingestion pipeline.

## 2. Export three known facility rows

In the local PowerShell session from the earlier lessons, run:

```powershell
@'
import csv
import os
from pathlib import Path
import duckdb

output = Path("warehouse/cloud-lab")
output.mkdir(parents=True, exist_ok=True)
with duckdb.connect(os.environ["DBT_DUCKDB_PATH"], read_only=True) as con:
    result = con.execute("select * from raw.facilities order by facility_id")
    columns = [column[0] for column in result.description]
    rows = result.fetchall()
with (output / "facilities.csv").open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(columns)
    writer.writerows(rows)
print(f"Exported {len(rows)} facilities to {output / 'facilities.csv'}")
'@ | & $py -
```

**Expect:** three rows plus a header. Open the CSV and inspect `facility_id`,
`facility_name`, `region`, `owner_name`, and `updated_at`. These are fictional
facilities. The export stays under the ignored `warehouse/` directory.

## 3. Land the CSV with Fivetran

Use the [S3 connector setup guide](https://fivetran.com/docs/connectors/files/amazon-s3/setup-guide)
for current screen labels and IAM configuration:

1. Upload the CSV to a private learning bucket at `energy-learning/facilities.csv`.
2. Add an S3 connection for your Snowflake destination. Choose schema
   `raw_fivetran` and a table-group name such as `energy_lesson`.
3. Configure IAM role access with the External ID shown by Fivetran.
4. Set base folder `energy-learning`, CSV format, comma delimiter, and headers.
5. Map the matching file to table `facilities`. Preview the match before syncing.
6. Choose **Upsert file using custom primary key**, then select `facility_id`
   when configuring keys. Use failure on malformed input for this exercise.
7. Save, test, and start the initial sync. Wait for completion.

**Done when:** the connection reports success and Snowflake contains the table.

## 4. Verify what was loaded

In a Snowflake worksheet, using your actual database/schema names:

```sql
select count(*) as row_count, count(distinct facility_id) as distinct_facilities
from ENERGY_LEARNING.RAW_FIVETRAN.FACILITIES;

select facility_id, facility_name, region, owner_name, updated_at
from ENERGY_LEARNING.RAW_FIVETRAN.FACILITIES
order by facility_id;
```

**Expect:** both counts are **3**, and business fields match the exported CSV.
Inspect the actual column types and any connector metadata columns. Keep
`updated_at` as the source's business-update timestamp; do not silently replace
it with the connector's sync time.

**Checkpoint A:** "I can follow a file from S3 through a successful managed sync
and verify its business keys and values in Snowflake."

## 5. Create an isolated Snowflake dbt environment

Create a learning branch before editing project files:

```powershell
git switch -c codex/learn-fivetran-snowflake
```

If resuming that branch, switch without `-c`. Keep the DuckDB environment intact;
make the cloud environment outside the repository:

```powershell
$snowflakeEnv = Join-Path $env:USERPROFILE '.venvs/dbt-energy-snowflake'
python -m venv $snowflakeEnv
$sfPy = Join-Path $snowflakeEnv 'Scripts/python.exe'
$sfDbt = Join-Path $snowflakeEnv 'Scripts/dbt.exe'
& $sfPy -m pip install 'dbt-core==1.11.15' 'dbt-snowflake==1.11.6'
$cloudProfiles = Join-Path $env:USERPROFILE '.dbt-energy-learning'
New-Item -ItemType Directory -Force $cloudProfiles | Out-Null
```

Use the [dbt Snowflake connection guide](https://docs.getdbt.com/docs/local/connect-data-platform/snowflake-setup)
to configure your dbt user's key-pair authentication. Save the following as
`profiles.yml` inside `$cloudProfiles`, not over the repository's DuckDB profile:

```yaml
dbt_energy_analytics:
  target: snowflake
  outputs:
    snowflake:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      private_key_path: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PATH') }}"
      private_key_passphrase: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE', '') }}"
      database: ENERGY_LEARNING
      warehouse: ENERGY_LEARNING_WH
      schema: analytics
      threads: 1
```

Set those environment variables locally to your actual connection values and
key location. For an encrypted key, supply its passphrase through your local
secret-handling mechanism. Do not commit secrets or private profiles.

```powershell
$env:DBT_TARGET_PATH = 'target/snowflake-learning'
$env:DBT_LOG_PATH = 'logs/snowflake-learning'
& $sfDbt deps --profiles-dir $cloudProfiles --target snowflake
& $sfDbt debug --profiles-dir $cloudProfiles --target snowflake
```

**Done when:** the dbt connection test passes for the intended database, role,
and warehouse. This step still does not establish a complete cloud build.

## 6. Build just the facility staging model

In the existing `raw_energy` declaration in
[sources.yml](../../models/staging/sources.yml), replace the `schema: raw` value
with this expression, retaining its YAML indentation and all other properties:

```yaml
schema: "{{ 'raw_fivetran' if target.type == 'snowflake' else 'raw' }}"
```

This preserves the local raw schema and maps the cloud target to your landing
schema. The other two source tables are declared but have not been loaded in
Snowflake yet, so select only the facility staging model:

```powershell
& $sfDbt compile --profiles-dir $cloudProfiles --target snowflake --select stg_facilities
& $sfDbt build --profiles-dir $cloudProfiles --target snowflake --select stg_facilities
& $sfDbt show --profiles-dir $cloudProfiles --target snowflake --inline "select * from analytics_staging.stg_facilities order by facility_id" --limit 10
```

**Expect:** three staged facilities and their selected tests passing. Investigate
type, casing, permission, or timestamp differences before expanding the selection.

## 7. Demonstrate one source update

1. In the exported CSV, change F001's owner to another fictional name and advance
   `updated_at` to `2026-01-05 00:00:00`, later than its current value.
2. Upload the replacement to the same S3 object key and run another sync.
3. Re-run Step 4's queries. Expect three distinct facilities and the changed owner.
4. Rebuild `stg_facilities` and verify the new metadata appears.
5. If rows duplicate, inspect the connector key and file behavior before continuing.

Do not infer delete behavior from this update exercise. Test deletes separately
if you later need that contract. A dbt snapshot can preserve observed ownership
changes once that portion of the cloud pipeline is built.

## 8. Extend from one table to the full project

This is the porting exercise, not a claim that the checked-in pipeline already
runs on Snowflake:

1. Export `raw.generation` and `raw.facility_load` using the same CSV pattern,
   retaining every source revision and original `ingested_at` value.
2. Add distinct file-to-table mappings for `generation` and `facility_load` in
   `raw_fivetran`. Use `reading_id` as each table's business key.
3. Check raw counts: baseline **864/216**, updated **1,153/289**. Facilities stay 3.
4. Validate UTC timestamps, nulls, numeric types, and key uniqueness after loading.
5. Seed reference factors, compile the full graph, and review adapter-specific
   SQL and the incremental strategy. Validate on Snowflake before calling the
   port complete; installation of an adapter alone is insufficient.
6. Build and reconcile key metrics against the matching DuckDB scenario. Make
   local and cloud checks cover identical source inputs.
7. To test both ownership versions, begin a separate cloud exercise schema with
   baseline fixtures, snapshot them, then ingest updated fixtures and build again.
   Starting with updated metadata cannot recreate the earlier owner.
8. Add cloud-specific validation: the existing Python integration script imports
   DuckDB and therefore does not validate a Snowflake deployment.

## 9. Add orchestration only after the cloud build works

Use [Fivetran's dbt setup guide](https://fivetran.com/docs/transformations/dbt/setup-guide)
to connect the repository through its provided deploy key and configure the
validated branch, project root, destination, and dbt version. This project's
version constraint requires dbt 1.11.x.

First run one manual `dbt build` job. Then configure a schedule that follows
successful source syncs. Check a complete chain: source change, sync completion,
dbt run, passing tests, and updated mart values. Record the Git commit and job
results. Pause the learning schedule when you finish using it.

**Checkpoint B:** after completing the full exercise, "I can demonstrate a
source update passing through managed ingestion, Snowflake, and tested dbt models."

## 10. Replace a fixture with documented public energy data

Choose one region and a small fixed time range from a public source. Record its
license, provenance, grain, units, timezone, revision behavior, and fuel mapping.
Keep public generation data distinct from the synthetic facility meters.

If it requires a custom API connector, follow the
[Fivetran Python Connector SDK guide](https://fivetran.com/docs/connector-sdk/getting-started):
prove retrieval locally, define stable keys, test pagination and checkpointing,
then deploy and validate the destination. This repository does not include that
connector yet.

Document which outputs use measured data and which still use synthetic data or
illustrative factors. Keep the local fixture path available for other learners.

Provider documentation reviewed on 2026-09-23. Cloud account settings and UI
labels can differ; follow the linked provider instructions for account-specific
authentication and permissions.
