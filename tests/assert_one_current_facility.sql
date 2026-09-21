select facility_id from {{ ref('facility_history') }}
group by facility_id
having sum(case when dbt_valid_to is null then 1 else 0 end) <> 1
