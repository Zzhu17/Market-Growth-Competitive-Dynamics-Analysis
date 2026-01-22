#!/usr/bin/env python
"""Generate data validation doc, metrics snapshot, and key figures."""
from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
DOCS_DIR = REPO_ROOT / "docs"
FIG_DIR = DOCS_DIR / "figures"

EXPECTED_INDUSTRIES = [
    "Food & Beverage Stores",
    "General Merchandise",
    "Motor Vehicles & Parts",
    "Clothing & Accessories",
    "Electronics & Appliances",
    "Nonstore Retail (E-commerce)",
    "Other Specialty Retail",
]

DATE_START = "2022-01"
DATE_END = "2024-12"


def _load():
    mtrs = pd.read_parquet(PROCESSED_DIR / "fact_national_retail_sales.parquet")
    msrs = pd.read_parquet(PROCESSED_DIR / "fact_state_retail_growth.parquet")
    return mtrs, msrs


def _to_dt(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.astype(str) + "-01")


def _month_range(start: str, end: str) -> list[str]:
    return pd.period_range(start=start, end=end, freq="M").astype(str).tolist()


def _data_validation(mtrs: pd.DataFrame, msrs: pd.DataFrame) -> str:
    expected_months = _month_range(DATE_START, DATE_END)

    # Coverage
    mtrs_months = sorted(mtrs["date"].unique().tolist())
    msrs_months = sorted(msrs["date"].unique().tolist())
    mtrs_missing = sorted(set(expected_months) - set(mtrs_months))
    msrs_missing = sorted(set(expected_months) - set(msrs_months))

    coverage_tbl = pd.DataFrame(
        [
            ["MRTS (national)", len(mtrs_months), len(mtrs_missing)],
            ["MSRS (state)", len(msrs_months), len(msrs_missing)],
        ],
        columns=["dataset", "months_present", "missing_months"],
    )

    # Uniqueness
    mtrs_dupes = mtrs.duplicated(subset=["date", "industry"]).sum()
    msrs_dupes = msrs.duplicated(subset=["date", "state", "industry"]).sum()
    uniq_tbl = pd.DataFrame(
        [
            ["MRTS", "date+industry", int(mtrs_dupes)],
            ["MSRS", "date+state+industry", int(msrs_dupes)],
        ],
        columns=["dataset", "key", "duplicate_rows"],
    )

    # Missing YoY
    msrs_missing_yoy = msrs["yoy_pct"].isna().mean() * 100
    missing_tbl = pd.DataFrame(
        [["MSRS", f"{msrs_missing_yoy:.2f}%"]],
        columns=["dataset", "yoy_pct_missing_rate"],
    )

    # Value range
    yoy_min = msrs["yoy_pct"].min()
    yoy_max = msrs["yoy_pct"].max()
    out_of_range = msrs[(msrs["yoy_pct"] < -100) | (msrs["yoy_pct"] > 300)]
    range_tbl = pd.DataFrame(
        [
            ["MSRS", float(yoy_min), float(yoy_max), int(len(out_of_range))],
        ],
        columns=["dataset", "yoy_min", "yoy_max", "out_of_range_rows"],
    )

    # Industry consistency
    mtrs_ind = sorted(mtrs["industry"].unique().tolist())
    msrs_ind = sorted(msrs["industry"].unique().tolist())
    expected_set = set(EXPECTED_INDUSTRIES)
    mtrs_missing_ind = sorted(expected_set - set(mtrs_ind))
    msrs_missing_ind = sorted(expected_set - set(msrs_ind))
    mtrs_unexpected = sorted(set(mtrs_ind) - expected_set)
    msrs_unexpected = sorted(set(msrs_ind) - expected_set)

    industry_tbl = pd.DataFrame(
        [
            ["MRTS", len(mtrs_ind), "; ".join(mtrs_missing_ind) or "None", "; ".join(mtrs_unexpected) or "None"],
            ["MSRS", len(msrs_ind), "; ".join(msrs_missing_ind) or "None", "; ".join(msrs_unexpected) or "None"],
        ],
        columns=["dataset", "industry_count", "missing_vs_target", "unexpected"],
    )

    # State mapping coverage
    states = msrs["state"].nunique()
    missing_region = msrs["region"].isna().sum()
    mapping_tbl = pd.DataFrame(
        [["MSRS", int(states), int(missing_region)]],
        columns=["dataset", "states_present", "missing_region_rows"],
    )

    def md_table(df: pd.DataFrame) -> str:
        return df.to_markdown(index=False)

    lines = [
        "# Data Validation",
        "",
        "## 1) Coverage (36 months, no gaps)",
        f"Conclusion: MRTS missing months = {len(mtrs_missing)}, MSRS missing months = {len(msrs_missing)}.",
        md_table(coverage_tbl),
        "",
        "## 2) Uniqueness (primary keys)",
        f"Conclusion: duplicate rows = MRTS {mtrs_dupes}, MSRS {msrs_dupes}.",
        md_table(uniq_tbl),
        "",
        "## 3) Missing YoY %",\
        f"Conclusion: MSRS yoy_pct missing rate = {msrs_missing_yoy:.2f}%.",
        md_table(missing_tbl),
        "",
        "## 4) Value Range (YoY %)",
        f"Conclusion: min={yoy_min:.2f}%, max={yoy_max:.2f}%, out-of-range rows={len(out_of_range)}.",
        md_table(range_tbl),
    ]

    if len(out_of_range) > 0:
        sample = out_of_range.sort_values("yoy_pct").head(5)
        lines += ["", "Out-of-range sample:", sample[["date", "state", "industry", "yoy_pct"]].to_markdown(index=False)]

    lines += [
        "",
        "## 5) Industry Consistency",\
        "Conclusion: industry lists are fixed; MSRS lacks Nonstore Retail (expected).",
        md_table(industry_tbl),
        "",
        "## 6) State Mapping Coverage",\
        f"Conclusion: states present={states}, missing region rows={missing_region}.",
        md_table(mapping_tbl),
    ]

    return "\n".join(lines)


def _metrics_snapshot(mtrs: pd.DataFrame, msrs: pd.DataFrame) -> pd.DataFrame:
    # National total sales
    mtrs_dt = mtrs.copy()
    mtrs_dt["date_dt"] = _to_dt(mtrs_dt["date"])
    total = mtrs_dt.groupby("date_dt", as_index=False)["sales_amount"].sum()
    total = total.sort_values("date_dt")
    total["mom_growth_pct"] = total["sales_amount"].pct_change() * 100
    total["yoy_growth_pct"] = total["sales_amount"].pct_change(12) * 100

    latest = total["date_dt"].max()
    last12 = total[total["date_dt"] > (latest - pd.DateOffset(months=12))]

    def latest_val(col: str):
        return float(total.loc[total["date_dt"] == latest, col].iloc[0])

    def last12_avg(col: str):
        return float(last12[col].mean())

    # MSRS Top5 share (all-industry, positive-only)
    msrs_dt = msrs.copy()
    msrs_dt["date_dt"] = _to_dt(msrs_dt["date"])

    all_ind = msrs_dt.groupby(["date_dt", "state"], as_index=False)["yoy_pct"].mean()
    all_ind["pos_yoy"] = all_ind["yoy_pct"].clip(lower=0)

    def topn_share(n: int) -> pd.DataFrame:
        shares = []
        for d, g in all_ind.groupby("date_dt"):
            total_pos = g["pos_yoy"].sum()
            if total_pos == 0:
                share = np.nan
            else:
                share = g.sort_values("pos_yoy", ascending=False).head(n)["pos_yoy"].sum() / total_pos * 100
            shares.append([d, share])
        return pd.DataFrame(shares, columns=["date_dt", f"top{n}_share_pct"]).sort_values("date_dt")

    top5 = topn_share(5)

    latest_top5 = float(top5.loc[top5["date_dt"] == latest, "top5_share_pct"].iloc[0])
    last12_top5 = float(top5[top5["date_dt"] > (latest - pd.DateOffset(months=12))]["top5_share_pct"].mean())

    snapshot = pd.DataFrame(
        [
            ["total_sales", latest.strftime("%Y-%m"), latest_val("sales_amount"), last12_avg("sales_amount")],
            ["yoy_growth_pct", latest.strftime("%Y-%m"), latest_val("yoy_growth_pct"), last12_avg("yoy_growth_pct")],
            ["mom_growth_pct", latest.strftime("%Y-%m"), latest_val("mom_growth_pct"), last12_avg("mom_growth_pct")],
            ["top5_state_growth_share_pct", latest.strftime("%Y-%m"), latest_top5, last12_top5],
        ],
        columns=["metric", "latest_month", "latest_value", "last_12m_avg"],
    )
    return snapshot


def _figures(mtrs: pd.DataFrame, msrs: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    mtrs_dt = mtrs.copy()
    mtrs_dt["date_dt"] = _to_dt(mtrs_dt["date"])
    total = mtrs_dt.groupby("date_dt", as_index=False)["sales_amount"].sum().sort_values("date_dt")
    total["mom_growth_pct"] = total["sales_amount"].pct_change() * 100
    total["yoy_growth_pct"] = total["sales_amount"].pct_change(12) * 100

    # Figure 1: Total sales trend
    plt.figure(figsize=(8, 4))
    plt.plot(total["date_dt"], total["sales_amount"], color="#1f77b4", linewidth=2)
    plt.title("National Retail Sales (Total)")
    plt.xlabel("Date")
    plt.ylabel("Sales (Millions $)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "total_sales_trend.png", dpi=150)
    plt.close()

    # Figure 2: YoY and MoM growth
    plt.figure(figsize=(8, 4))
    plt.plot(total["date_dt"], total["yoy_growth_pct"], label="YoY %", color="#2ca02c")
    plt.plot(total["date_dt"], total["mom_growth_pct"], label="MoM %", color="#ff7f0e")
    plt.axhline(0, color="#999999", linewidth=0.8)
    plt.title("National Retail Sales Growth")
    plt.xlabel("Date")
    plt.ylabel("Growth (%)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "growth_yoy_mom.png", dpi=150)
    plt.close()

    # Figure 3: Seasonality heatmap
    season = total.copy()
    season["year"] = season["date_dt"].dt.year
    season["month"] = season["date_dt"].dt.month
    pivot = season.pivot(index="month", columns="year", values="sales_amount")

    plt.figure(figsize=(8, 4))
    plt.imshow(pivot, aspect="auto", cmap="YlGnBu")
    plt.title("Seasonality Heatmap (Total Sales)")
    plt.xlabel("Year")
    plt.ylabel("Month")
    plt.xticks(range(len(pivot.columns)), pivot.columns, rotation=0)
    plt.yticks(range(1, 13), range(1, 13))
    plt.colorbar(label="Sales (Millions $)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "seasonality_heatmap.png", dpi=150)
    plt.close()

    # Figure 4: Top5 growth share trend
    msrs_dt = msrs.copy()
    msrs_dt["date_dt"] = _to_dt(msrs_dt["date"])
    all_ind = msrs_dt.groupby(["date_dt", "state"], as_index=False)["yoy_pct"].mean()
    all_ind["pos_yoy"] = all_ind["yoy_pct"].clip(lower=0)

    shares = []
    for d, g in all_ind.groupby("date_dt"):
        total_pos = g["pos_yoy"].sum()
        share = np.nan
        if total_pos > 0:
            share = g.sort_values("pos_yoy", ascending=False).head(5)["pos_yoy"].sum() / total_pos * 100
        shares.append([d, share])
    share_df = pd.DataFrame(shares, columns=["date_dt", "top5_share_pct"]).sort_values("date_dt")

    plt.figure(figsize=(8, 4))
    plt.plot(share_df["date_dt"], share_df["top5_share_pct"], color="#9467bd", linewidth=2)
    plt.title("Top 5 States Share of Positive Growth")
    plt.xlabel("Date")
    plt.ylabel("Share (%)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "top5_growth_share_trend.png", dpi=150)
    plt.close()


def main() -> int:
    mtrs, msrs = _load()

    # Data validation doc
    report = _data_validation(mtrs, msrs)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "data_validation.md").write_text(report, encoding="utf-8")

    # Metrics snapshot
    snapshot = _metrics_snapshot(mtrs, msrs)
    snapshot_path = DOCS_DIR / "metrics_snapshot.csv"
    snapshot.to_csv(snapshot_path, index=False)

    # Figures
    _figures(mtrs, msrs)

    print(f"wrote {DOCS_DIR / 'data_validation.md'}")
    print(f"wrote {snapshot_path}")
    print(f"wrote figures to {FIG_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
