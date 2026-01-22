# Data Lineage

```
MRTS (xlsx) ---------------------+--> data/raw/mtrs/ ---------------------------+
                                 |                                            |
                                 +--> scripts/transform_fact_tables.py ------+---> data/processed/fact_national_retail_sales.parquet
                                                                              |
MSRS (csv) ----------------------+--> data/raw/msrs/ --------------------------+
                                                                              |
                                                                              +---> data/processed/fact_state_retail_growth.parquet
                                                                                       |
                                                                                       +---> sql/marts_market_trends.sql (DuckDB)
                                                                                       |         -> data/marts/marts_market_trends.parquet
                                                                                       |         -> data/published/marts_market_trends.csv
                                                                                       |
                                                                                       +---> sql/marts_growth_contribution.sql (DuckDB)
                                                                                                 -> data/marts/marts_growth_contribution.parquet
                                                                                                 -> data/published/marts_growth_contribution.csv

Processed facts --> scripts/generate_reports.py --> docs/data_validation.md
                                                --> docs/metrics_snapshot.csv
                                                --> docs/figures/*.png

Published marts (CSV) --> Tableau dashboards (Market Overview / Growth Breakdown / Risk & Concentration)
```
