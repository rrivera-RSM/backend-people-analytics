BEGIN;

CREATE OR REPLACE VIEW analytics.v_bi_employee_monthly_snapshot AS
SELECT snapshot.*
FROM analytics.mv_employee_monthly_snapshot AS snapshot
JOIN analytics.v_bi_employee_categories AS category
    ON category.id = snapshot.category_id;

COMMENT ON VIEW analytics.v_bi_employee_monthly_snapshot IS
    'Employee-month facts restricted to the employee categories approved for BI reporting.';

CREATE OR REPLACE VIEW analytics.v_bi_employee_movements AS
SELECT movement.*
FROM analytics.mv_employee_movements AS movement
JOIN analytics.v_bi_employee_categories AS category
    ON category.id = movement.category_id;

COMMENT ON VIEW analytics.v_bi_employee_movements IS
    'Employee movement facts restricted to the employee categories approved for BI reporting.';

CREATE OR REPLACE VIEW analytics.v_workforce_monthly AS
SELECT
    snapshot.snapshot_month,
    max(snapshot.snapshot_date) AS snapshot_date,
    snapshot.calendar_year,
    snapshot.calendar_month,
    snapshot.calendar_month_label,
    snapshot.fiscal_year,
    snapshot.fiscal_year_label,
    snapshot.fiscal_quarter,
    snapshot.fiscal_semester,
    snapshot.fiscal_month,
    snapshot.society_id,
    snapshot.society_name,
    snapshot.office_id,
    snapshot.office_name,
    snapshot.department_id,
    snapshot.department_name,
    snapshot.category_id,
    snapshot.category_name,
    snapshot.gender_id,
    snapshot.gender_name,
    snapshot.organic_onboard,
    count(*)::integer AS headcount,
    count(*) FILTER (WHERE snapshot.is_partner)::integer
        AS partner_headcount,
    sum(snapshot.age_years)::bigint AS age_years_sum,
    count(snapshot.age_years)::integer AS age_observation_count,
    avg(snapshot.age_years)::numeric(10, 2) AS average_age_years,
    sum(snapshot.tenure_months)::bigint AS tenure_months_sum,
    count(snapshot.tenure_months)::integer AS tenure_observation_count,
    (
        avg(snapshot.tenure_months) / 12.0
    )::numeric(10, 2) AS average_tenure_years,
    sum(snapshot.salary)::numeric AS salary_sum,
    count(snapshot.salary)::integer AS salary_observation_count,
    avg(snapshot.salary)::numeric(14, 2) AS average_salary,
    sum(snapshot.bonus)::numeric AS bonus_sum,
    count(snapshot.bonus)::integer AS bonus_observation_count,
    avg(snapshot.bonus)::numeric(14, 2) AS average_bonus,
    sum(snapshot.evaluation_score)::numeric AS evaluation_score_sum,
    count(snapshot.evaluation_score)::integer
        AS evaluation_observation_count,
    avg(snapshot.evaluation_score)::numeric(10, 2)
        AS average_evaluation_score,
    sum(snapshot.attrition_rate)::numeric AS attrition_rate_sum,
    count(snapshot.attrition_rate)::integer
        AS attrition_observation_count,
    avg(snapshot.attrition_rate)::numeric(10, 4)
        AS average_attrition_rate
FROM analytics.v_bi_employee_monthly_snapshot AS snapshot
GROUP BY
    snapshot.snapshot_month,
    snapshot.calendar_year,
    snapshot.calendar_month,
    snapshot.calendar_month_label,
    snapshot.fiscal_year,
    snapshot.fiscal_year_label,
    snapshot.fiscal_quarter,
    snapshot.fiscal_semester,
    snapshot.fiscal_month,
    snapshot.society_id,
    snapshot.society_name,
    snapshot.office_id,
    snapshot.office_name,
    snapshot.department_id,
    snapshot.department_name,
    snapshot.category_id,
    snapshot.category_name,
    snapshot.gender_id,
    snapshot.gender_name,
    snapshot.organic_onboard;

COMMENT ON VIEW analytics.v_workforce_monthly IS
    'Additive workforce metrics at month and full organisational grain. Average components are also exposed for safe re-aggregation.';

CREATE OR REPLACE VIEW analytics.v_movements_monthly AS
SELECT
    movement.movement_month,
    movement.calendar_year,
    movement.calendar_month,
    movement.fiscal_year,
    movement.fiscal_year_label,
    movement.fiscal_quarter,
    movement.fiscal_semester,
    movement.fiscal_month,
    movement.society_id,
    movement.society_name,
    movement.office_id,
    movement.office_name,
    movement.department_id,
    movement.department_name,
    movement.category_id,
    movement.category_name,
    movement.gender_id,
    movement.gender_name,
    count(*) FILTER (
        WHERE movement.movement_type = 'join'
    )::integer AS joins,
    count(*) FILTER (
        WHERE movement.movement_type = 'join'
          AND movement.organic_onboard
    )::integer AS organic_joins,
    count(*) FILTER (
        WHERE movement.movement_type = 'join'
          AND NOT movement.organic_onboard
    )::integer AS inorganic_joins,
    count(*) FILTER (
        WHERE movement.movement_type = 'exit'
    )::integer AS exits,
    count(*) FILTER (
        WHERE movement.is_rotation_exit
    )::integer AS rotation_eligible_exits,
    count(*) FILTER (
        WHERE movement.is_voluntary_rotation_exit
    )::integer AS voluntary_rotation_exits,
    count(*) FILTER (
        WHERE movement.is_dismissal_rotation_exit
    )::integer AS dismissal_rotation_exits,
    count(*) FILTER (
        WHERE movement.movement_type = 'exit'
          AND NOT movement.has_exit_detail
    )::integer AS exits_without_detail,
    sum(movement.salary_at_movement) FILTER (
        WHERE movement.movement_type = 'exit'
    )::numeric AS exit_salary_sum,
    count(movement.salary_at_movement) FILTER (
        WHERE movement.movement_type = 'exit'
    )::integer AS exit_salary_observation_count,
    avg(movement.salary_at_movement) FILTER (
        WHERE movement.movement_type = 'exit'
    )::numeric(14, 2) AS average_exit_salary,
    sum(movement.evaluation_score_at_movement) FILTER (
        WHERE movement.movement_type = 'exit'
    )::numeric AS exit_evaluation_score_sum,
    count(movement.evaluation_score_at_movement) FILTER (
        WHERE movement.movement_type = 'exit'
    )::integer AS exit_evaluation_observation_count
FROM analytics.v_bi_employee_movements AS movement
GROUP BY
    movement.movement_month,
    movement.calendar_year,
    movement.calendar_month,
    movement.fiscal_year,
    movement.fiscal_year_label,
    movement.fiscal_quarter,
    movement.fiscal_semester,
    movement.fiscal_month,
    movement.society_id,
    movement.society_name,
    movement.office_id,
    movement.office_name,
    movement.department_id,
    movement.department_name,
    movement.category_id,
    movement.category_name,
    movement.gender_id,
    movement.gender_name;

COMMENT ON VIEW analytics.v_movements_monthly IS
    'Monthly joins and exits at full organisational grain. Detailed exit reasons are intentionally excluded.';

CREATE OR REPLACE VIEW analytics.v_turnover_monthly AS
WITH workforce AS (
    SELECT
        snapshot_month,
        society_id,
        office_id,
        department_id,
        category_id,
        gender_id,
        count(*)::integer AS headcount
    FROM analytics.v_bi_employee_monthly_snapshot
    GROUP BY
        snapshot_month,
        society_id,
        office_id,
        department_id,
        category_id,
        gender_id
),
movements AS (
    SELECT
        movement_month,
        society_id,
        office_id,
        department_id,
        category_id,
        gender_id,
        count(*) FILTER (
            WHERE movement_type = 'exit'
        )::integer AS exits,
        count(*) FILTER (
            WHERE is_rotation_exit
        )::integer AS rotation_eligible_exits,
        count(*) FILTER (
            WHERE is_voluntary_rotation_exit
        )::integer AS voluntary_rotation_exits,
        count(*) FILTER (
            WHERE is_dismissal_rotation_exit
        )::integer AS dismissal_rotation_exits,
        count(*) FILTER (
            WHERE movement_type = 'exit'
              AND NOT has_exit_detail
        )::integer AS exits_without_detail
    FROM analytics.v_bi_employee_movements
    GROUP BY
        movement_month,
        society_id,
        office_id,
        department_id,
        category_id,
        gender_id
),
metric_keys AS (
    SELECT
        snapshot_month AS metric_month,
        society_id,
        office_id,
        department_id,
        category_id,
        gender_id
    FROM workforce

    UNION

    SELECT
        movement_month,
        society_id,
        office_id,
        department_id,
        category_id,
        gender_id
    FROM movements
),
turnover_components AS (
    SELECT
        keys.metric_month,
        keys.society_id,
        keys.office_id,
        keys.department_id,
        keys.category_id,
        keys.gender_id,
        COALESCE(opening.headcount, 0) AS opening_headcount,
        COALESCE(closing.headcount, 0) AS closing_headcount,
        (
            COALESCE(opening.headcount, 0)
            + COALESCE(closing.headcount, 0)
        ) / 2.0 AS average_headcount,
        COALESCE(movement.exits, 0) AS exits,
        COALESCE(
            movement.rotation_eligible_exits,
            0
        ) AS rotation_eligible_exits,
        COALESCE(
            movement.voluntary_rotation_exits,
            0
        ) AS voluntary_rotation_exits,
        COALESCE(
            movement.dismissal_rotation_exits,
            0
        ) AS dismissal_rotation_exits,
        COALESCE(
            movement.exits_without_detail,
            0
        ) AS exits_without_detail
    FROM metric_keys AS keys
    LEFT JOIN workforce AS closing
        ON closing.snapshot_month = keys.metric_month
       AND closing.society_id IS NOT DISTINCT FROM keys.society_id
       AND closing.office_id IS NOT DISTINCT FROM keys.office_id
       AND closing.department_id IS NOT DISTINCT FROM keys.department_id
       AND closing.category_id IS NOT DISTINCT FROM keys.category_id
       AND closing.gender_id IS NOT DISTINCT FROM keys.gender_id
    LEFT JOIN workforce AS opening
        ON opening.snapshot_month = (
            keys.metric_month - interval '1 month'
        )::date
       AND opening.society_id IS NOT DISTINCT FROM keys.society_id
       AND opening.office_id IS NOT DISTINCT FROM keys.office_id
       AND opening.department_id IS NOT DISTINCT FROM keys.department_id
       AND opening.category_id IS NOT DISTINCT FROM keys.category_id
       AND opening.gender_id IS NOT DISTINCT FROM keys.gender_id
    LEFT JOIN movements AS movement
        ON movement.movement_month = keys.metric_month
       AND movement.society_id IS NOT DISTINCT FROM keys.society_id
       AND movement.office_id IS NOT DISTINCT FROM keys.office_id
       AND movement.department_id IS NOT DISTINCT FROM keys.department_id
       AND movement.category_id IS NOT DISTINCT FROM keys.category_id
       AND movement.gender_id IS NOT DISTINCT FROM keys.gender_id
)
SELECT
    components.metric_month,
    calendar.calendar_year,
    calendar.calendar_month,
    calendar.calendar_month_label,
    calendar.fiscal_year,
    calendar.fiscal_year_label,
    calendar.fiscal_quarter,
    calendar.fiscal_semester,
    calendar.fiscal_month,
    components.society_id,
    society.name AS society_name,
    components.office_id,
    office.name AS office_name,
    components.department_id,
    department.name AS department_name,
    components.category_id,
    category.name AS category_name,
    components.gender_id,
    gender.param_value AS gender_name,
    components.opening_headcount,
    components.closing_headcount,
    components.average_headcount,
    components.exits,
    components.rotation_eligible_exits,
    components.voluntary_rotation_exits,
    components.dismissal_rotation_exits,
    components.exits_without_detail,
    components.exits_without_detail = 0 AS classification_complete,
    CASE
        WHEN components.average_headcount > 0
         AND components.exits_without_detail = 0
            THEN (
                components.rotation_eligible_exits
                / components.average_headcount
            )::numeric(12, 6)
        ELSE NULL
    END AS turnover_rate,
    CASE
        WHEN components.average_headcount > 0
         AND components.exits_without_detail = 0
            THEN (
                components.voluntary_rotation_exits
                / components.average_headcount
            )::numeric(12, 6)
        ELSE NULL
    END AS voluntary_turnover_rate,
    CASE
        WHEN components.average_headcount > 0
         AND components.exits_without_detail = 0
            THEN (
                components.dismissal_rotation_exits
                / components.average_headcount
            )::numeric(12, 6)
        ELSE NULL
    END AS dismissal_turnover_rate
FROM turnover_components AS components
JOIN analytics.dim_date AS calendar
    ON calendar.date_day = components.metric_month
LEFT JOIN core.society AS society
    ON society.id = components.society_id
LEFT JOIN core.office AS office
    ON office.id = components.office_id
LEFT JOIN core.department AS department
    ON department.id = components.department_id
LEFT JOIN core.category AS category
    ON category.id = components.category_id
LEFT JOIN core.param AS gender
    ON gender.param_type = 'gender'
   AND gender.param_key = components.gender_id;

COMMENT ON VIEW analytics.v_turnover_monthly IS
    'Monthly turnover using rotation-eligible exits divided by average opening and closing headcount. Rates must be recalculated from components for wider periods.';

CREATE OR REPLACE VIEW analytics.v_executive_monthly AS
WITH workforce AS (
    SELECT
        snapshot_month,
        max(snapshot_date) AS snapshot_date,
        count(*)::integer AS headcount,
        count(*) FILTER (WHERE is_partner)::integer AS partner_headcount,
        count(DISTINCT society_id)::integer AS society_count,
        count(DISTINCT office_id)::integer AS office_count,
        count(DISTINCT department_id)::integer AS department_count,
        avg(age_years)::numeric(10, 2) AS average_age_years,
        (avg(tenure_months) / 12.0)::numeric(10, 2)
            AS average_tenure_years,
        avg(salary)::numeric(14, 2) AS average_salary,
        avg(evaluation_score)::numeric(10, 2)
            AS average_evaluation_score,
        avg(attrition_rate)::numeric(10, 4)
            AS average_attrition_rate
    FROM analytics.v_bi_employee_monthly_snapshot
    GROUP BY snapshot_month
),
movements AS (
    SELECT
        movement_month,
        count(*) FILTER (
            WHERE movement_type = 'join'
        )::integer AS joins,
        count(*) FILTER (
            WHERE movement_type = 'join'
              AND organic_onboard
        )::integer AS organic_joins,
        count(*) FILTER (
            WHERE movement_type = 'join'
              AND NOT organic_onboard
        )::integer AS inorganic_joins,
        count(*) FILTER (
            WHERE movement_type = 'exit'
        )::integer AS exits,
        count(*) FILTER (
            WHERE is_rotation_exit
        )::integer AS rotation_eligible_exits,
        count(*) FILTER (
            WHERE is_voluntary_rotation_exit
        )::integer AS voluntary_rotation_exits,
        count(*) FILTER (
            WHERE is_dismissal_rotation_exit
        )::integer AS dismissal_rotation_exits,
        count(*) FILTER (
            WHERE movement_type = 'exit'
              AND NOT has_exit_detail
        )::integer AS exits_without_detail
    FROM analytics.v_bi_employee_movements
    GROUP BY movement_month
),
combined AS (
    SELECT
        workforce.*,
        COALESCE(movements.joins, 0) AS joins,
        COALESCE(movements.organic_joins, 0) AS organic_joins,
        COALESCE(movements.inorganic_joins, 0) AS inorganic_joins,
        COALESCE(movements.exits, 0) AS exits,
        COALESCE(
            movements.rotation_eligible_exits,
            0
        ) AS rotation_eligible_exits,
        COALESCE(
            movements.voluntary_rotation_exits,
            0
        ) AS voluntary_rotation_exits,
        COALESCE(
            movements.dismissal_rotation_exits,
            0
        ) AS dismissal_rotation_exits,
        COALESCE(
            movements.exits_without_detail,
            0
        ) AS exits_without_detail
    FROM workforce
    LEFT JOIN movements
        ON movements.movement_month = workforce.snapshot_month
),
with_comparisons AS (
    SELECT
        combined.*,
        lag(headcount) OVER (
            ORDER BY snapshot_month
        ) AS previous_month_headcount,
        lag(headcount, 12) OVER (
            ORDER BY snapshot_month
        ) AS previous_year_headcount
    FROM combined
)
SELECT
    metrics.*,
    metrics.headcount
        - metrics.previous_month_headcount AS monthly_headcount_change,
    CASE
        WHEN metrics.previous_month_headcount > 0
            THEN (
                (
                    metrics.headcount
                    - metrics.previous_month_headcount
                )::numeric
                / metrics.previous_month_headcount
            )::numeric(12, 6)
        ELSE NULL
    END AS monthly_headcount_growth_rate,
    metrics.headcount
        - metrics.previous_year_headcount AS yearly_headcount_change,
    CASE
        WHEN metrics.previous_year_headcount > 0
            THEN (
                (
                    metrics.headcount
                    - metrics.previous_year_headcount
                )::numeric
                / metrics.previous_year_headcount
            )::numeric(12, 6)
        ELSE NULL
    END AS yearly_headcount_growth_rate
FROM with_comparisons AS metrics;

COMMENT ON VIEW analytics.v_executive_monthly IS
    'Company-level monthly metrics for executive cards and trend validation.';

CREATE OR REPLACE VIEW analytics.v_satisfaction_summary AS
SELECT
    survey.id AS survey_id,
    survey.name AS survey_name,
    survey.start_at::date AS survey_start_date,
    survey.end_at::date AS survey_end_date,
    answer.society_id,
    society.name AS society_name,
    answer.office_id,
    office.name AS office_name,
    answer.category_id,
    category.name AS category_name,
    answer.gender_id,
    gender.param_value AS gender_name,
    avg(answer.value)::numeric(10, 4) AS satisfaction_average,
    count(answer.value)::integer AS answer_group_count
FROM people.answer AS answer
JOIN people.survey_question AS survey_question
    ON survey_question.id = answer.survey_question_id
JOIN people.survey AS survey
    ON survey.id = survey_question.survey_id
LEFT JOIN core.society AS society
    ON society.id = answer.society_id
LEFT JOIN core.office AS office
    ON office.id = answer.office_id
JOIN analytics.v_bi_employee_categories AS category
    ON category.id = answer.category_id
LEFT JOIN core.param AS gender
    ON gender.param_type = 'gender'
   AND gender.param_key = answer.gender_id
GROUP BY
    survey.id,
    survey.name,
    survey.start_at::date,
    survey.end_at::date,
    answer.society_id,
    society.name,
    answer.office_id,
    office.name,
    answer.category_id,
    category.name,
    answer.gender_id,
    gender.param_value;

COMMENT ON VIEW analytics.v_satisfaction_summary IS
    'Survey satisfaction aggregated from the already aggregated answer source. Department is unavailable in the source.';

CREATE OR REPLACE VIEW analytics.v_data_quality_checks AS
SELECT
    checks.check_name::varchar(80) AS check_name,
    checks.issue_count::bigint AS issue_count,
    checks.severity::varchar(10) AS severity,
    checks.description::text AS description
FROM (
SELECT
    'overlapping_open_employee_history'::varchar(80) AS check_name,
    COALESCE(sum(open_rows - 1), 0)::bigint AS issue_count,
    'warning'::varchar(10) AS severity,
    'Employees with more than one employee_hst row without end_at.'::text
        AS description
FROM (
    SELECT employee_id, count(*) AS open_rows
    FROM core.employee_hst
    WHERE end_at IS NULL
    GROUP BY employee_id
    HAVING count(*) > 1
) AS duplicates

UNION ALL

SELECT
    'future_employee_history',
    count(*)::bigint,
    'info',
    'employee_hst rows whose start_at is later than current_date.'
FROM core.employee_hst
WHERE start_at > current_date

UNION ALL

SELECT
    'invalid_employee_history_range',
    count(*)::bigint,
    'error',
    'employee_hst rows whose end_at is not later than start_at.'
FROM core.employee_hst
WHERE end_at IS NOT NULL
  AND end_at <= start_at

UNION ALL

SELECT
    'current_snapshot_assignment_fallback',
    count(*)::bigint,
    'warning',
    'Current active employees using core.employee because no valid employee_hst row was resolved.'
FROM analytics.mv_employee_monthly_snapshot
WHERE snapshot_month = date_trunc('month', current_date)::date
  AND assignment_source = 'employee'

UNION ALL

SELECT
    'exits_without_exit_detail',
    count(*)::bigint,
    'warning',
    'Employee exits without a matching people.exit record within two days.'
FROM analytics.mv_employee_movements
WHERE movement_type = 'exit'
  AND NOT has_exit_detail
) AS checks;

COMMIT;
