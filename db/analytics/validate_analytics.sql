-- Read-only reconciliation checks to run after deployment and every time
-- metric definitions or source ingestion rules change.

WITH expected_fiscal_boundaries (
    date_day,
    fiscal_year,
    fiscal_month,
    fiscal_quarter,
    fiscal_semester
) AS (
    VALUES
        (DATE '2025-08-31', 2025, 12, 4, 2),
        (DATE '2025-09-01', 2026, 1, 1, 1),
        (DATE '2026-02-28', 2026, 6, 2, 1),
        (DATE '2026-03-01', 2026, 7, 3, 2),
        (DATE '2026-08-31', 2026, 12, 4, 2),
        (DATE '2026-09-01', 2027, 1, 1, 1)
)
SELECT
    expected.date_day,
    actual.fiscal_year,
    actual.fiscal_month,
    actual.fiscal_quarter,
    actual.fiscal_semester,
    (
        actual.fiscal_year = expected.fiscal_year
        AND actual.fiscal_month = expected.fiscal_month
        AND actual.fiscal_quarter = expected.fiscal_quarter
        AND actual.fiscal_semester = expected.fiscal_semester
    ) AS matches_expected_fiscal_period
FROM expected_fiscal_boundaries AS expected
LEFT JOIN analytics.dim_date AS actual
    ON actual.date_day = expected.date_day
ORDER BY expected.date_day;

WITH source_headcount AS (
    SELECT count(*)::bigint AS headcount
    FROM core.employee AS employee
    LEFT JOIN LATERAL (
        SELECT history.category_id
        FROM core.employee_hst AS history
        WHERE history.employee_id = employee.id
          AND history.start_at <= current_date
          AND (
              history.end_at IS NULL
              OR history.end_at > current_date
          )
        ORDER BY history.start_at DESC, history.id DESC
        LIMIT 1
    ) AS assignment
        ON true
    JOIN analytics.v_bi_employee_categories AS category
        ON category.id = COALESCE(
            assignment.category_id,
            employee.category_id
        )
    WHERE employee.joined_at <= current_date
      AND (
          employee.left_at IS NULL
          OR employee.left_at > current_date
      )
),
analytics_headcount AS (
    SELECT count(*)::bigint AS headcount
    FROM analytics.v_bi_employee_monthly_snapshot
    WHERE snapshot_month = date_trunc('month', current_date)::date
)
SELECT
    source.headcount AS source_headcount,
    analytics.headcount AS analytics_headcount,
    source.headcount = analytics.headcount AS matches
FROM source_headcount AS source
CROSS JOIN analytics_headcount AS analytics;

SELECT
    'employee_monthly_snapshot' AS dataset,
    count(*)::bigint AS out_of_scope_rows
FROM analytics.v_bi_employee_monthly_snapshot AS snapshot
LEFT JOIN analytics.v_bi_employee_categories AS category
    ON category.id = snapshot.category_id
WHERE category.id IS NULL

UNION ALL

SELECT
    'employee_movements',
    count(*)::bigint
FROM analytics.v_bi_employee_movements AS movement
LEFT JOIN analytics.v_bi_employee_categories AS category
    ON category.id = movement.category_id
WHERE category.id IS NULL;

SELECT
    'powerbi_dataset_all' AS dataset,
    count(*)::bigint AS out_of_scope_rows
FROM analytics.v_powerbi_dataset_all AS dataset
WHERE COALESCE(
        lower(btrim(dataset.professional_category)),
        ''
      ) NOT IN (
        'junior',
        'senior',
        'manager',
        'director',
        'socio',
        'estructura'
      )

UNION ALL

SELECT
    'powerbi_attrition_predictions',
    count(*)::bigint
FROM analytics.v_powerbi_attrition_predictions AS prediction
WHERE COALESCE(
        lower(btrim(prediction.professional_category)),
        ''
      ) NOT IN (
        'junior',
        'senior',
        'manager',
        'director',
        'socio',
        'estructura'
      );

SELECT
    snapshot_month,
    count(*) AS rows,
    count(DISTINCT employee_id) AS employees,
    count(*) = count(DISTINCT employee_id) AS unique_employee_month
FROM analytics.mv_employee_monthly_snapshot
GROUP BY snapshot_month
HAVING count(*) <> count(DISTINCT employee_id)
ORDER BY snapshot_month;

SELECT
    movement_type,
    count(*) AS movements,
    min(movement_date) AS first_movement,
    max(movement_date) AS last_movement
FROM analytics.mv_employee_movements
GROUP BY movement_type
ORDER BY movement_type;

SELECT
    count(*) FILTER (
        WHERE is_rotation_exit
    ) AS rotation_eligible_exits,
    count(*) FILTER (
        WHERE is_voluntary_rotation_exit
    ) AS voluntary_rotation_exits,
    count(*) FILTER (
        WHERE is_dismissal_rotation_exit
    ) AS dismissal_rotation_exits,
    count(*) FILTER (
        WHERE movement_type = 'exit'
          AND NOT has_exit_detail
    ) AS exits_without_detail
FROM analytics.mv_employee_movements;

SELECT
    check_name,
    issue_count,
    severity,
    description
FROM analytics.v_data_quality_checks
ORDER BY
    CASE severity
        WHEN 'error' THEN 1
        WHEN 'warning' THEN 2
        ELSE 3
    END,
    check_name;

SELECT *
FROM analytics.v_executive_monthly
ORDER BY snapshot_month DESC
LIMIT 24;
