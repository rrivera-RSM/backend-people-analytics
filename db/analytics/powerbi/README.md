# Power BI PostgreSQL copy

This folder contains the reproducible source switch for the legacy
`HR Analytics EXCO.pbix` report.

The process never overwrites the source PBIX. It changes only the four Import
partition expressions that currently use Excel/SharePoint:

- `Dataset_all`
- `Probabilidades_2024`
- `Probabilidades_2025`
- `Clustering_Salidas`

All report pages, visuals, measures, calculated columns, relationships and
cached rows are retained.

## Database prerequisite

Deploy `../006_create_powerbi_compatibility_views.sql` after scripts 001-005.
The Power BI role needs `USAGE` on `analytics` and `SELECT` on:

- `analytics.v_powerbi_dataset_all`
- `analytics.v_powerbi_probabilities_2024`
- `analytics.v_powerbi_probabilities_2025`
- `analytics.v_powerbi_clustering_salidas`

The detailed Exit Reasons source is not present in the current database.
`v_powerbi_clustering_salidas` therefore exposes an empty typed contract so
the model can refresh without Excel. That page becomes blank after the first
database refresh instead of showing stale or fabricated data.

Employee-grain survey answers and travel expenses are also unavailable in the
current database. Their compatibility columns are nullable and are not
fabricated.

## Area and society semantics

The legacy model uses three related fields:

- `SOCIEDAD`: the legal society name.
- `SOCIEDAD-Nombre`: the business area shown by the `HC por áreas` visual.
- `AREA/DEPARTAMENTO`: the employee department, not the business area.

The PostgreSQL view and Power Query both normalize `SOCIEDAD-Nombre` from
the legal society name. Unknown non-null societies fall back to their trimmed
name instead of becoming blank.

## Test-data exclusion

Employees are excluded from the report when either their current or historical
society/area or department has a trimmed name beginning with `ADN`,
case-insensitively.
The exclusion is applied before aggregation, so those employees do not appear
in slicers and do not contribute to headcount, hires, exits, turnover or
attrition predictions.

## Employee category scope

Employee-based report queries use the canonical population: Junior, Senior,
Gerente/Manager, Director, Socio and Estructura. The PostgreSQL compatibility
views apply this rule using the category valid for each fiscal snapshot or
prediction date.

The Power Query expressions intentionally do not repeat the category
allow-list. PostgreSQL is the single source of truth for population scope,
which avoids rule drift between SQL, generated PBIX files and manually edited
report copies.

## Connection placeholders

Each file in `queries/` contains these values:

```text
POWERBI_POSTGRES_SERVER:5432
POWERBI_POSTGRES_DATABASE
```

Replace them with the real PostgreSQL host/port and database before building,
or edit the four queries in Power Query after opening the generated copy.
Credentials are intentionally not stored in the project or PBIX.

## Build a copy

Create an isolated environment and install the pinned tool:

```bash
python -m venv /tmp/people-analytics-pbix
/tmp/people-analytics-pbix/bin/pip install -r requirements-powerbi.txt
```

Then generate the copy:

```bash
/tmp/people-analytics-pbix/bin/python build_postgresql_copy.py \
  "/mnt/c/Users/<user>/Downloads/HR Analytics EXCO.pbix" \
  "./output/HR Analytics EXCO - PostgreSQL.pbix"
```

The build refuses to use the same input and output path. It hashes the source
before and after, validates the result, checks that the four sources are
PostgreSQL Import partitions, and writes a sibling
`.validation.json` report.

## First Power BI refresh

1. Open the generated PBIX, not the original.
2. Set the real PostgreSQL host and database if placeholders remain.
3. Enter the read-only database credentials when Power BI requests them.
4. Refresh the model.
5. Reconcile the fiscal totals and known data-quality tolerances before
   publishing.

The fiscal year remains 1 September through 31 August and is labelled in the
legacy model by its starting year (for example, September 2025-August 2026 is
`Año Fiscal = 2025`).
