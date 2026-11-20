BEGIN;

CREATE SCHEMA IF NOT EXISTS analytics;

COMMENT ON SCHEMA analytics IS
    'Curated analytical layer shared by Power BI and application APIs.';

CREATE TABLE IF NOT EXISTS analytics.configuration (
    singleton boolean PRIMARY KEY DEFAULT true,
    history_start_date date NOT NULL DEFAULT DATE '2019-01-01',
    fiscal_year_start_month smallint NOT NULL DEFAULT 9,
    dimension_end_date date NOT NULL DEFAULT DATE '2035-12-31',
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ck_analytics_configuration_singleton
        CHECK (singleton),
    CONSTRAINT ck_analytics_configuration_fiscal_month
        CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
    CONSTRAINT ck_analytics_configuration_date_range
        CHECK (dimension_end_date >= history_start_date)
);

INSERT INTO analytics.configuration (
    singleton,
    history_start_date,
    fiscal_year_start_month,
    dimension_end_date
)
VALUES (
    true,
    DATE '2019-01-01',
    9,
    DATE '2035-12-31'
)
ON CONFLICT (singleton) DO NOTHING;

COMMENT ON TABLE analytics.configuration IS
    'Singleton configuration for analytics. The confirmed fiscal year runs from 1 September through 31 August and is labelled by its ending year.';

CREATE TABLE IF NOT EXISTS analytics.dim_date (
    date_day date PRIMARY KEY,
    calendar_year integer NOT NULL,
    calendar_quarter smallint NOT NULL,
    calendar_month smallint NOT NULL,
    calendar_month_label varchar(7) NOT NULL,
    month_start date NOT NULL,
    month_end date NOT NULL,
    fiscal_year integer NOT NULL,
    fiscal_year_label varchar(8) NOT NULL,
    fiscal_quarter smallint NOT NULL,
    fiscal_semester smallint NOT NULL,
    fiscal_month smallint NOT NULL,
    is_month_end boolean NOT NULL,
    is_weekend boolean NOT NULL
);

WITH configured_dates AS (
    SELECT
        generated.date_day,
        configuration.fiscal_year_start_month
    FROM analytics.configuration AS configuration
    CROSS JOIN LATERAL generate_series(
        configuration.history_start_date::timestamp,
        configuration.dimension_end_date::timestamp,
        interval '1 day'
    ) AS generated(date_day)
),
derived_dates AS (
    SELECT
        date_day::date AS date_day,
        EXTRACT(YEAR FROM date_day)::integer AS calendar_year,
        EXTRACT(QUARTER FROM date_day)::smallint AS calendar_quarter,
        EXTRACT(MONTH FROM date_day)::smallint AS calendar_month,
        to_char(date_day, 'YYYY-MM') AS calendar_month_label,
        date_trunc('month', date_day)::date AS month_start,
        (
            date_trunc('month', date_day)
            + interval '1 month'
            - interval '1 day'
        )::date AS month_end,
        CASE
            WHEN fiscal_year_start_month = 1
                THEN EXTRACT(YEAR FROM date_day)::integer
            WHEN EXTRACT(MONTH FROM date_day) >= fiscal_year_start_month
                THEN EXTRACT(YEAR FROM date_day)::integer + 1
            ELSE EXTRACT(YEAR FROM date_day)::integer
        END AS fiscal_year,
        (
            (
                EXTRACT(MONTH FROM date_day)::integer
                - fiscal_year_start_month
                + 12
            ) % 12
        ) + 1 AS fiscal_month
    FROM configured_dates
)
INSERT INTO analytics.dim_date (
    date_day,
    calendar_year,
    calendar_quarter,
    calendar_month,
    calendar_month_label,
    month_start,
    month_end,
    fiscal_year,
    fiscal_year_label,
    fiscal_quarter,
    fiscal_semester,
    fiscal_month,
    is_month_end,
    is_weekend
)
SELECT
    date_day,
    calendar_year,
    calendar_quarter,
    calendar_month,
    calendar_month_label,
    month_start,
    month_end,
    fiscal_year,
    'FY' || fiscal_year::text,
    (((fiscal_month - 1) / 3) + 1)::smallint,
    CASE WHEN fiscal_month <= 6 THEN 1 ELSE 2 END::smallint,
    fiscal_month::smallint,
    date_day = month_end,
    EXTRACT(ISODOW FROM date_day) IN (6, 7)
FROM derived_dates
ON CONFLICT (date_day) DO UPDATE
SET
    calendar_year = EXCLUDED.calendar_year,
    calendar_quarter = EXCLUDED.calendar_quarter,
    calendar_month = EXCLUDED.calendar_month,
    calendar_month_label = EXCLUDED.calendar_month_label,
    month_start = EXCLUDED.month_start,
    month_end = EXCLUDED.month_end,
    fiscal_year = EXCLUDED.fiscal_year,
    fiscal_year_label = EXCLUDED.fiscal_year_label,
    fiscal_quarter = EXCLUDED.fiscal_quarter,
    fiscal_semester = EXCLUDED.fiscal_semester,
    fiscal_month = EXCLUDED.fiscal_month,
    is_month_end = EXCLUDED.is_month_end,
    is_weekend = EXCLUDED.is_weekend;

CREATE INDEX IF NOT EXISTS ix_dim_date_month_start
    ON analytics.dim_date (month_start);

CREATE INDEX IF NOT EXISTS ix_dim_date_fiscal_period
    ON analytics.dim_date (fiscal_year, fiscal_month);

COMMENT ON TABLE analytics.dim_date IS
    'Shared calendar dimension. fiscal_year represents the year in which the configured fiscal year ends.';

COMMIT;
