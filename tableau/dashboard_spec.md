# Tableau Dashboard Spec

## Data Sources
- **Market Trends Mart:** `sql/marts_market_trends.sql`
- **Growth Contribution Mart:** `sql/marts_growth_contribution.sql`

---

## 1) Market Overview (MRTS)
**Purpose:** Market size, growth, and seasonality at the national level.

**Default view:** last 12 months, all industries.
**Filters (only 2):** Date range, Industry.

**Key fields:**
- `date` (continuous month)
- `industry`
- `sales_amount`

**Sheets (minimum set):**
- Total Sales Trend
- YoY Growth
- MoM Growth
- Seasonality Heatmap

**Views:**
1) **Total Sales (Line)**
   - X: `date`
   - Y: `SUM(sales_amount)`
   - Color: `industry` (or a fixed “Total” if desired)

2) **YoY Growth (Bar/Line)**
   - X: `date`
   - Y: YoY % of `sales_amount`

3) **MoM Growth (Bar/Line)**
   - X: `date`
   - Y: MoM % of `sales_amount`

4) **Seasonality Heatmap (Month × Year)**
   - Rows: `MONTH(date)`
   - Columns: `YEAR(date)`
   - Color: `SUM(sales_amount)` or YoY %

**Proposed calculated fields:**
- `YoY % (MRTS)`
  - `SUM([sales_amount]) / LOOKUP(SUM([sales_amount]), -12) - 1`
- `MoM % (MRTS)`
  - `SUM([sales_amount]) / LOOKUP(SUM([sales_amount]), -1) - 1`

---

## 2) Growth Breakdown (MSRS)
**Purpose:** Decompose growth by region, state, and industry (growth rates only).

**Default view:** last 12 months, all industries.
**Filters (only 2):** Date range, Industry.

**Key fields:**
- `date`
- `state`
- `region`
- `industry`
- `yoy_pct`

**Sheets (minimum set):**
- Region Contribution
- Top5 vs Long Tail
- State Growth Map

**Coverage note:**  
MSRS does not publish NAICS 454 (Nonstore Retail), so state-level views may show 6 industry groups.

**Views:**
1) **Growth Contribution (Stacked Bar)**
   - X: `date`
   - Y: `Growth Contribution Share`
   - Color: `region` or `industry`

2) **State Growth Map**
   - Geography: `state`
   - Color: `yoy_pct`
   - Filter: `industry`, `date`

3) **Top vs Long Tail**
   - Compare Top 5 states vs Rest of US using contribution share
   - **Important:** Do NOT filter on `SUM(State Contribution)`; it must sum to 1 each month.
   - Industry filter should be **single-select** (All Industries or one industry).

**Calculated fields (positive-only, confirmed):**
- `Positive YoY % (MSRS)`  
  - `IF [yoy_pct] > 0 THEN [yoy_pct] ELSE 0 END`
- `Growth Contribution Share (MSRS)`  
  - `SUM([Positive YoY % (MSRS)]) / WINDOW_SUM(SUM([Positive YoY % (MSRS)]))`

---

## 3) Risk & Concentration (MSRS)
**Purpose:** Track concentration risk using growth share rather than sales level.

**Default view:** last 12 months, all industries.
**Filters (only 2):** Date range, Industry.

**Key fields:**
- `date`
- `state`
- `industry`
- `yoy_pct`

**Sheets (minimum set):**
- Top5 Share Trend
- Concentration Snapshot
- Industry Share Trend

**Views:**
1) **Top N Share Trend (Line)**
   - X: `date`
   - Y: `Top N Growth Share`
   - **Important:** Do NOT filter on `SUM(State Contribution)`; it will distort shares.
   - Industry filter should be **single-select** (All Industries or one industry).

2) **Concentration Snapshot**
   - Bar or table: Top 5 / Top 10 states by growth share (latest month)
   - Use a **latest month** filter to lock the snapshot.

3) **Risk Callout (Text)**
   - Conditional text based on concentration trend direction

4) **Industry Share Trend (Line, MRTS)**
   - Data source: `marts_market_trends`
   - X: `date`
   - Y: `sales_amount / TOTAL(sales_amount)` by industry

**Latest month filter (recommended):**
- Calculated field `Is Latest`:
  - `[Date (Month)] = { MAX([Date (Month)]) }`
- Filter on `Is Latest = True` for snapshot views.

**Calculated fields (positive-only, confirmed):**
- `Top N Growth Share`  
  - Rank states by `Growth Contribution Share`, then sum Top N
- `Top Industry Growth Share`  
  - `SUM([Positive YoY % (MSRS)])` by industry / window sum

---

## Open Questions (need confirmation)
1) Do we need separate views by **industry** or only **total retail**?
2) Should seasonality heatmap use **sales level** or **YoY %**?
