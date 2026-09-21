select * from {{ ref('fct_facility_hourly') }}
where region is null or production_co2_kg_per_mwh is null
