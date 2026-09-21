{{ config(
    materialized='incremental',
    unique_key='grid_hour_id',
    incremental_strategy='delete+insert',
    on_schema_change='fail'
) }}

select
    {{ dbt_utils.generate_surrogate_key(['region', 'hour_utc']) }} as grid_hour_id,
    region,
    hour_utc,
    generation_mwh,
    estimated_co2_kg,
    carbon_free_generation_mwh,
    estimated_co2_kg / nullif(generation_mwh, 0) as production_co2_kg_per_mwh,
    carbon_free_generation_mwh / nullif(generation_mwh, 0) as carbon_free_share,
    fuel_count,
    ingested_at
from {{ ref('int_grid_hourly') }}
{% if is_incremental() %}
-- Ingestion time catches corrections to old event hours. >= safely replays ties.
where ingested_at >= (
    select coalesce(max(ingested_at), timestamp '1900-01-01') from {{ this }}
)
{% endif %}
