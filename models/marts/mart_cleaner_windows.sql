-- Retrospective comparison: a 3 MWh job at constant 1 MW for three hours.
-- Each candidate must contain three consecutive hours within one UTC day.
with candidates as (
    select
        region,
        cast(hour_utc as date) as date_utc,
        hour_utc as start_hour_utc,
        count(*) over w as window_hours,
        max(hour_utc) over w as end_hour_utc,
        avg(production_co2_kg_per_mwh) over w as mean_co2_kg_per_mwh,
        count(production_co2_kg_per_mwh) over w as matched_hours
    from {{ ref('fct_grid_hourly') }}
    window w as (
        partition by region, cast(hour_utc as date)
        order by hour_utc rows between current row and 2 following
    )
), complete as (
    select * from candidates
    where window_hours = 3 and matched_hours = 3
      and end_hour_utc = start_hour_utc + interval '2 hours'
), ranked as (
    select *, row_number() over (
        partition by region, date_utc
        order by mean_co2_kg_per_mwh, start_hour_utc
    ) as window_rank
    from complete
), baseline as (
    select region, date_utc, mean_co2_kg_per_mwh as baseline_co2_kg_per_mwh
    from complete where extract(hour from start_hour_utc) = 18
)
select
    r.region,
    r.date_utc,
    r.start_hour_utc as best_start_hour_utc,
    r.mean_co2_kg_per_mwh as best_co2_kg_per_mwh,
    b.baseline_co2_kg_per_mwh,
    3.0 as job_energy_mwh,
    (b.baseline_co2_kg_per_mwh - r.mean_co2_kg_per_mwh) * 3.0
        as illustrative_co2_difference_kg
from ranked r
left join baseline b using (region, date_utc)
where r.window_rank = 1
