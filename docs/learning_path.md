# Learn the project, step by step

Work through one lesson at a time. Each connects a dbt feature to a familiar
data-engineering job, gives you commands to run, and ends with a checkpoint.
Predict the result before running a command; explain it afterward.

**Start with [Lesson 1: set up your learning environment](lessons/01_setup.md).**
You do not need Fivetran, Snowflake, AWS, or a credit card for Lessons 1-9.
Commands use Windows PowerShell and Python 3.12 or 3.13.

## Your route through the project

1. [Environment and first connection](lessons/01_setup.md) — Python environment,
   project configuration, a separate learning database, and `dbt debug`.
2. [Ingestion and raw data](lessons/02_ingestion.md) — load fixtures, inspect
   their grain, and distinguish ingestion from transformation.
3. [Seeds, staging, macros, and dependencies](lessons/03_models.md) — compile SQL,
   use `source()` and `ref()`, and inspect dbt's execution order.
4. [Trace the business calculations](lessons/04_metrics.md) — follow an hour from
   fuel mix to facility emissions and interpret the cleaner-window result.
5. [Data tests and a controlled failure](lessons/05_tests.md) — break a lookup,
   inspect the failure, and restore it.
6. [Incremental models and late corrections](lessons/06_incremental.md) — process
   an updated batch, replace an old hour, and prove a rerun is safe.
7. [Snapshots and ownership history](lessons/07_snapshots.md) — inspect SCD2
   versions and understand what snapshots preserve.
8. [Documentation, lineage, and CI](lessons/08_docs_ci.md) — explore generated
   documentation and understand what GitHub verifies.
9. [Build your own regional mart](lessons/09_build_a_model.md) — add a model,
   describe it, test it, and inspect the results.
10. [Fivetran and Snowflake extension](lessons/10_fivetran_snowflake.md) — learn
    managed ingestion with one table, then plan a complete cloud port.

Allow roughly 20-45 minutes per local lesson, and more time for Lesson 9.
Lesson 10 is an account-dependent extension; its integrations are not already
implemented in this repository.

## How to use the commands

Run commands from the repository root, the folder containing `dbt_project.yml`.
Lesson 1 defines `$py` and `$dbt` as executables in your virtual environment.
The PowerShell `&` operator runs an executable whose path is in a variable.

SQL previews use `dbt show --inline`. They inspect existing relations; they do
not build missing upstream models. Omit a trailing semicolon inside an inline
query. Build preceding models before inspecting them.
[dbt show reference](https://docs.getdbt.com/reference/commands/show)

Stop when a normal command fails and repair it before continuing. Lesson 5
labels the deliberately failing test and gives immediate recovery commands.

## Resume after closing PowerShell

Open PowerShell in this repository and restore your session settings:

```powershell
$projectRoot = (Get-Location).Path
$py = Join-Path $projectRoot '.venv/Scripts/python.exe'
$dbt = Join-Path $projectRoot '.venv/Scripts/dbt.exe'
$env:DBT_DUCKDB_PATH = Join-Path $projectRoot 'warehouse/learning.duckdb'
$env:DBT_TARGET_PATH = 'target/learning'
$env:DBT_LOG_PATH = 'logs/learning'
$env:DBT_SEND_ANONYMOUS_USAGE_STATS = 'false'
```

If you chose a different `learning-*.duckdb` filename, use that same name here.
These settings apply to this terminal and its child processes, not other terminals.

After Lesson 6, keep using the updated data. The loader rejects loading baseline
data over an updated database. To restart, select a new filename such as
`warehouse/learning-02.duckdb` and start from Lesson 2. Keep its name beginning
with `learning`; the failure exercise checks this.

## Keep a record of what you learned

Use your own notes outside the repository. For each lesson, record:

- The command and result you observed.
- The grain and units of the model you inspected.
- A change you predicted correctly, or a mistake you corrected.
- Your answer to the checkpoint question.

Checkpoints are learning goals, not claims to use before doing the work.
Completing the local lessons establishes hands-on dbt Core project experience.
The cloud chapter becomes hands-on Fivetran/Snowflake experience after you
configure and verify that integration yourself.

## Troubleshooting

- **`$dbt` is empty or not recognized:** restore the session settings above.
- **Project or profile not found:** return to the repository root and retain
  `--profiles-dir .` on dbt commands.
- **Package missing:** run `& $dbt deps --profiles-dir .`.
- **Raw table missing:** run Lesson 2's loader against the same database path.
- **Model table missing:** finish Lesson 3's full `dbt build`.
- **DuckDB file locked:** close another client using the file and retry. Avoid
  simultaneous dbt builds against one local file.
- **Wrong counts:** check `$env:DBT_DUCKDB_PATH` and your scenario. Baseline has
  144 grid hours; updated has 192.
- **Cloud step blocked:** record the exact step and error; the local course
  remains usable while account or permissions setup is resolved.

Read [methodology and data contracts](methodology.md) alongside the lessons.

The local walkthrough and Lesson 9's example, failure, and recovery were checked
on Windows with Python 3.13.7 and dbt Core 1.11.15. The cloud chapter's CSV export
was checked locally; account setup and Snowflake execution remain exercises to
validate in your own cloud environment.
