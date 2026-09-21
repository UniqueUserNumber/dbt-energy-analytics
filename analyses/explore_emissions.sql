-- Compile with dbt compile --profiles-dir . and inspect target/compiled/.
select f.facility_name, d.date_utc, d.load_mwh,
    round(d.estimated_production_proxy_co2_kg, 2) as estimated_co2_kg,
    round(d.load_weighted_co2_kg_per_mwh, 2) as weighted_intensity
from {{ ref('mart_facility_daily') }} d
join {{ ref('dim_facilities') }} f using (facility_id)
order by d.date_utc, f.facility_name
