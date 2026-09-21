-- Rebuild this small downstream mart so corrected grid factors propagate.
-- Current facility region is intentionally used; see docs/methodology.md.
select
    {{ dbt_utils.generate_surrogate_key(['l.facility_id', 'l.hour_utc']) }} as facility_hour_id,
    l.facility_id,
    f.region,
    l.hour_utc,
    l.load_mwh,
    g.production_co2_kg_per_mwh,
    g.carbon_free_share,
    l.load_mwh * g.production_co2_kg_per_mwh as estimated_production_proxy_co2_kg
from {{ ref('int_load_latest') }} l
left join {{ ref('dim_facilities') }} f using (facility_id)
left join {{ ref('fct_grid_hourly') }} g
    on f.region = g.region and l.hour_utc = g.hour_utc
