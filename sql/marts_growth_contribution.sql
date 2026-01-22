-- Growth Contribution Mart (state x industry YoY rates)
-- Dialect: DuckDB

WITH base AS (
    SELECT
        date,
        state,
        region,
        industry,
        yoy_pct,
        CAST(date || '-01' AS DATE) AS month_date
    FROM read_parquet('data/processed/fact_state_retail_growth.parquet')
),
base_pos AS (
    SELECT
        date,
        state,
        region,
        industry,
        yoy_pct,
        GREATEST(yoy_pct, 0) AS pos_yoy,
        month_date
    FROM base
),
industry_level AS (
    SELECT
        date,
        region,
        state,
        industry,
        yoy_pct,
        pos_yoy,
        pos_yoy / NULLIF(SUM(pos_yoy) OVER (PARTITION BY date, industry), 0) AS state_contribution,
        SUM(pos_yoy) OVER (PARTITION BY date, industry, region)
            / NULLIF(SUM(pos_yoy) OVER (PARTITION BY date, industry), 0) AS region_contribution,
        ROW_NUMBER() OVER (PARTITION BY date, industry ORDER BY pos_yoy DESC) AS state_rank
    FROM base_pos
),
all_industry AS (
    SELECT
        date,
        state,
        region,
        'All Industries' AS industry,
        AVG(yoy_pct) AS yoy_pct,
        CAST(date || '-01' AS DATE) AS month_date
    FROM base
    GROUP BY date, state, region
),
all_industry_pos AS (
    SELECT
        date,
        state,
        region,
        industry,
        yoy_pct,
        GREATEST(yoy_pct, 0) AS pos_yoy,
        month_date
    FROM all_industry
),
all_industry_level AS (
    SELECT
        date,
        region,
        state,
        industry,
        yoy_pct,
        pos_yoy,
        pos_yoy / NULLIF(SUM(pos_yoy) OVER (PARTITION BY date), 0) AS state_contribution,
        SUM(pos_yoy) OVER (PARTITION BY date, region)
            / NULLIF(SUM(pos_yoy) OVER (PARTITION BY date), 0) AS region_contribution,
        ROW_NUMBER() OVER (PARTITION BY date ORDER BY pos_yoy DESC) AS state_rank
    FROM all_industry_pos
)
SELECT
    date,
    region,
    state,
    industry,
    yoy_pct,
    pos_yoy,
    state_contribution,
    region_contribution,
    CASE
        WHEN state_rank <= 5 THEN 'Top5'
        WHEN state_rank <= 10 THEN 'Top10'
        ELSE 'Other'
    END AS topN_flag
FROM industry_level

UNION ALL

SELECT
    date,
    region,
    state,
    industry,
    yoy_pct,
    pos_yoy,
    state_contribution,
    region_contribution,
    CASE
        WHEN state_rank <= 5 THEN 'Top5'
        WHEN state_rank <= 10 THEN 'Top10'
        ELSE 'Other'
    END AS topN_flag
FROM all_industry_level
ORDER BY date, industry, state;
