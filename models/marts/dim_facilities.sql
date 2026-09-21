select facility_id, facility_name, region, owner_name, updated_at
from {{ ref('facility_history') }}
where dbt_valid_to is null
