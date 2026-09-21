-- A strict demo contract: every represented region/day has 24 distinct UTC hours.
select region, cast(hour_utc as date) as date_utc
from {{ ref('fct_grid_hourly') }}
group by region, cast(hour_utc as date)
having count(distinct hour_utc) <> 24
