# Lesson 8 — Documentation, lineage, and CI

[Course home](../learning_path.md) · [Next: build your model](09_build_a_model.md)

**Goal:** make the project understandable and verify it beyond a successful run.

## 1. Generate the catalog and lineage

```powershell
& $dbt docs generate --profiles-dir .
```

**Expect:** `manifest.json`, `catalog.json`, and the documentation app under
`target/learning`. The manifest describes dbt resources and dependencies; the
catalog adds database metadata. These artifacts are ignored by Git.

Start the local documentation server:

```powershell
& $dbt docs serve --profiles-dir . --port 8080
```

Open `http://localhost:8080`. This command stays running; stop it with Ctrl+C
before continuing in the same terminal.

## 2. Explore with a purpose

1. Find `mart_facility_daily` and read its grain and column descriptions.
2. Open its lineage graph and follow upstream references to the raw sources.
3. Find where the emission-factor seed enters the graph.
4. Find `facility_history` and the current dimension.
5. Inspect the generated SQL for a model that calls a macro.

Compare the documentation with [marts/schema.yml](../../models/marts/schema.yml).
The descriptions are maintained beside the models, so they can change in the
same commit as the SQL.

## 3. Run the integration checks

```powershell
& $py scripts/verify_demo.py
```

**Expect:** `All integration checks passed.` The script creates a temporary
warehouse. It checks known arithmetic, late corrections, ownership history,
idempotent reruns, and agreement between incremental and full-refresh results.
It deliberately runs two failing data tests and treats those failures as expected.
Your learning database retains its data.

Read [verify_demo.py](../../scripts/verify_demo.py). Explain why checking only
row counts would miss a correction that never reached an existing row. Also
find the small floating-point tolerance used when comparing aggregate results.

## 4. Read the GitHub workflow

Open [dbt.yml](../../.github/workflows/dbt.yml). Trace these steps:

1. Check out the committed project in a clean runner.
2. Install Python dependencies and the dbt package.
3. Run integration checks in an isolated warehouse.
4. Load a fresh baseline and run `dbt build`.
5. Generate documentation.

The matrix covers Linux/Python 3.12 and Windows/Python 3.13. No cloud account
secrets are required for these synthetic-data checks.

## 5. Inspect an actual workflow run

Open the repository's [Actions page](https://github.com/UniqueUserNumber/dbt-energy-analytics/actions).
Choose a run and inspect its commit, both jobs, and one build log. For your own
changes, check the run for your exact commit rather than an older green badge.

Local success proves the code works in your environment. CI helps show another
person can reproduce it from the committed files and declared dependencies.

**Checkpoint:** "I can find model definitions and lineage, explain our
integration checks, and identify which commit the CI result verifies."

**Exercise:** name one thing these checks establish and one thing they do not
establish, such as production-scale performance or cloud connector behavior.
