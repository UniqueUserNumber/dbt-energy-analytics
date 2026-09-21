-- Source ingestion timestamps are monotonic. Break ties deterministically.
select reading_id, region, hour_utc, fuel_type, generation_mwh, ingested_at
from {{ ref('stg_generation') }}
qualify row_number() over (
    partition by region, hour_utc, fuel_type
    order by ingested_at desc, reading_id desc
) = 1
