# Analytics SQL layer

This directory defines the PostgreSQL analytical layer shared by Power BI and
future application APIs. It does not change the operational ownership of
`core` or `people`.

## Scope of v1

Included:

- Monthly active headcount.
- Partners, using category name `Socio`.
- Organisational breakdown by society, office, department and category.
- Gender, age and tenure.
- Joins, including organic and inorganic joins.
- Total exits and rotation-eligible exits.
- High-level voluntary and dismissal counts needed by the Rotation page.
- Salary, bonus, evaluation and stored attrition probability.
- Satisfaction from the existing aggregated survey source.
- Fiscal and calendar periods.

Explicitly excluded:

- The detailed Exit Reasons page and its taxonomy.
- Equity-partner classification, because no authoritative field exists.
- A separate area hierarchy, because the current source only models
  department.
- Final age, tenure, salary and performer bands. The numerical inputs are
  exposed so the approved bands can be added without rebuilding the facts.

## Confirmed business rules

- The fiscal year runs from 1 September through 31 August of the following
  calendar year and is labelled by its ending year. For example,
  1 September 2025 through 31 August 2026 is `FY2026`.

## Business assumptions to confirm

1. Analytics history starts on 1 January 2019.
2. A person is active on a snapshot date when:
   `joined_at <= snapshot_date AND (left_at IS NULL OR left_at > snapshot_date)`.
3. Monthly turnover is:
   `rotation-eligible exits / ((opening headcount + closing headcount) / 2)`.
4. Voluntary and dismissal metrics only count records whose
   `people.exit.bol_rotation = 1`.
5. Organisational attribution is resolved from `core.employee_hst` using the
   latest valid `start_at` and `id`. If no valid row exists, the current
   values in `core.employee` are used and `assignment_source = 'employee'`.

All remaining assumptions must be reconciled with the Power BI measures before
replacing the existing semantic model.

## Objects

| Object | Grain | Purpose |
|---|---|---|
| `analytics.configuration` | One row | History and fiscal configuration |
| `analytics.dim_date` | Day | Calendar and fiscal dimension |
| `analytics.v_employee_assignment_intervals` | Employee assignment | Auditable source intervals |
| `analytics.v_employee_movements` | Employee event | Base join and exit events |
| `analytics.mv_employee_monthly_snapshot` | Employee/month | Flexible workforce fact |
| `analytics.mv_employee_movements` | Employee/event | Enriched movement fact |
| `analytics.v_bi_employee_categories` | Category | Categories included in BI employee metrics |
| `analytics.v_bi_employee_monthly_snapshot` | Employee/month | BI-scoped workforce fact |
| `analytics.v_bi_employee_movements` | Employee/event | BI-scoped movement fact |
| `analytics.v_workforce_monthly` | Month/full dimensional grain | Additive workforce metrics |
| `analytics.v_movements_monthly` | Month/full dimensional grain | Join and exit metrics |
| `analytics.v_turnover_monthly` | Month/full dimensional grain | Turnover components and rates |
| `analytics.v_executive_monthly` | Month/company | Executive cards and trends |
| `analytics.v_satisfaction_summary` | Survey/dimensional grain | Satisfaction metric |
| `analytics.v_data_quality_checks` | Check | Operational quality warnings |
| `analytics.v_powerbi_dataset_all` | Employee/fiscal year | Legacy PBIX compatibility dataset |
| `analytics.v_powerbi_attrition_predictions` | Employee/fiscal year | Stored attrition predictions |
| `analytics.v_powerbi_probabilities_2024/2025` | Employee/prediction set | Legacy prediction table contracts |
| `analytics.v_powerbi_clustering_salidas` | Empty typed contract | Exit-reason page placeholder |

## Deployment order

Run with a database owner or migration role. `PSQL_DATABASE_URL` must be a
native `postgresql://` URI, not SQLAlchemy's
`postgresql+asyncpg://` URI:

```bash
psql "$PSQL_DATABASE_URL" -f db/analytics/001_create_analytics_foundation.sql
psql "$PSQL_DATABASE_URL" -f db/analytics/002_create_source_indexes.sql
psql "$PSQL_DATABASE_URL" -f db/analytics/003_create_base_views.sql
psql "$PSQL_DATABASE_URL" -f db/analytics/004_create_materialized_views.sql
psql "$PSQL_DATABASE_URL" -f db/analytics/005_create_reporting_views.sql
psql "$PSQL_DATABASE_URL" -f db/analytics/006_create_powerbi_compatibility_views.sql
psql "$PSQL_DATABASE_URL" -f db/analytics/validate_analytics.sql
```

The materialized views are created populated. Subsequent refreshes use:

```bash
psql "$PSQL_DATABASE_URL" -f db/analytics/refresh_materialized_views.sql
```

Schedule the refresh before the Power BI semantic model refresh.

## Power BI consumption

Recommended imported objects:

- `analytics.dim_date`
- `analytics.v_executive_monthly`
- `analytics.v_workforce_monthly`
- `analytics.v_movements_monthly`
- `analytics.v_turnover_monthly`
- `analytics.v_satisfaction_summary`

Use `analytics.v_bi_employee_monthly_snapshot` and
`analytics.v_bi_employee_movements` when a visual needs employee-grain
segmentation such as custom age, tenure, salary or performer bands. Do not
connect Power BI directly to the unfiltered materialized views.

All employee BI objects, including the `v_powerbi_*` compatibility objects,
use the canonical population: Junior, Senior, Gerente/Manager, Director, Socio
and Estructura. The category is resolved at the snapshot, movement or
prediction date, so historical headcount, joins, exits, turnover and
predictions use the employee category that was valid at that time.

Power BI should connect with a read-only role that has `USAGE` on
`analytics` and `SELECT` only on the approved analytical objects.

The legacy report source-switch, Power Query expressions and reproducible PBIX
copy builder are documented in
[`db/analytics/powerbi/README.md`](powerbi/README.md).

## Refresh behaviour

The current month is materialized using `current_date`; closed months use
their calendar month end. Therefore the materialized views must be refreshed
to advance the current snapshot and ingest new source data.

Regular refresh can be used during initial deployment. The supplied operational
script uses concurrent refresh so Power BI can continue reading during refresh.

## Known source quality conditions

The current database contains overlapping open-ended
`core.employee_hst` rows for some employees. The analytics queries resolve
them deterministically with `ORDER BY start_at DESC, id DESC LIMIT 1`, but the
source condition should eventually be corrected.

Some employee exits do not have a matching `people.exit` row. Total exit
counts use `core.employee.left_at`; rotation classification is only available
when the matching detail exists. `analytics.v_turnover_monthly` exposes
`classification_complete` and returns null rates when any exit in that
dimensional group lacks detail, instead of reporting a misleading zero.

The assessment performed on 20 October 2026 found no matching
`people.exit` detail for the 176 exits recorded in `core.employee` during
2026. The source ingestion must be restored before current voluntary,
dismissal or rotation-eligible metrics can be considered complete.
