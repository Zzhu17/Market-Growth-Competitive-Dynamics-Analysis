# Data Dictionary

## fact_national_retail_sales
Source: MRTS (national level). Unit: **millions of dollars**.

| field | type | nullable | description | source/logic |
|:--|:--|:--|:--|:--|
| date | string (YYYY-MM) | no | Month of observation | MRTS sheet month column |
| industry | string | no | Analysis industry group | `data/reference/industry_crosswalk.csv` |
| sales_amount | float | no | National monthly sales level | MRTS (not seasonally adjusted) |

## fact_state_retail_growth
Source: MSRS (state YoY %). Unit: **percent**.

| field | type | nullable | description | source/logic |
|:--|:--|:--|:--|:--|
| date | string (YYYY-MM) | no | Month of observation | MSRS `yyYYYYMM` columns |
| state | string | no | State abbreviation (2‑letter) | MSRS `stateabbr` |
| region | string | no | Census region | `data/reference/state_region_map.csv` |
| industry | string | no | Analysis industry group | `data/reference/industry_crosswalk.csv` |
| yoy_pct | float | yes | State YoY % change | MSRS `yyYYYYMM`; averaged when multiple NAICS map to one group |

## marts_market_trends
Derived from `fact_national_retail_sales` for Tableau.

| field | type | nullable | description | source/logic |
|:--|:--|:--|:--|:--|
| date | string (YYYY-MM) | no | Month of observation | passthrough |
| industry | string | no | Analysis industry group | passthrough |
| sales_amount | float | no | National monthly sales level | passthrough |
| mom_growth_pct | float | yes | Month‑over‑month growth % | `sales_amount / lag(1) - 1` |
| yoy_growth_pct | float | yes | Year‑over‑year growth % | `sales_amount / lag(12) - 1` |
| sales_index | float | no | Index base=100 at first month | `sales_amount / first_value * 100` |

## marts_growth_contribution
Derived from `fact_state_retail_growth` for Tableau.

| field | type | nullable | description | source/logic |
|:--|:--|:--|:--|:--|
| date | string (YYYY-MM) | no | Month of observation | passthrough |
| region | string | no | Census region | passthrough |
| state | string | no | State abbreviation | passthrough |
| industry | string | no | Analysis industry group or “All Industries” | computed | 
| yoy_pct | float | yes | State YoY % change | passthrough |
| pos_yoy | float | no | Positive‑only YoY % | `max(yoy_pct, 0)` |
| state_contribution | float | yes | Share of positive growth | `pos_yoy / sum(pos_yoy)` by date+industry |
| region_contribution | float | yes | Region share of positive growth | sum(pos_yoy) by date+industry+region / sum(pos_yoy) |
| topN_flag | string | no | Top5 / Top10 / Other | rank by `pos_yoy` |

## metrics_snapshot
Summary KPIs for README.

| field | type | nullable | description | source/logic |
|:--|:--|:--|:--|:--|
| metric | string | no | Metric name | predefined list |
| latest_month | string (YYYY-MM) | no | Latest month in data | computed |
| latest_value | float | no | Metric value for latest month | computed |
| last_12m_avg | float | yes | 12‑month average | computed |
