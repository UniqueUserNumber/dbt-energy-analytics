select
    facility_id,
    region,
    cast(hour_utc as date) as date_utc,
    count(*) as observed_hours,
    count(production_co2_kg_per_mwh) as matched_grid_hours,
    sum(load_mwh) as load_mwh,
    -- Do not publish a partial emissions total when any grid hour is missing.
    case when count(production_co2_kg_per_mwh) = count(*) then
        sum(estimated_production_proxy_co2_kg)
    end as estimated_production_proxy_co2_kg,
    case when count(production_co2_kg_per_mwh) = count(*) then
        sum(estimated_production_proxy_co2_kg) / nullif(sum(load_mwh), 0)
    end as load_weighted_co2_kg_per_mwh,
    case when count(carbon_free_share) = count(*) then
        sum(load_mwh * carbon_free_share) / nullif(sum(load_mwh), 0)
    end as load_weighted_carbon_free_share
from {{ ref('fct_facility_hourly') }}
group by facility_id, region, cast(hour_utc as date)
