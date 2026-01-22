# Data Pipeline Design

## Scope
- **Time window:** 2022-01 to 2024-12 (36 months)
- **Sources:**
  - MRTS (national monthly retail sales levels)
  - MSRS (state-level monthly YoY % change)
- **Outputs:** two fact tables, **not joined**

## Inputs (official sources)
- **MRTS (national level):**
  - Source page: https://www.census.gov/retail/sales.html
  - File type: Excel or CSV (download link to be confirmed)
  - Expected content: national monthly retail sales by industry category

- **MSRS (state growth):**
  - Source page: https://www.census.gov/retail/state_retail_sales.html
  - File type: CSV (download link to be confirmed; likely a wide format with `yyYYYYMM` columns)
  - Expected content: state-level YoY % change by industry category

**Source configuration:** locked in `config/data_sources.yaml`.
**Ingestion rule:** ingestion scripts do **not** scrape landing pages; file URLs are manually curated in `files:` for auditability.

## Outputs (analysis-ready)
1) **fact_national_retail_sales**
   - `date` (YYYY-MM)
   - `industry`
   - `sales_amount`

2) **fact_state_retail_growth**
   - `date` (YYYY-MM)
   - `state`
   - `region`
   - `industry`
   - `yoy_pct`

**Storage layers:**
- `data/processed/*.parquet` (primary pipeline output, typed and efficient)
- `data/published/*.csv` (sharing / Tableau-friendly)

**Target industry groups (analysis layer):**
- Food & Beverage Stores
- General Merchandise
- Motor Vehicles & Parts
- Clothing & Accessories
- Electronics & Appliances
- Nonstore Retail (E-commerce)
- Other Specialty Retail

**MSRS coverage note:**  
MSRS state data does not include NAICS 454 (Nonstore Retail) in the current release, so state-level outputs may show 6 groups.

## Transformations
### MRTS (national sales levels)
- Download source file and cache raw copy in `data/raw/mrts/`.
- Standardize column names and clean numeric fields.
- Convert date column to `YYYY-MM`.
- Filter to 2022-01 → 2024-12.
- Keep/rename columns to `date`, `industry`, `sales_amount`.
- Output to `data/processed/fact_national_retail_sales.csv` (or `.parquet`).

### MSRS (state YoY %)
- Download source file and cache raw copy in `data/raw/msrs/`.
- If wide format, melt `yyYYYYMM` to long `date`.
- Clean numeric fields, handle suppressed/missing values.
- Filter to 2022-01 → 2024-12.
- Map `state` → `region` via reference table (to be created in `data/reference/state_region_map.csv`).
- Standardize industry categories across sources (classification crosswalk in `data/reference/industry_crosswalk.csv`).
- If multiple NAICS codes map to one industry group (e.g., Other Specialty Retail), compute **unweighted mean** YoY % per state-month-group due to lack of level weights.
- Output to `data/processed/fact_state_retail_growth.csv` (or `.parquet`).

**Reference readiness:**  
`data/reference/state_region_map.csv` includes all 50 states + DC with Census region/division/FIPS.

## Validation Checks
- 36 months present for each table (2022-01 to 2024-12).
- No duplicate keys:
  - MRTS: (`date`, `industry`)
  - MSRS: (`date`, `state`, `industry`)
- Null rate checks on `sales_amount` and `yoy_pct`.
- Region mapping coverage: 100% of states mapped.

## Growth Contribution Definition (MSRS)
Growth contribution is computed using **positive-only** YoY rates to avoid negative values inflating contribution shares:
- `positive_yoy = max(yoy_pct, 0)`
- `growth_contribution = positive_yoy / SUM(positive_yoy)`

## Open Questions
None. Output layers and contribution logic are locked.
