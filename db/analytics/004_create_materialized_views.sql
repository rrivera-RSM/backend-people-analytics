BEGIN;

CREATE MATERIALIZED VIEW IF NOT EXISTS
    analytics.mv_employee_monthly_snapshot
AS
WITH snapshot_months AS (
    SELECT
        calendar.month_start AS snapshot_month,
        least(calendar.month_end, current_date) AS snapshot_date
    FROM analytics.dim_date AS calendar
    CROSS JOIN analytics.configuration AS configuration
    WHERE calendar.is_month_end
      AND calendar.month_start >= date_trunc(
          'month',
          configuration.history_start_date
      )::date
      AND calendar.month_start <= date_trunc(
          'month',
          current_date
      )::date
)
SELECT
    months.snapshot_month,
    months.snapshot_date,
    calendar.calendar_year,
    calendar.calendar_month,
    calendar.calendar_month_label,
    calendar.fiscal_year,
    calendar.fiscal_year_label,
    calendar.fiscal_quarter,
    calendar.fiscal_semester,
    calendar.fiscal_month,
    employee.id AS employee_id,
    employee.gender_id,
    gender.param_value AS gender_name,
    COALESCE(assignment.society_id, employee.society_id) AS society_id,
    society.name AS society_name,
    COALESCE(assignment.office_id, employee.office_id) AS office_id,
    office.name AS office_name,
    COALESCE(
        assignment.department_id,
        employee.department_id
    ) AS department_id,
    department.name AS department_name,
    COALESCE(assignment.category_id, employee.category_id) AS category_id,
    category.name AS category_name,
    lower(category.name) = 'socio' AS is_partner,
    COALESCE(employee.bol_organic_onboard, 0) = 1 AS organic_onboard,
    CASE
        WHEN employee.birth_date IS NULL
          OR employee.birth_date > months.snapshot_date
            THEN NULL
        ELSE EXTRACT(
            YEAR FROM age(months.snapshot_date, employee.birth_date)
        )::smallint
    END AS age_years,
    CASE
        WHEN employee.joined_at IS NULL
          OR employee.joined_at > months.snapshot_date
            THEN NULL
        ELSE (
            EXTRACT(
                YEAR FROM age(months.snapshot_date, employee.joined_at)
            )::integer * 12
            + EXTRACT(
                MONTH FROM age(months.snapshot_date, employee.joined_at)
            )::integer
        )
    END AS tenure_months,
    salary.salary,
    salary.bonus,
    salary.start_at AS salary_effective_from,
    evaluation.final_score AS evaluation_score,
    evaluation.evaluation_at::date AS evaluation_date,
    attrition.attrition_rate,
    attrition.calculated_at::date AS attrition_calculated_date,
    CASE
        WHEN assignment.employee_history_id IS NOT NULL
            THEN 'employee_hst'
        ELSE 'employee'
    END::varchar(20) AS assignment_source
FROM snapshot_months AS months
JOIN analytics.dim_date AS calendar
    ON calendar.date_day = months.snapshot_date
JOIN core.employee AS employee
    ON employee.joined_at <= months.snapshot_date
   AND (
       employee.left_at IS NULL
       OR employee.left_at > months.snapshot_date
   )
LEFT JOIN LATERAL (
    SELECT
        history.id AS employee_history_id,
        history.society_id,
        history.office_id,
        history.department_id,
        history.category_id
    FROM core.employee_hst AS history
    WHERE history.employee_id = employee.id
      AND history.start_at <= months.snapshot_date
      AND (
          history.end_at IS NULL
          OR history.end_at > months.snapshot_date
      )
    ORDER BY history.start_at DESC, history.id DESC
    LIMIT 1
) AS assignment
    ON true
LEFT JOIN LATERAL (
    SELECT
        employee_salary.salary,
        employee_salary.bonus,
        employee_salary.start_at
    FROM people.salary AS employee_salary
    WHERE employee_salary.employee_id = employee.id
      AND employee_salary.start_at <= months.snapshot_date
      AND (
          employee_salary.end_at IS NULL
          OR employee_salary.end_at > months.snapshot_date
      )
    ORDER BY employee_salary.start_at DESC, employee_salary.id DESC
    LIMIT 1
) AS salary
    ON true
LEFT JOIN LATERAL (
    SELECT
        employee_evaluation.final_score,
        employee_evaluation.evaluation_at
    FROM people.evaluation AS employee_evaluation
    WHERE employee_evaluation.employee_id = employee.id
      AND employee_evaluation.evaluation_at
          < months.snapshot_date::timestamptz + interval '1 day'
    ORDER BY
        employee_evaluation.evaluation_at DESC,
        employee_evaluation.id DESC
    LIMIT 1
) AS evaluation
    ON true
LEFT JOIN LATERAL (
    SELECT
        employee_attrition.attrition_rate,
        employee_attrition.calculated_at
    FROM people.employee_attrition AS employee_attrition
    WHERE employee_attrition.employee_id = employee.id
      AND employee_attrition.calculated_at
          < months.snapshot_date::timestamptz + interval '1 day'
    ORDER BY
        employee_attrition.calculated_at DESC,
        employee_attrition.id DESC
    LIMIT 1
) AS attrition
    ON true
LEFT JOIN core.param AS gender
    ON gender.param_type = 'gender'
   AND gender.param_key = employee.gender_id
LEFT JOIN core.society AS society
    ON society.id = COALESCE(
        assignment.society_id,
        employee.society_id
    )
LEFT JOIN core.office AS office
    ON office.id = COALESCE(
        assignment.office_id,
        employee.office_id
    )
LEFT JOIN core.department AS department
    ON department.id = COALESCE(
        assignment.department_id,
        employee.department_id
    )
LEFT JOIN core.category AS category
    ON category.id = COALESCE(
        assignment.category_id,
        employee.category_id
    );

CREATE UNIQUE INDEX IF NOT EXISTS ux_employee_monthly_snapshot
    ON analytics.mv_employee_monthly_snapshot (
        snapshot_month,
        employee_id
    );

CREATE INDEX IF NOT EXISTS ix_employee_monthly_snapshot_org
    ON analytics.mv_employee_monthly_snapshot (
        snapshot_month,
        society_id,
        office_id,
        department_id,
        category_id
    );

CREATE INDEX IF NOT EXISTS ix_employee_monthly_snapshot_fiscal
    ON analytics.mv_employee_monthly_snapshot (
        fiscal_year,
        fiscal_month
    );

COMMENT ON MATERIALIZED VIEW
    analytics.mv_employee_monthly_snapshot IS
    'One row per active employee and month. The current month uses current_date as its snapshot date.';

CREATE MATERIALIZED VIEW IF NOT EXISTS
    analytics.mv_employee_movements
AS
SELECT
    movement.*,
    (
        movement.is_rotation_exit
        AND lower(exit_reason.param_value) = 'voluntaria'
    ) AS is_voluntary_rotation_exit,
    (
        movement.is_rotation_exit
        AND lower(exit_reason.param_value) = 'despido'
    ) AS is_dismissal_rotation_exit,
    salary.salary AS salary_at_movement,
    salary.bonus AS bonus_at_movement,
    evaluation.final_score AS evaluation_score_at_movement,
    evaluation.evaluation_at::date AS evaluation_date_at_movement
FROM analytics.v_employee_movements AS movement
CROSS JOIN analytics.configuration AS configuration
LEFT JOIN people.exit AS exit_detail
    ON exit_detail.id = movement.source_exit_id
LEFT JOIN core.param AS exit_reason
    ON exit_reason.param_type = 'reason'
   AND exit_reason.param_key = exit_detail.reason_id
LEFT JOIN LATERAL (
    SELECT
        employee_salary.salary,
        employee_salary.bonus
    FROM people.salary AS employee_salary
    WHERE employee_salary.employee_id = movement.employee_id
      AND employee_salary.start_at <= movement.movement_date
      AND (
          employee_salary.end_at IS NULL
          OR employee_salary.end_at > movement.movement_date
      )
    ORDER BY employee_salary.start_at DESC, employee_salary.id DESC
    LIMIT 1
) AS salary
    ON true
LEFT JOIN LATERAL (
    SELECT
        employee_evaluation.final_score,
        employee_evaluation.evaluation_at
    FROM people.evaluation AS employee_evaluation
    WHERE employee_evaluation.employee_id = movement.employee_id
      AND employee_evaluation.evaluation_at
          < movement.movement_date::timestamptz + interval '1 day'
    ORDER BY
        employee_evaluation.evaluation_at DESC,
        employee_evaluation.id DESC
    LIMIT 1
) AS evaluation
    ON true
WHERE movement.movement_date >= configuration.history_start_date
  AND movement.movement_date <= current_date;

CREATE UNIQUE INDEX IF NOT EXISTS ux_employee_movements
    ON analytics.mv_employee_movements (movement_key);

CREATE INDEX IF NOT EXISTS ix_employee_movements_month_org
    ON analytics.mv_employee_movements (
        movement_month,
        movement_type,
        society_id,
        office_id,
        department_id,
        category_id
    );

CREATE INDEX IF NOT EXISTS ix_employee_movements_fiscal
    ON analytics.mv_employee_movements (
        fiscal_year,
        fiscal_month,
        movement_type
    );

COMMENT ON MATERIALIZED VIEW analytics.mv_employee_movements IS
    'Employee join and exit events from the configured history start date. Exit reasons are excluded from v1.';

COMMIT;
