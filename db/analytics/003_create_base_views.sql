BEGIN;

CREATE OR REPLACE VIEW analytics.v_bi_employee_categories AS
SELECT
    category.id,
    category.name
FROM core.category AS category
WHERE lower(btrim(category.name)) IN (
    'junior',
    'senior',
    'gerente',
    'manager',
    'director',
    'socio',
    'estructura'
);

COMMENT ON VIEW analytics.v_bi_employee_categories IS
    'Employee categories included in BI metrics: Junior, Senior, Gerente/Manager, Director, Socio and Estructura.';

CREATE OR REPLACE VIEW analytics.v_employee_assignment_intervals AS
SELECT
    history.id AS employee_history_id,
    history.employee_id,
    history.start_at AS effective_from,
    history.end_at AS effective_to,
    history.society_id,
    society.name AS society_name,
    history.office_id,
    office.name AS office_name,
    history.department_id,
    department.name AS department_name,
    department.society_id AS department_society_id,
    history.category_id,
    category.name AS category_name
FROM core.employee_hst AS history
LEFT JOIN core.society AS society
    ON society.id = history.society_id
LEFT JOIN core.office AS office
    ON office.id = history.office_id
LEFT JOIN core.department AS department
    ON department.id = history.department_id
LEFT JOIN core.category AS category
    ON category.id = history.category_id;

COMMENT ON VIEW analytics.v_employee_assignment_intervals IS
    'Effective-dated organisational assignments. Consumers must resolve overlapping rows by latest start_at and id.';

CREATE OR REPLACE VIEW analytics.v_employee_movements AS
WITH movement_events AS (
    SELECT
        employee.id AS employee_id,
        'join'::varchar(8) AS movement_type,
        employee.joined_at AS movement_date,
        NULL::bigint AS source_exit_id,
        NULL::integer AS bol_rotation,
        NULL::date AS source_exit_date
    FROM core.employee AS employee
    WHERE employee.joined_at IS NOT NULL

    UNION ALL

    SELECT
        employee.id AS employee_id,
        'exit'::varchar(8) AS movement_type,
        employee.left_at AS movement_date,
        exit_record.id AS source_exit_id,
        exit_record.bol_rotation,
        exit_record.source_exit_date
    FROM core.employee AS employee
    LEFT JOIN LATERAL (
        SELECT
            employee_exit.id,
            employee_exit.bol_rotation,
            employee_exit.left_at::date AS source_exit_date
        FROM people.exit AS employee_exit
        WHERE employee_exit.employee_id = employee.id
          AND abs(employee_exit.left_at::date - employee.left_at) <= 2
        ORDER BY
            abs(employee_exit.left_at::date - employee.left_at),
            employee_exit.id DESC
        LIMIT 1
    ) AS exit_record
        ON true
    WHERE employee.left_at IS NOT NULL
)
SELECT
    concat(
        events.movement_type,
        ':',
        events.employee_id::text,
        ':',
        events.movement_date::text
    ) AS movement_key,
    events.employee_id,
    events.movement_type,
    events.movement_date,
    date_trunc('month', events.movement_date)::date AS movement_month,
    calendar.calendar_year,
    calendar.calendar_month,
    calendar.fiscal_year,
    calendar.fiscal_year_label,
    calendar.fiscal_quarter,
    calendar.fiscal_semester,
    calendar.fiscal_month,
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
          OR employee.birth_date > events.movement_date
            THEN NULL
        ELSE EXTRACT(
            YEAR FROM age(events.movement_date, employee.birth_date)
        )::smallint
    END AS age_years,
    CASE
        WHEN employee.joined_at IS NULL
          OR employee.joined_at > events.movement_date
            THEN NULL
        ELSE (
            EXTRACT(
                YEAR FROM age(events.movement_date, employee.joined_at)
            )::integer * 12
            + EXTRACT(
                MONTH FROM age(events.movement_date, employee.joined_at)
            )::integer
        )
    END AS tenure_months,
    events.source_exit_id,
    events.source_exit_date,
    events.bol_rotation,
    CASE
        WHEN events.movement_type = 'exit'
            THEN COALESCE(events.bol_rotation, 0) = 1
        ELSE false
    END AS is_rotation_exit,
    events.movement_type = 'exit'
        AND events.source_exit_id IS NOT NULL AS has_exit_detail,
    CASE
        WHEN assignment.employee_history_id IS NOT NULL
            THEN 'employee_hst'
        ELSE 'employee'
    END::varchar(20) AS assignment_source
FROM movement_events AS events
JOIN core.employee AS employee
    ON employee.id = events.employee_id
LEFT JOIN LATERAL (
    SELECT
        history.id AS employee_history_id,
        history.society_id,
        history.office_id,
        history.department_id,
        history.category_id
    FROM core.employee_hst AS history
    WHERE history.employee_id = events.employee_id
      AND history.start_at <= events.movement_date
      AND (
          history.end_at IS NULL
          OR history.end_at >= events.movement_date
      )
    ORDER BY history.start_at DESC, history.id DESC
    LIMIT 1
) AS assignment
    ON true
LEFT JOIN analytics.dim_date AS calendar
    ON calendar.date_day = events.movement_date
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

COMMENT ON VIEW analytics.v_employee_movements IS
    'Join and exit events enriched with the organisational assignment at the event date. Exit reasons are intentionally excluded from v1.';

COMMIT;
