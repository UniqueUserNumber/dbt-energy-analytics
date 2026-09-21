select
    g.region,
    g.hour_utc,
    sum(g.generation_mwh) as generation_mwh,
    -- LEFT JOIN preserves unknown fuels so tests expose them.
    case when count(f.fuel_type) = count(*) then
        sum(g.generation_mwh * f.co2_kg_per_mwh)
    end as estimated_co2_kg,
    case when count(f.fuel_type) = count(*) then
        sum(case when f.is_carbon_free then g.generation_mwh else 0 end)
    end as carbon_free_generation_mwh,
    count(*) as fuel_count,
    max(g.ingested_at) as ingested_at
from {{ ref('int_generation_latest') }} g
left join {{ ref('demo_emission_factors') }} f using (fuel_type)
group by g.region, g.hour_utc
