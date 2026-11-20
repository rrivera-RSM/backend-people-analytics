-- Run outside an explicit transaction.
-- Both materialized views have a unique index, so concurrent refresh keeps
-- them readable by Power BI during the operation.

REFRESH MATERIALIZED VIEW CONCURRENTLY
    analytics.mv_employee_monthly_snapshot;

REFRESH MATERIALIZED VIEW CONCURRENTLY
    analytics.mv_employee_movements;

ANALYZE analytics.mv_employee_monthly_snapshot;
ANALYZE analytics.mv_employee_movements;
