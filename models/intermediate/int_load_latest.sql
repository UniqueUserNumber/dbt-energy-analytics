select reading_id, facility_id, hour_utc, load_mwh, ingested_at
from {{ ref('stg_facility_load') }}
qualify row_number() over (
    partition by facility_id, hour_utc
    order by ingested_at desc, reading_id desc
) = 1
