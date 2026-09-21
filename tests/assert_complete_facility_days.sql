select * from {{ ref('mart_facility_daily') }}
where observed_hours <> 24 or matched_grid_hours <> observed_hours
