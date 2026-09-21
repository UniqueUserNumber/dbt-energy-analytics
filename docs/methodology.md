# Methodology and data contracts

## Scope

This is an original synthetic demonstration of analytics engineering for energy.
Generation, facilities, loads, ownership changes, and fixed emission factors are
invented. ISONE and PJM are familiar region labels, not evidence of measured data.
The generator in `scripts/load_demo.py` is the source of every fixture.

The dbt portion starts after ingestion. DuckDB stores the raw data, views, tables,
and snapshots locally. Models expose their dependencies in dbt's graph.

## Units and grain

- Generation is **MWh per one-hour interval**, by region and fuel.
- Meter data arrives as **kWh per one-hour interval** and is divided by 1,000.
- All timestamps are naive SQL timestamps with an explicit **UTC contract**.
  `hour_utc` is the inclusive interval start; the end is one hour later.
- Each generation revision has an ingestion timestamp and unique reading ID.
- The latest-generation view has one row per region/hour/fuel.
- The grid fact has one row per region/hour; the facility fact has one per
  facility/hour; the daily mart has one per facility/UTC date.

Raw revisions are retained. Latest ingestion time wins. Reading ID breaks ties
deterministically; a production connector must define authoritative revision
ordering rather than relying on arbitrary identifiers.

## Formulas

For each region and hour:

```text
estimated direct CO2 (kg) = sum(generation MWh by fuel * demo factor kg/MWh)
production intensity (kg/MWh) = estimated direct CO2 / total generation MWh
carbon-free share = (nuclear + hydro + wind + solar MWh) / total generation MWh
facility emissions proxy (kg) = facility load MWh * production intensity
daily load-weighted intensity = sum(hourly facility proxy kg) / sum(hourly load MWh)
```

The daily intensity must be load weighted. An unweighted average of hourly
intensities answers a different question when facility load varies by hour.
The model uses `nullif` to avoid dividing by zero, and data tests flag nulls.

The factors (gas 400, coal 950, other included fuels 0 kg CO2/MWh) are illustrative
constants. They exclude methane, other greenhouse gases, upstream supply chains,
and lifecycle emissions. The outputs are **CO2, not CO2e**. Zero direct emissions
does not establish zero lifecycle impact.

## Interpretation limits

Production intensity describes the generation mix inside a region. It does not
trace imports and exports or determine the electricity delivered to a consumer.
Applying it to facility load is explicitly a **production-based proxy**, not a
validated consumption-based or market-based Scope 2 inventory.

The clean-window model compares a hypothetical 1 MW workload lasting three
consecutive hours (3 MWh). It finds the lowest average-intensity window within a
single UTC date, breaking ties by earliest start, and compares it to 18:00 UTC.
It requires three consecutive hours and never joins across a gap or midnight.
It uses observed synthetic values, so this is retrospective, not a forecast.

Its output is an illustrative difference in average-factor estimates. It does
not measure avoided emissions: that would require a suitable marginal-emissions
method and assumptions about the grid's response. It also excludes deadlines,
prices, dispatch constraints, and battery losses.

Carbon-free generation share is not hourly contractual matching. No RECs, PPAs,
residual mix, or double-counting rules are modeled.

## Missing data is visible

Unknown fuels stay in the left join and produce null emissions totals. A
relationship test detects missing factors. Unmatched load intervals remain in
the facility fact, and coverage tests reject them. A daily emissions total is
null when any observed interval lacks a factor.

The fixture contract requires all six fuels, including explicit zero readings,
and 24 distinct UTC hours for every represented day. A production feed may use
different completeness rules. These tests do not detect an entirely absent
facility-day or region-day; a production connector should join an expected
calendar/asset spine. Do not replace missing readings with zero.

Historical fixture dates are intentional. Wall-clock freshness checks would
always fail here; add source freshness thresholds when a real feed is connected.

## Incremental assumptions

The grid fact selects region-hours whose latest `ingested_at` is at least the
target's highest ingestion timestamp. It replaces those keys with `delete+insert`.
An old event hour is still eligible when its correction arrives with a new
ingestion time. Reprocessing equal timestamps makes batch retries safe.

This requires ingestion timestamps assigned monotonically by the landing
process. Backdated ingestion times, hard source deletions, and changes to factors
or calculation logic need a full refresh or an explicit backfill design. Factors
are fixed here; a real factor history needs versions and effective dates.
The integration suite compares incremental results with a full rebuild.

The upstream deduplication/aggregation views scan source history. At scale,
identify changed region-hours first, then read every fuel for those hours;
filtering individual fuels before aggregation would produce incomplete totals.

Facility facts and daily marts rebuild entirely. That is intentional for the
small demo and ensures corrected grid intensities reach all affected loads.

## History

`facility_history` snapshots metadata using the source `updated_at` timestamp.
It preserves only changes observed at build time, not unobserved intermediate
states. A full refresh of models does not recreate snapshot history.

The current facility dimension is used for reporting. Ownership changes are
demonstrated separately in the snapshot; region is fixed in the fixtures. If
facilities can change region, add an effective-date join for hourly attribution.

## Real-data extension

The next extension is a connector for documented public generation and emissions
data. Start with one small, fixed historical slice and map its fields to the
source contracts above. A connector is an open learning task, not an implemented
feature.

Before adding a dataset, record its release, source URL, license and required
attribution, units, timezone, factor methodology, and geographic scope. Preserve
published measured emissions when available rather than silently replacing them
with the demo constants. Keep original synthetic inputs as an offline test path.
