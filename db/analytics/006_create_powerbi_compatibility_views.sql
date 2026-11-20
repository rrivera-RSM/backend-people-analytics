-- DBeaver: run this whole file with Execute SQL Script (Alt+X).
-- Do not run a selected block with Execute SQL Statement (Ctrl+Enter).
BEGIN;

CREATE OR REPLACE VIEW analytics.v_powerbi_dataset_all AS
WITH test_employees AS (
    SELECT employee.id AS employee_id
    FROM core.employee AS employee
    LEFT JOIN core.society AS society
      ON society.id = employee.society_id
    LEFT JOIN core.department AS department
      ON department.id = employee.department_id
    WHERE COALESCE(upper(trim(society.name)), '') LIKE 'ADN%'
       OR COALESCE(upper(trim(department.name)), '') LIKE 'ADN%'

    UNION

    SELECT history.employee_id
    FROM core.employee_hst AS history
    LEFT JOIN core.society AS society
      ON society.id = history.society_id
    LEFT JOIN core.department AS department
      ON department.id = history.department_id
    WHERE COALESCE(upper(trim(society.name)), '') LIKE 'ADN%'
       OR COALESCE(upper(trim(department.name)), '') LIKE 'ADN%'
),
fiscal_periods AS (
    SELECT
        calendar.fiscal_year - 1 AS fiscal_year,
        min(calendar.date_day) AS period_start,
        max(calendar.date_day) AS period_end,
        least(max(calendar.date_day), current_date) AS snapshot_date
    FROM analytics.dim_date AS calendar
    GROUP BY calendar.fiscal_year
    HAVING min(calendar.date_day) >= DATE '2020-09-01'
       AND min(calendar.date_day) <= current_date
),
employee_periods AS (
    SELECT
        employee.*,
        period.fiscal_year,
        period.period_start,
        period.period_end,
        period.snapshot_date,
        least(
            period.snapshot_date,
            COALESCE(employee.left_at, period.snapshot_date)
        ) AS employee_as_of_date
    FROM core.employee AS employee
    JOIN fiscal_periods AS period
      ON employee.joined_at <= period.snapshot_date
     AND (
            employee.left_at IS NULL
            OR employee.left_at >= period.period_start
         )
    WHERE NOT EXISTS (
        SELECT 1
        FROM test_employees AS test_employee
        WHERE test_employee.employee_id = employee.id
    )
),
enriched AS (
    SELECT
        employee_periods.id AS employee_id,
        employee_periods.first_name,
        employee_periods.last_name,
        employee_periods.email,
        employee_periods.dni,
        employee_periods.birth_date,
        employee_periods.joined_at,
        employee_periods.left_at,
        employee_periods.fiscal_year,
        employee_periods.period_start,
        employee_periods.period_end,
        employee_periods.snapshot_date,
        employee_periods.employee_as_of_date,
        employee_periods.bol_organic_onboard,
        gender.param_value AS gender,
        society.name AS society,
        office.name AS office,
        CASE
            WHEN department.name = 'PERSONAS' THEN 'PEOPLE & CULTURE'
            ELSE department.name
        END AS department,
        CASE category.name
            WHEN 'Becario s/c' THEN 'Becario'
            WHEN 'AU/EX' THEN 'Autónomo/Externo'
            WHEN 'Gerente' THEN 'Manager'
            ELSE category.name
        END AS professional_category,
        CASE
            WHEN society.name IS NULL THEN NULL
            WHEN upper(trim(society.name))
                    LIKE '%SERVICIOS ADMINISTRATIVOS%'
                THEN 'Servicios'
            WHEN upper(trim(society.name)) LIKE '%AUDITORES%'
                THEN 'Auditoría'
            WHEN upper(trim(society.name)) LIKE '%CONSULTORES%'
                THEN 'Consulting'
            WHEN upper(trim(society.name))
                    LIKE '%ASESORES LEGALES Y TRIBUTARIOS%'
                THEN 'Tax & Legal'
            WHEN upper(trim(society.name)) LIKE '%CORPORATE FINANCE%'
                THEN 'Corporate'
            ELSE trim(society.name)
        END AS society_short_name,
        salary.salary,
        salary.bonus,
        evaluation.final_score,
        COALESCE(positive_impact.bol_positive_impact, 0)
            AS positive_impact,
        exit_detail.id AS exit_id,
        exit_detail.bol_rotation,
        exit_reason.param_value AS exit_motive,
        CASE
            WHEN employee_periods.birth_date IS NULL
              OR employee_periods.birth_date
                    > employee_periods.employee_as_of_date
                THEN NULL
            ELSE EXTRACT(
                YEAR FROM age(
                    employee_periods.employee_as_of_date,
                    employee_periods.birth_date
                )
            )::integer
        END AS age,
        CASE
            WHEN employee_periods.joined_at IS NULL
              OR employee_periods.joined_at
                    > employee_periods.employee_as_of_date
                THEN NULL
            ELSE round(
                (
                    employee_periods.employee_as_of_date
                    - employee_periods.joined_at
                )::numeric / 365.25,
                2
            )
        END AS tenure_years
    FROM employee_periods
    LEFT JOIN LATERAL (
        SELECT
            history.id,
            history.society_id,
            history.office_id,
            history.department_id,
            history.category_id
        FROM core.employee_hst AS history
        WHERE history.employee_id = employee_periods.id
          AND history.start_at <= employee_periods.employee_as_of_date
          AND (
                history.end_at IS NULL
                OR history.end_at >= employee_periods.employee_as_of_date
              )
        ORDER BY history.start_at DESC, history.id DESC
        LIMIT 1
    ) AS assignment
      ON true
    LEFT JOIN core.society AS society
      ON society.id = COALESCE(
            assignment.society_id,
            employee_periods.society_id
         )
    LEFT JOIN core.office AS office
      ON office.id = COALESCE(
            assignment.office_id,
            employee_periods.office_id
         )
    LEFT JOIN core.department AS department
      ON department.id = COALESCE(
            assignment.department_id,
            employee_periods.department_id
         )
    JOIN analytics.v_bi_employee_categories AS category
      ON category.id = COALESCE(
            assignment.category_id,
            employee_periods.category_id
         )
    LEFT JOIN core.param AS gender
      ON gender.param_type = 'gender'
     AND gender.param_key = employee_periods.gender_id
    LEFT JOIN LATERAL (
        SELECT
            employee_salary.salary,
            employee_salary.bonus
        FROM people.salary AS employee_salary
        WHERE employee_salary.employee_id = employee_periods.id
          AND employee_salary.start_at
                <= employee_periods.employee_as_of_date
          AND (
                employee_salary.end_at IS NULL
                OR employee_salary.end_at
                    > employee_periods.employee_as_of_date
              )
        ORDER BY employee_salary.start_at DESC, employee_salary.id DESC
        LIMIT 1
    ) AS salary
      ON true
    LEFT JOIN LATERAL (
        SELECT employee_evaluation.final_score
        FROM people.evaluation AS employee_evaluation
        WHERE employee_evaluation.employee_id = employee_periods.id
          AND employee_evaluation.evaluation_at
                < employee_periods.employee_as_of_date::timestamptz
                    + interval '1 day'
        ORDER BY
            employee_evaluation.evaluation_at DESC,
            employee_evaluation.id DESC
        LIMIT 1
    ) AS evaluation
      ON true
    LEFT JOIN LATERAL (
        SELECT impact.bol_positive_impact
        FROM people.positive_impact AS impact
        WHERE impact.employee_id = employee_periods.id
          AND impact.evaluation_at
                < employee_periods.employee_as_of_date::timestamptz
                    + interval '1 day'
        ORDER BY impact.evaluation_at DESC, impact.id DESC
        LIMIT 1
    ) AS positive_impact
      ON true
    LEFT JOIN LATERAL (
        SELECT
            employee_exit.id,
            employee_exit.reason_id,
            employee_exit.bol_rotation
        FROM people.exit AS employee_exit
        WHERE employee_exit.employee_id = employee_periods.id
          AND employee_periods.left_at IS NOT NULL
          AND abs(
                employee_exit.left_at::date
                - employee_periods.left_at
              ) <= 2
        ORDER BY
            abs(
                employee_exit.left_at::date
                - employee_periods.left_at
            ),
            employee_exit.id DESC
        LIMIT 1
    ) AS exit_detail
      ON true
    LEFT JOIN core.param AS exit_reason
      ON exit_reason.param_type = 'reason'
     AND exit_reason.param_key = exit_detail.reason_id
    WHERE COALESCE(upper(trim(society.name)), '') NOT LIKE 'ADN%'
      AND COALESCE(
            upper(trim(department.name)), ''
          ) NOT LIKE 'ADN%'
),
with_previous AS (
    SELECT
        enriched.*,
        lag(enriched.professional_category) OVER (
            PARTITION BY enriched.employee_id
            ORDER BY enriched.fiscal_year
        ) AS previous_professional_category,
        lag(enriched.salary) OVER (
            PARTITION BY enriched.employee_id
            ORDER BY enriched.fiscal_year
        ) AS previous_salary
    FROM enriched
)
SELECT
    employee_id::text,
    first_name,
    last_name,
    office,
    society,
    department,
    dni,
    birth_date,
    gender,
    joined_at,
    left_at,
    fiscal_year,
    professional_category,
    CASE
        WHEN left_at BETWEEN period_start AND snapshot_date THEN '1'
        ELSE '0'
    END AS target,
    age,
    tenure_years,
    CASE
        WHEN previous_professional_category IS NOT NULL
         AND professional_category IS DISTINCT FROM
                previous_professional_category
            THEN '1'
        ELSE '0'
    END AS promotion,
    salary,
    CASE
        WHEN salary IS NOT NULL
         AND previous_salary > 0
            THEN (salary - previous_salary) / previous_salary
        ELSE NULL
    END AS salary_increase,
    NULL::numeric AS survey_q01,
    NULL::numeric AS survey_q02,
    NULL::numeric AS survey_q03,
    NULL::numeric AS survey_q04,
    NULL::numeric AS survey_q05,
    NULL::numeric AS survey_q06,
    NULL::numeric AS survey_q07,
    NULL::numeric AS survey_q08,
    NULL::numeric AS survey_q09,
    NULL::numeric AS survey_q10,
    NULL::numeric AS survey_q11,
    NULL::numeric AS survey_q12,
    NULL::numeric AS survey_q13,
    NULL::numeric AS survey_q14,
    NULL::numeric AS survey_q15,
    NULL::numeric AS survey_q16,
    NULL::numeric AS survey_q17,
    NULL::numeric AS survey_q18,
    NULL::numeric AS survey_q19,
    NULL::numeric AS survey_q20,
    NULL::numeric AS survey_q21,
    NULL::numeric AS survey_q22,
    NULL::numeric AS survey_q23,
    NULL::numeric AS survey_q24,
    NULL::numeric AS survey_q25,
    NULL::numeric AS survey_q26,
    NULL::numeric AS survey_q27,
    NULL::numeric AS survey_q28,
    NULL::numeric AS survey_q29,
    bonus,
    NULL::numeric AS mileage,
    NULL::numeric AS per_diem,
    NULL::numeric AS lodging,
    NULL::numeric AS transport,
    final_score,
    NULL::text AS flexible_compensation,
    society_short_name,
    NULL::numeric AS satisfaction_average,
    trim(concat_ws(' ', first_name, last_name)) AS full_name,
    NULL::text AS exit_cause,
    CASE
        WHEN exit_id IS NULL THEN NULL
        WHEN COALESCE(bol_rotation, 0) = 1 THEN 'Sí'
        ELSE 'No'
    END AS rotation_flag,
    exit_motive,
    NULL::numeric AS enc_brand,
    NULL::numeric AS enc_environment,
    NULL::numeric AS enc_training,
    NULL::text AS exit_cause_group,
    positive_impact,
    NULL::numeric AS enc_development,
    NULL::numeric AS enc_work_life,
    NULL::numeric AS enc_internal_communication,
    NULL::numeric AS enc_salary,
    NULL::numeric AS total_expenses,
    NULL::text AS expense_category,
    email,
    CASE
        WHEN COALESCE(bol_organic_onboard, 0) = 1 THEN '1'
        ELSE '0'
    END AS inorganic_growth,
    NULL::text AS distance_km
FROM with_previous;

COMMENT ON VIEW analytics.v_powerbi_dataset_all IS
    'Compatibility dataset for the legacy HR Analytics EXCO semantic model. One row per employee and fiscal year (September-August), labelled by the starting year. Survey detail, travel expenses and detailed exit causes remain null because the current database does not provide employee-grain values for those fields.';

CREATE OR REPLACE VIEW analytics.v_powerbi_attrition_predictions AS
WITH test_employees AS (
    SELECT employee.id AS employee_id
    FROM core.employee AS employee
    LEFT JOIN core.society AS society
      ON society.id = employee.society_id
    LEFT JOIN core.department AS department
      ON department.id = employee.department_id
    WHERE COALESCE(upper(trim(society.name)), '') LIKE 'ADN%'
       OR COALESCE(upper(trim(department.name)), '') LIKE 'ADN%'

    UNION

    SELECT history.employee_id
    FROM core.employee_hst AS history
    LEFT JOIN core.society AS society
      ON society.id = history.society_id
    LEFT JOIN core.department AS department
      ON department.id = history.department_id
    WHERE COALESCE(upper(trim(society.name)), '') LIKE 'ADN%'
       OR COALESCE(upper(trim(department.name)), '') LIKE 'ADN%'
),
prediction_ranked AS (
    SELECT
        attrition.*,
        CASE
            WHEN EXTRACT(MONTH FROM attrition.calculated_at) >= 9
                THEN EXTRACT(YEAR FROM attrition.calculated_at)::integer
            ELSE EXTRACT(YEAR FROM attrition.calculated_at)::integer - 1
        END AS fiscal_year,
        row_number() OVER (
            PARTITION BY
                attrition.employee_id,
                CASE
                    WHEN EXTRACT(MONTH FROM attrition.calculated_at) >= 9
                        THEN EXTRACT(YEAR FROM attrition.calculated_at)::integer
                    ELSE EXTRACT(YEAR FROM attrition.calculated_at)::integer - 1
                END
            ORDER BY attrition.calculated_at DESC, attrition.id DESC
        ) AS prediction_rank
    FROM people.employee_attrition AS attrition
    WHERE attrition.employee_id IS NOT NULL
      AND attrition.attrition_rate IS NOT NULL
      AND NOT EXISTS (
            SELECT 1
            FROM test_employees AS test_employee
            WHERE test_employee.employee_id = attrition.employee_id
          )
),
prediction AS (
    SELECT *
    FROM prediction_ranked
    WHERE prediction_rank = 1
)
SELECT
    prediction.employee_id::text AS employee_id,
    prediction.fiscal_year,
    prediction.calculated_at::date AS prediction_date,
    prediction.attrition_rate,
    employee.first_name,
    employee.last_name,
    employee.birth_date,
    employee.joined_at,
    employee.left_at,
    gender.param_value AS gender,
    society.name AS society,
    office.name AS office,
    CASE
        WHEN department.name = 'PERSONAS' THEN 'PEOPLE & CULTURE'
        ELSE department.name
    END AS department,
    CASE category.name
        WHEN 'Becario s/c' THEN 'Becario'
        WHEN 'AU/EX' THEN 'Autónomo/Externo'
        WHEN 'Gerente' THEN 'Manager'
        ELSE category.name
    END AS professional_category,
    CASE
        WHEN society.name IS NULL THEN NULL
        WHEN upper(trim(society.name))
                LIKE '%SERVICIOS ADMINISTRATIVOS%'
            THEN 'Servicios'
        WHEN upper(trim(society.name)) LIKE '%AUDITORES%'
            THEN 'Auditoría'
        WHEN upper(trim(society.name)) LIKE '%CONSULTORES%'
            THEN 'Consulting'
        WHEN upper(trim(society.name))
                LIKE '%ASESORES LEGALES Y TRIBUTARIOS%'
            THEN 'Tax & Legal'
        WHEN upper(trim(society.name)) LIKE '%CORPORATE FINANCE%'
            THEN 'Corporate'
        ELSE trim(society.name)
    END AS society_short_name,
    salary.salary,
    evaluation.final_score,
    CASE
        WHEN employee.left_at BETWEEN
            make_date(prediction.fiscal_year, 9, 1)
            AND make_date(prediction.fiscal_year + 1, 8, 31)
            THEN '1'
        ELSE '0'
    END AS target,
    CASE
        WHEN prediction.attrition_rate >= 0.4 THEN '1'
        ELSE '0'
    END AS prediction_target,
    CASE
        WHEN prediction.attrition_rate >= 0.185 THEN 'Abandona'
        ELSE 'Permanece'
    END AS permanence_label
FROM prediction
JOIN core.employee AS employee
  ON employee.id = prediction.employee_id
LEFT JOIN LATERAL (
    SELECT
        history.society_id,
        history.office_id,
        history.department_id,
        history.category_id
    FROM core.employee_hst AS history
    WHERE history.employee_id = prediction.employee_id
      AND history.start_at <= prediction.calculated_at::date
      AND (
            history.end_at IS NULL
            OR history.end_at >= prediction.calculated_at::date
          )
    ORDER BY history.start_at DESC, history.id DESC
    LIMIT 1
) AS assignment
  ON true
LEFT JOIN core.society AS society
  ON society.id = COALESCE(assignment.society_id, employee.society_id)
LEFT JOIN core.office AS office
  ON office.id = COALESCE(assignment.office_id, employee.office_id)
LEFT JOIN core.department AS department
  ON department.id = COALESCE(
        assignment.department_id,
        employee.department_id
     )
JOIN analytics.v_bi_employee_categories AS category
  ON category.id = COALESCE(assignment.category_id, employee.category_id)
LEFT JOIN core.param AS gender
  ON gender.param_type = 'gender'
 AND gender.param_key = employee.gender_id
LEFT JOIN LATERAL (
    SELECT employee_salary.salary
    FROM people.salary AS employee_salary
    WHERE employee_salary.employee_id = prediction.employee_id
      AND employee_salary.start_at <= prediction.calculated_at::date
      AND (
            employee_salary.end_at IS NULL
            OR employee_salary.end_at > prediction.calculated_at::date
          )
    ORDER BY employee_salary.start_at DESC, employee_salary.id DESC
    LIMIT 1
) AS salary
  ON true
LEFT JOIN LATERAL (
    SELECT employee_evaluation.final_score
    FROM people.evaluation AS employee_evaluation
    WHERE employee_evaluation.employee_id = prediction.employee_id
      AND employee_evaluation.evaluation_at <= prediction.calculated_at
    ORDER BY
        employee_evaluation.evaluation_at DESC,
        employee_evaluation.id DESC
    LIMIT 1
) AS evaluation
  ON true
WHERE COALESCE(upper(trim(society.name)), '') NOT LIKE 'ADN%'
  AND COALESCE(upper(trim(department.name)), '') NOT LIKE 'ADN%';

COMMENT ON VIEW analytics.v_powerbi_attrition_predictions IS
    'Latest stored attrition prediction per employee and fiscal year, enriched for the two legacy prediction tables.';

CREATE OR REPLACE VIEW analytics.v_powerbi_probabilities_2024 AS
SELECT
    employee_id,
    first_name,
    last_name,
    professional_category,
    office,
    society,
    department,
    NULL::text AS job_title,
    joined_at,
    left_at,
    salary,
    attrition_rate AS probability,
    permanence_label
FROM analytics.v_powerbi_attrition_predictions
WHERE fiscal_year = 2024;

COMMENT ON VIEW analytics.v_powerbi_probabilities_2024 IS
    'Legacy Probabilidades_2024 contract. It is empty when historical FY2024 predictions are not stored in people.employee_attrition.';

CREATE OR REPLACE VIEW analytics.v_powerbi_probabilities_2025 AS
SELECT
    employee_id,
    target,
    fiscal_year::text AS fiscal_year,
    prediction_target,
    attrition_rate::text AS probability_actual,
    first_name,
    last_name,
    office,
    society,
    department,
    birth_date::text AS birth_date,
    gender,
    joined_at::text AS joined_at,
    left_at::text AS left_at,
    final_score,
    professional_category,
    society_short_name
FROM analytics.v_powerbi_attrition_predictions
WHERE fiscal_year = (
    SELECT max(latest.fiscal_year)
    FROM analytics.v_powerbi_attrition_predictions AS latest
);

COMMENT ON VIEW analytics.v_powerbi_probabilities_2025 IS
    'Legacy Probabilidades_2025 contract. The table name is retained for report compatibility while the view exposes the latest available fiscal prediction set.';

CREATE OR REPLACE VIEW analytics.v_powerbi_clustering_salidas AS
SELECT
    NULL::double precision AS tsne1,
    NULL::double precision AS tsne2,
    NULL::double precision AS workload,
    NULL::double precision AS salary,
    NULL::double precision AS environment,
    NULL::double precision AS salary_increase,
    NULL::double precision AS bonus,
    NULL::double precision AS technical_training,
    NULL::text AS professional_category,
    NULL::bigint AS age,
    NULL::double precision AS tenure,
    NULL::text AS total_expenses_category,
    NULL::double precision AS autonomy,
    NULL::text AS cluster,
    NULL::text AS exit_cause,
    NULL::text AS motive_cluster,
    NULL::text AS society,
    NULL::text AS office,
    NULL::text AS employee_id,
    NULL::text AS last_name,
    NULL::text AS first_name
WHERE false;

COMMENT ON VIEW analytics.v_powerbi_clustering_salidas IS
    'Empty typed compatibility contract for the out-of-scope detailed Exit Reasons page.';

COMMIT;
