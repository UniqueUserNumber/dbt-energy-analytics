# Lesson 1 — Environment and first connection

[Course home](../learning_path.md) · [Next: ingestion](02_ingestion.md)

**Goal:** connect dbt to an isolated local warehouse. If you already know Python
environments and database connections, focus on how dbt expresses them.

## 1. Open the repository

If the repository is already on your computer, open PowerShell in its root.
For a first clone, run these commands from a folder where you keep projects:

```powershell
git clone https://github.com/UniqueUserNumber/dbt-energy-analytics.git
Set-Location dbt-energy-analytics
```

Do not clone again inside an existing checkout. Check your location:

```powershell
Get-Location
Test-Path dbt_project.yml
git status --short
python --version
```

**Expect:** `True` for the project file and Python 3.12 or 3.13. Keep any local
changes; do not reset the repository to follow this guide.

## 2. Prepare the Python environment

If `.venv` already exists for this project, reuse it. Otherwise:

```powershell
python -m venv .venv
```

Set the executable paths, then install the pinned dependencies:

```powershell
$projectRoot = (Get-Location).Path
$py = Join-Path $projectRoot '.venv/Scripts/python.exe'
$dbt = Join-Path $projectRoot '.venv/Scripts/dbt.exe'
& $py -m pip install -r requirements.txt
& $dbt --version
```

**Expect:** dbt Core 1.11.15 and DuckDB adapter 1.11.0. DuckDB is the database
engine; the adapter lets dbt create and query relations in that engine.

## 3. Pick a fresh learning warehouse

```powershell
New-Item -ItemType Directory -Force warehouse | Out-Null
$env:DBT_DUCKDB_PATH = Join-Path $projectRoot 'warehouse/learning.duckdb'
$env:DBT_TARGET_PATH = 'target/learning'
$env:DBT_LOG_PATH = 'logs/learning'
$env:DBT_SEND_ANONYMOUS_USAGE_STATS = 'false'
Test-Path $env:DBT_DUCKDB_PATH
```

**Expect:** `False` on your first pass. If the file exists and you are starting
over, choose a new `learning-*.duckdb` filename. If you are resuming, keep the
existing file and return to your current lesson.

The original demo uses `warehouse/energy.duckdb`; these lessons use your selected
path. Generated files are already ignored by Git.

## 4. Read the two configuration files

Open [dbt_project.yml](../../dbt_project.yml) and [profiles.yml](../../profiles.yml).
Find these connections:

1. The project `profile` matches the top-level name in `profiles.yml`.
2. The profile selects the `dev` target and `duckdb` adapter.
3. The profile reads `DBT_DUCKDB_PATH` from the environment.
4. Staging defaults to views and marts to tables. A model can override its
   materialization with its own `config()`.
5. The default schema is `analytics`. dbt appends custom schema names, producing
   `analytics_staging` and `analytics_marts`.

This is the dbt equivalent of connection configuration and per-job output settings.

## 5. Install the dbt package and test the connection

```powershell
& $dbt deps --profiles-dir .
& $dbt debug --profiles-dir .
```

**Expect:** `dbt_utils` 1.4.1 installs and the connection succeeds. `pip install`
installed Python software; `dbt deps` installed SQL/Jinja macros from
[packages.yml](../../packages.yml).

No energy data is loaded yet. A successful connection completes this lesson.

**Checkpoint:** "I can identify the project configuration, the database
connection configuration, and how I isolate a learning database."

**Answer aloud:** What changes to connect the project to a different warehouse?
Which parts also require adapter-specific validation?
