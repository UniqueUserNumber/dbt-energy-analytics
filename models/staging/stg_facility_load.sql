select
    reading_id,
    facility_id,
    cast(hour_utc as timestamp) as hour_utc,
    {{ kwh_to_mwh('cast(load_kwh as double)') }} as load_mwh,
    cast(ingested_at as timestamp) as ingested_at
from {{ source('raw_energy', 'facility_load') }}
