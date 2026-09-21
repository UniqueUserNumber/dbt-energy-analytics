with hourly as (
    select facility_id, cast(hour_utc as date) as date_utc,
        sum(estimated_production_proxy_co2_kg) as co2_kg
    from {{ ref('fct_facility_hourly') }}
    group by facility_id, cast(hour_utc as date)
)
select d.* from {{ ref('mart_facility_daily') }} d
join hourly h using (facility_id, date_utc)
where abs(d.estimated_production_proxy_co2_kg - h.co2_kg) > 0.000001
