select
    facility_id,
    trim(facility_name) as facility_name,
    upper(trim(region)) as region,
    trim(owner_name) as owner_name,
    cast(updated_at as timestamp) as updated_at
from {{ source('raw_energy', 'facilities') }}
