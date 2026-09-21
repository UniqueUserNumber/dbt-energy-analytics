# Contributing

Fork the repository and follow the README quickstart. Use a branch for your
change. Keep the synthetic path available without credentials or paid services.

Before opening a pull request:

1. Explain the use case, model grain, units, and assumptions.
2. Add or update model and column descriptions.
3. Run `dbt deps --profiles-dir .` and `python scripts/verify_demo.py` in your environment.
4. Run the baseline loader, `dbt build --profiles-dir .`, and `dbt docs generate --profiles-dir .`.
5. For real datasets, include provenance and required license attribution.

Keep generated warehouses, credentials, virtual environments, logs, and dbt
artifacts out of commits. `profiles.yml` is tracked because it is a credential-free
DuckDB profile; use a separate private profile for remote databases.

Useful starter contributions: a region/day mart, calendar-spine completeness
checks, unit tests for clean-window edge cases, a public-data adapter, or a
documented warehouse port. Open an issue with reproducible steps for defects.
