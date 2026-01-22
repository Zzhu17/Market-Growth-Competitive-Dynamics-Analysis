# Growth Contribution Methodology (Audit Note)

**Definition (positive-only):** For each period, convert YoY% to `pos_yoy = max(yoy_pct, 0)` and compute contribution as `pos_yoy / sum(pos_yoy)` within the same **date + industry** group. This ensures contributions reflect **sources of expansion**, not contraction.

**Why not signed normalization:** Using `yoy_pct / sum(yoy_pct)` can produce unstable or misleading shares when negative growth is large or the denominator is near zero. It can also inflate contributions from growing states when others are contracting.

**Bias note:** Positive-only normalization **understates the impact of contracting states/industries**. It is designed for growth‑driver narratives, not net‑growth attribution.

**Sensitivity check (All‑industry, Dec 2024):**
| metric | positive-only | signed | note |
|:--|--:|--:|:--|
| Top 5 states share of growth | **28.0%** | **32.1%** | signed denominator is smaller due to negative growth |
| Top 5 overlap | **5 / 5** | **5 / 5** | same Top 5 set |
| Contribution correlation | **0.97** | **0.97** | ranking stable |

**Conclusion:** Positive-only vs signed changes absolute share levels, but **top contributors and rankings remain stable** in this sample.
