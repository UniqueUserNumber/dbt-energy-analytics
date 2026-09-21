-- Fixtures publish all six fuels, including explicit zero-generation rows.
select * from {{ ref('fct_grid_hourly') }}
where fuel_count <> 6 or generation_mwh <= 0
