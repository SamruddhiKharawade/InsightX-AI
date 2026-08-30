"""
Ingestion layer — responsible ONLY for reading raw CSV files into pandas
DataFrames and validating their basic structure (file exists, not empty,
expected columns present). It does NOT fix data problems — that happens
in the Cleaning phase (Phase 5).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
from config.settings import RAW_DATA_DIR, EXPECTED_SCHEMAS
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_csv(table_name: str) -> pd.DataFrame:
    """
    Load one raw CSV file by table name (e.g. "customers") and validate
    that it exists, is non-empty, and has all expected columns.
    """
    file_path = RAW_DATA_DIR / f"{table_name}.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Expected raw file not found: {file_path}. "
            f"Did you run scripts/generate_synthetic_data.py?"
        )

    df = pd.read_csv(file_path)

    if df.empty:
        raise ValueError(f"{table_name}.csv was loaded but contains zero rows.")

    expected_columns = set(EXPECTED_SCHEMAS[table_name])
    actual_columns = set(df.columns)
    missing = expected_columns - actual_columns

    if missing:
        raise ValueError(f"{table_name}.csv is missing expected columns: {missing}")

    logger.info(f"Loaded {table_name}: {len(df)} rows, {len(df.columns)} columns")
    return df


def load_all_raw_data() -> dict:
    """
    Load every raw table and return a dictionary of {table_name: DataFrame},
    so other scripts can do:
        data = load_all_raw_data()
        customers = data["customers"]
    """
    data = {}
    for table_name in EXPECTED_SCHEMAS:
        data[table_name] = load_csv(table_name)
    return data


if __name__ == "__main__":
    all_data = load_all_raw_data()
    logger.info("All raw tables loaded and validated successfully.")
    for name, df in all_data.items():
        print(f"\n--- {name} ---")
        print(df.head(3))