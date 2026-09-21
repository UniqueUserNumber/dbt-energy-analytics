"""Print the main dbt outputs without installing a separate database client."""

import duckdb

from load_demo import database_path


def show(title, sql):
    with duckdb.connect(str(database_path()), read_only=True) as con:
        result = con.execute(sql)
        print(f"\n{title}\n" + " | ".join(column[0] for column in result.description))
        for row in result.fetchall():
            print(" | ".join(str(value) for value in row))


if __name__ == "__main__":
    show("Synthetic facility emissions estimates (production-based proxy)", """
        select facility_id, date_utc, round(load_mwh, 2) as mwh,
            round(estimated_production_proxy_co2_kg, 2) as estimated_co2_kg,
            round(load_weighted_co2_kg_per_mwh, 2) as kg_per_mwh
        from analytics_marts.mart_facility_daily order by date_utc, facility_id
    """)
    show("Retrospective 3 MWh job comparison (not measured avoided emissions)", """
        select region, date_utc, best_start_hour_utc,
            round(illustrative_co2_difference_kg, 2) as difference_vs_18utc_kg
        from analytics_marts.mart_cleaner_windows order by date_utc, region
    """)
