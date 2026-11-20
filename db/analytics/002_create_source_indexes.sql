BEGIN;

-- Effective-dated lookups used by the monthly snapshot and movement facts.
CREATE INDEX IF NOT EXISTS ix_employee_hst_employee_effective
    ON core.employee_hst (
        employee_id,
        start_at DESC,
        end_at,
        id DESC
    );

CREATE INDEX IF NOT EXISTS ix_salary_employee_effective
    ON people.salary (
        employee_id,
        start_at DESC,
        end_at,
        id DESC
    );

CREATE INDEX IF NOT EXISTS ix_evaluation_employee_date
    ON people.evaluation (
        employee_id,
        evaluation_at DESC,
        id DESC
    );

CREATE INDEX IF NOT EXISTS ix_employee_attrition_employee_date
    ON people.employee_attrition (
        employee_id,
        calculated_at DESC,
        id DESC
    );

CREATE INDEX IF NOT EXISTS ix_exit_employee_date
    ON people.exit (
        employee_id,
        left_at DESC,
        id DESC
    );

CREATE INDEX IF NOT EXISTS ix_employee_joined_at
    ON core.employee (joined_at);

CREATE INDEX IF NOT EXISTS ix_employee_left_at
    ON core.employee (left_at);

COMMIT;
