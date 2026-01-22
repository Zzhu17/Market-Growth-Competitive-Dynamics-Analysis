-- Market Trends Mart (national sales levels)
-- Dialect: DuckDB

WITH base AS (
    SELECT
        date,
        industry,
        sales_amount,
        CAST(date || '-01' AS DATE) AS month_date
    FROM read_parquet('data/processed/fact_national_retail_sales.parquet')
),
calc AS (
    SELECT
        date,
        industry,
        sales_amount,
        (sales_amount / LAG(sales_amount) OVER (PARTITION BY industry ORDER BY month_date) - 1) AS mom_growth_pct,
        (sales_amount / LAG(sales_amount, 12) OVER (PARTITION BY industry ORDER BY month_date) - 1) AS yoy_growth_pct,
        (sales_amount / FIRST_VALUE(sales_amount) OVER (PARTITION BY industry ORDER BY month_date)) * 100 AS sales_index
    FROM base
)
SELECT *
FROM calc
ORDER BY date, industry;
