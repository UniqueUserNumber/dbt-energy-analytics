# Make this project your own

This repository is a working starter. Build confidence by changing one piece,
predicting its effect, running dbt, and explaining the result in your own words.

## 1. Trace one number

Run the baseline, then find ISONE at 2026-01-01 18:00 UTC. Its generation is
1,315 MWh and estimated direct emissions are 295,500 kg CO2. The intensity is
295,500 / 1,315 kg/MWh. F001 consumes 1.1 MWh at that hour.

Follow the number through raw generation, staging, latest revisions, hourly
aggregation, the grid fact, and facility estimates. Use dbt docs for the graph.
Run `dbt compile --profiles-dir .` and inspect the generated SQL in `target/compiled`.

Checkpoint: explain what `source()` and `ref()` add to a collection of SQL files.

## 2. Add one useful mart

Build `mart_region_daily.sql` with daily generation and a generation-weighted
daily intensity. Add its grain, column descriptions, and a test that reconciles
daily emissions to hourly totals. Predict why `avg(hourly_intensity)` is wrong
when generation changes from hour to hour.

Checkpoint: explain the difference between generation weighting and load weighting.

## 3. Break a data contract

Use a separate demo warehouse. Introduce an unknown fuel or remove a grid hour,
then run the relevant tests. Explain why missing values should not become zero.
The integration suite already demonstrates two failures; add a missing entire
day and build a calendar-spine completeness test to catch it.

Checkpoint: name a defect your tests catch and one they currently miss.

## 4. Study corrections and history

Run the updated scenario. Inspect the corrected old grid hour and F001's two
ownership versions. Re-run it and confirm no duplicates appear. Read
`scripts/verify_demo.py` for checks against a full rebuild.

Checkpoint: explain why the incremental model filters by ingestion time, not
event time, and why snapshots and incremental facts solve different problems.

## 5. Connect a documented public source

Add a connector for one small, fixed historical slice from a public dataset.
Keep it opt-in so the synthetic quickstart remains dependable. Document licensing,
lineage, UTC conversion, geographic mapping, null handling, and revision behavior.
Add tests against representative input fixtures. Avoid presenting a real-data
connector as complete until you have actually verified it.

Checkpoint: explain the limitations of generation-based versus consumption-based
factors and why load shifting needs more than an average emissions estimate.

## 6. Extend the delivery layer

Choose a dashboard, a Snowflake port, or a scheduled ingestion job. For Snowflake,
review adapter-specific SQL and incremental strategies, isolate environments,
keep credentials outside Git, and validate the results against the local demo.
Local dbt Core experience does not imply dbt Cloud deployment experience.

## Present it honestly

After running and explaining the starter: "I'm building a public dbt energy
analytics project with hourly emissions estimates, data tests, incremental
corrections, and snapshots. I can walk through how the models work."

After implementing an extension, describe exactly what you added, how you tested
it, and the tradeoffs. Personal project work should be identified as personal
project work; it does not establish production dbt ownership.
