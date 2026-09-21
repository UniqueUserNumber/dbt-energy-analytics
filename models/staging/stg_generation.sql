select
    reading_id,
    upper(trim(region)) as region,
    cast(hour_utc as timestamp) as hour_utc,
    lower(trim(fuel_type)) as fuel_type,
    cast(generation_mwh as double) as generation_mwh,
    cast(ingested_at as timestamp) as ingested_at
from {{ source('raw_energy', 'generation') }}
