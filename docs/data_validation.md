# Data Validation

## 1) Coverage (36 months, no gaps)
Conclusion: MRTS missing months = 0, MSRS missing months = 0.
| dataset         |   months_present |   missing_months |
|:----------------|-----------------:|-----------------:|
| MRTS (national) |               36 |                0 |
| MSRS (state)    |               36 |                0 |

## 2) Uniqueness (primary keys)
Conclusion: duplicate rows = MRTS 0, MSRS 0.
| dataset   | key                 |   duplicate_rows |
|:----------|:--------------------|-----------------:|
| MRTS      | date+industry       |                0 |
| MSRS      | date+state+industry |                0 |

## 3) Missing YoY %
Conclusion: MSRS yoy_pct missing rate = 0.56%.
| dataset   | yoy_pct_missing_rate   |
|:----------|:-----------------------|
| MSRS      | 0.56%                  |

## 4) Value Range (YoY %)
Conclusion: min=-31.40%, max=38.60%, out-of-range rows=0.
| dataset   |   yoy_min |   yoy_max |   out_of_range_rows |
|:----------|----------:|----------:|--------------------:|
| MSRS      |     -31.4 |      38.6 |                   0 |

## 5) Industry Consistency
Conclusion: industry lists are fixed; MSRS lacks Nonstore Retail (expected).
| dataset   |   industry_count | missing_vs_target            | unexpected   |
|:----------|-----------------:|:-----------------------------|:-------------|
| MRTS      |                7 | None                         | None         |
| MSRS      |                6 | Nonstore Retail (E-commerce) | None         |

## 6) State Mapping Coverage
Conclusion: states present=51, missing region rows=0.
| dataset   |   states_present |   missing_region_rows |
|:----------|-----------------:|----------------------:|
| MSRS      |               51 |                     0 |