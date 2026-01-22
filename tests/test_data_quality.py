from pathlib import Path
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MTRS_PATH = REPO_ROOT / "data" / "processed" / "fact_national_retail_sales.parquet"
MSRS_PATH = REPO_ROOT / "data" / "processed" / "fact_state_retail_growth.parquet"

EXPECTED_MONTHS = pd.period_range("2022-01", "2024-12", freq="M").astype(str).tolist()
EXPECTED_INDUSTRIES = {
    "Food & Beverage Stores",
    "General Merchandise",
    "Motor Vehicles & Parts",
    "Clothing & Accessories",
    "Electronics & Appliances",
    "Nonstore Retail (E-commerce)",
    "Other Specialty Retail",
}


def _skip_if_missing():
    if not MTRS_PATH.exists() or not MSRS_PATH.exists():
        pytest.skip("Processed fact tables not found. Run scripts/run_pipeline.sh")


def test_coverage_months():
    _skip_if_missing()
    mtrs = pd.read_parquet(MTRS_PATH)
    msrs = pd.read_parquet(MSRS_PATH)

    assert sorted(mtrs["date"].unique().tolist()) == EXPECTED_MONTHS
    assert sorted(msrs["date"].unique().tolist()) == EXPECTED_MONTHS


def test_uniqueness_keys():
    _skip_if_missing()
    mtrs = pd.read_parquet(MTRS_PATH)
    msrs = pd.read_parquet(MSRS_PATH)

    assert mtrs.duplicated(subset=["date", "industry"]).sum() == 0
    assert msrs.duplicated(subset=["date", "state", "industry"]).sum() == 0


def test_yoy_range():
    _skip_if_missing()
    msrs = pd.read_parquet(MSRS_PATH)
    out_of_range = msrs[(msrs["yoy_pct"] < -100) | (msrs["yoy_pct"] > 300)]
    assert len(out_of_range) == 0


def test_industry_set():
    _skip_if_missing()
    mtrs = pd.read_parquet(MTRS_PATH)
    msrs = pd.read_parquet(MSRS_PATH)

    assert set(mtrs["industry"].unique()) == EXPECTED_INDUSTRIES
    # MSRS lacks Nonstore Retail (expected)
    assert set(msrs["industry"].unique()).issubset(EXPECTED_INDUSTRIES)
