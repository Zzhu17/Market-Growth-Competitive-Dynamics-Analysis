#!/usr/bin/env python
"""Transform raw MRTS/MSRS files into analysis-ready fact tables.

Outputs:
- data/processed/*.parquet (primary)
- data/published/*.csv (sharing / Tableau)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_MTRS_DIR = REPO_ROOT / "data" / "raw" / "mtrs"
RAW_MSRS_DIR = REPO_ROOT / "data" / "raw" / "msrs"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
PUBLISHED_DIR = REPO_ROOT / "data" / "published"

CROSSWALK_PATH = REPO_ROOT / "data" / "reference" / "industry_crosswalk.csv"
STATE_REGION_PATH = REPO_ROOT / "data" / "reference" / "state_region_map.csv"

DATE_START = "2022-01"
DATE_END = "2024-12"
MTRS_YEARS = [2022, 2023, 2024]


def _list_files(dir_path: Path) -> list[Path]:
    if not dir_path.exists():
        return []
    return sorted([p for p in dir_path.iterdir() if p.is_file()])


def _parse_date_col(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.to_period("M").dt.to_timestamp()


def _to_yyyymm(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.to_period("M").astype(str)


def _load_crosswalk() -> pd.DataFrame:
    if not CROSSWALK_PATH.exists():
        raise FileNotFoundError(f"missing crosswalk: {CROSSWALK_PATH}")
    return pd.read_csv(CROSSWALK_PATH, dtype=str)


def _load_state_region() -> pd.DataFrame:
    if not STATE_REGION_PATH.exists():
        raise FileNotFoundError(f"missing state map: {STATE_REGION_PATH}")
    return pd.read_csv(STATE_REGION_PATH, dtype=str)


def _map_industry(df: pd.DataFrame, naics_col: str) -> pd.DataFrame:
    crosswalk = _load_crosswalk()
    cw = crosswalk[["naics_prefix", "industry_group"]].dropna()

    def map_prefix(code: str) -> str | None:
        if code is None:
            return None
        code = str(code).strip()
        if not code:
            return None
        tokens = re.findall(r"\d{3,5}", code)
        if not tokens:
            return None
        for prefix, group in cw.itertuples(index=False):
            if prefix in ("", None):
                continue
            if "-" in prefix:
                lo, hi = prefix.split("-")
                if any(t.startswith(lo) or t.startswith(hi) for t in tokens):
                    return group
            else:
                if any(t.startswith(prefix) for t in tokens):
                    return group
        return None

    df["industry"] = df[naics_col].map(map_prefix)
    return df


def _map_region(df: pd.DataFrame, state_col: str) -> pd.DataFrame:
    state_map = _load_state_region()
    state_map["state_abbr"] = state_map["state_abbr"].str.upper().str.strip()
    state_map["state_name"] = state_map["state_name"].str.upper().str.strip()

    df[state_col] = df[state_col].astype(str).str.strip()
    df_state = df[state_col].str.upper()

    by_abbr = state_map.set_index("state_abbr")["region"]
    by_name = state_map.set_index("state_name")["region"]

    df["region"] = df_state.map(by_abbr)
    df.loc[df["region"].isna(), "region"] = df_state.map(by_name)
    return df


def _filter_months(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    df = df.copy()
    df[date_col] = _to_yyyymm(df[date_col])
    return df[(df[date_col] >= DATE_START) & (df[date_col] <= DATE_END)]


def _melt_wide_yyyy_mm(df: pd.DataFrame, id_vars: Iterable[str]) -> pd.DataFrame:
    date_cols = [c for c in df.columns if re.fullmatch(r"\d{6}", str(c))]
    if not date_cols:
        date_cols = [c for c in df.columns if re.fullmatch(r"yy\d{6}", str(c), flags=re.IGNORECASE)]
    if not date_cols:
        raise ValueError("No YYYYMM columns found for wide format.")

    long = df.melt(id_vars=list(id_vars), value_vars=date_cols, var_name="date", value_name="value")
    long["date"] = long["date"].astype(str).str.replace("yy", "", case=False, regex=False)
    long["date"] = pd.to_datetime(long["date"], format="%Y%m", errors="coerce")
    return long


def _parse_mtrs_sheet(df: pd.DataFrame, year: int) -> pd.DataFrame:
    header_idx = df[df.apply(lambda r: r.astype(str).str.contains("Jan", case=False, na=False).any(), axis=1)].index
    if header_idx.empty:
        raise ValueError(f"Unable to locate month header row for {year}")
    header_idx = header_idx[0]

    header_row = df.iloc[header_idx].tolist()
    col_names = []
    for i, val in enumerate(header_row):
        if i == 0:
            col_names.append("naics")
        elif i == 1:
            col_names.append("kind_of_business")
        else:
            col_names.append(str(val).strip())

    data = df.iloc[header_idx + 2 :].copy()
    data.columns = col_names

    month_cols = [c for c in data.columns if str(year) in str(c)]
    if not month_cols:
        raise ValueError(f"No month columns detected for {year}")

    # Keep rows with at least one numeric month value
    data[month_cols] = data[month_cols].apply(pd.to_numeric, errors="coerce")
    data = data[data[month_cols].notna().any(axis=1)]

    # Drop rows without NAICS codes (aggregates/notes)
    data = data.dropna(subset=["naics"])

    long = data.melt(id_vars=["naics", "kind_of_business"], value_vars=month_cols, var_name="date", value_name="sales_amount")
    long["date"] = long["date"].str.replace(".", "", regex=False)
    long["date"] = pd.to_datetime(long["date"], format="%b %Y", errors="coerce")
    long = _map_industry(long, "naics")
    long = long.dropna(subset=["industry"])
    long = long[["date", "industry", "sales_amount"]]
    long = long.groupby(["date", "industry"], as_index=False)["sales_amount"].sum()
    return long


def load_mtrs() -> pd.DataFrame:
    files = _list_files(RAW_MTRS_DIR)
    if not files:
        raise FileNotFoundError(f"No MRTS files found in {RAW_MTRS_DIR}")

    frames = []
    for path in files:
        if path.suffix.lower() in {".xlsx", ".xls"}:
            xls = pd.ExcelFile(path)
            for year in MTRS_YEARS:
                sheet = str(year)
                if sheet not in xls.sheet_names:
                    continue
                raw = pd.read_excel(path, sheet_name=sheet, header=None)
                frames.append(_parse_mtrs_sheet(raw, year))
        else:
            # Fallback: try CSV as long format with date + value
            raw = pd.read_csv(path)
            raw.columns = [str(c).strip() for c in raw.columns]
            date_col = next((c for c in raw.columns if c.lower() in {"date", "month"}), None)
            value_col = next((c for c in raw.columns if "sales" in c.lower() or "value" in c.lower()), None)
            naics_col = next((c for c in raw.columns if "naics" in c.lower()), None)
            if date_col and value_col:
                df = raw[[date_col, value_col] + ([naics_col] if naics_col else [])].copy()
                df.rename(columns={date_col: "date", value_col: "sales_amount"}, inplace=True)
                if naics_col:
                    df = _map_industry(df, naics_col)
                    df = df.dropna(subset=["industry"])
                else:
                    df["industry"] = "Total Retail"
                frames.append(df[["date", "industry", "sales_amount"]])

    df = pd.concat(frames, ignore_index=True)
    df = _filter_months(df, "date")
    df = df.dropna(subset=["date", "sales_amount"])
    return df


def load_msrs() -> pd.DataFrame:
    files = _list_files(RAW_MSRS_DIR)
    if not files:
        raise FileNotFoundError(f"No MSRS files found in {RAW_MSRS_DIR}")

    frames = []
    for path in files:
        df = pd.read_csv(path)
        frames.append(df)

    raw = pd.concat(frames, ignore_index=True)
    raw.columns = [str(c).strip() for c in raw.columns]

    state_col = next((c for c in raw.columns if c.lower() in {"state", "state_abbr", "stateabbr", "state_name"}), None)
    naics_col = next((c for c in raw.columns if "naics" in c.lower()), None)

    if state_col is None:
        raise ValueError("MSRS file missing state column.")

    id_vars = [state_col] + ([naics_col] if naics_col else [])
    long = _melt_wide_yyyy_mm(raw, id_vars=id_vars)
    long.rename(columns={state_col: "state", "value": "yoy_pct"}, inplace=True)
    long["yoy_pct"] = pd.to_numeric(long["yoy_pct"], errors="coerce")

    if naics_col:
        long = _map_industry(long, naics_col)
    else:
        long["industry"] = "Total Retail"

    long = _map_region(long, "state")
    long = _filter_months(long, "date")
    long = long[["date", "state", "region", "industry", "yoy_pct"]]
    long = long.dropna(subset=["date", "state", "industry", "region"])
    long = long.groupby(["date", "state", "region", "industry"], as_index=False)["yoy_pct"].mean()
    return long


def _write_outputs(df: pd.DataFrame, name: str) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)

    parquet_path = PROCESSED_DIR / f"{name}.parquet"
    csv_path = PUBLISHED_DIR / f"{name}.csv"

    df.to_parquet(parquet_path, index=False)
    df.to_csv(csv_path, index=False)

    print(f"wrote {parquet_path}")
    print(f"wrote {csv_path}")


def main() -> int:
    try:
        mtrs = load_mtrs()
        msrs = load_msrs()
    except Exception as exc:
        print(f"transform failed: {exc}", file=sys.stderr)
        return 1

    _write_outputs(mtrs, "fact_national_retail_sales")
    _write_outputs(msrs, "fact_state_retail_growth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
