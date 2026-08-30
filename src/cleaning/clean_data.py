"""
Cleaning layer — fixes data quality issues in each raw table and adds
calculated columns the rest of the project depends on. Reads validated
raw data via the ingestion layer, writes cleaned data to data/processed/.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pandas as pd
from config.settings import PROCESSED_DATA_DIR
from src.ingestion.load_raw_data import load_all_raw_data
from src.utils.logger import get_logger

logger = get_logger(__name__)


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"customers: removed {before - len(df)} duplicate rows")

    # Standardize city text: trim whitespace, Title Case
    df["city"] = df["city"].str.strip().str.title()

    # Fill missing age with the median age (keeps the row usable)
    median_age = df["age"].median()
    n_missing_age = df["age"].isna().sum()
    df["age"] = df["age"].fillna(median_age)
    logger.info(f"customers: filled {n_missing_age} missing ages with median ({median_age})")

    # Fill missing gender with "Unknown" rather than guessing
    n_missing_gender = df["gender"].isna().sum()
    df["gender"] = df["gender"].fillna("Unknown")
    logger.info(f"customers: filled {n_missing_gender} missing genders with 'Unknown'")

    # Fix data type: signup_date should be a real date, not text
    df["signup_date"] = pd.to_datetime(df["signup_date"])

    # Calculated column: tenure in days, measured from the latest signup
    # date in the dataset (our data is historical, so "today" isn't meaningful)
    reference_date = df["signup_date"].max()
    df["tenure_days"] = (reference_date - df["signup_date"]).dt.days

    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"products: removed {before - len(df)} duplicate rows")

    # Negative inventory is impossible — treat as missing, then fill
    df.loc[df["inventory"] < 0, "inventory"] = np.nan
    median_inventory = df["inventory"].median()
    n_missing = df["inventory"].isna().sum()
    df["inventory"] = df["inventory"].fillna(median_inventory).astype(int)
    logger.info(f"products: fixed {n_missing} missing/invalid inventory values")

    # Calculated columns: profit margin, in absolute and percentage terms
    df["profit_margin"] = df["selling_price"] - df["cost"]
    df["margin_pct"] = (df["profit_margin"] / df["selling_price"]).round(3)

    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"orders: removed {before - len(df)} duplicate rows")

    # Remove impossible rows: negative quantity, zero/negative price
    before = len(df)
    df = df[(df["quantity"] > 0) & (df["price"] > 0)]
    logger.info(f"orders: removed {before - len(df)} rows with impossible quantity/price")

    # Standardize payment_method text casing
    df["payment_method"] = df["payment_method"].str.strip().str.title()

    # Fill missing delivery_time with the median
    median_delivery = df["delivery_time"].median()
    n_missing = df["delivery_time"].isna().sum()
    df["delivery_time"] = df["delivery_time"].fillna(median_delivery)
    logger.info(f"orders: filled {n_missing} missing delivery_time values with median")

    # Fix data type
    df["order_date"] = pd.to_datetime(df["order_date"])

    # Calculated column: actual revenue after discount
    df["revenue"] = (df["price"] * df["quantity"] * (1 - df["discount"])).round(2)

    return df


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"reviews: removed {before - len(df)} duplicate rows")

    n_missing_text = df["review_text"].isna().sum()
    df["review_text"] = df["review_text"].fillna("No review text provided")
    logger.info(f"reviews: filled {n_missing_text} missing review_text values")

    df["review_date"] = pd.to_datetime(df["review_date"])

    return df


def clean_marketing(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    logger.info(f"marketing: removed {before - len(df)} duplicate rows")

    median_spend = df["spend"].median()
    n_missing = df["spend"].isna().sum()
    df["spend"] = df["spend"].fillna(median_spend)
    logger.info(f"marketing: filled {n_missing} missing spend values with median")

    return df


def run_cleaning_pipeline():
    raw = load_all_raw_data()

    cleaned = {
        "customers": clean_customers(raw["customers"]),
        "products": clean_products(raw["products"]),
        "orders": clean_orders(raw["orders"]),
        "reviews": clean_reviews(raw["reviews"]),
        "marketing": clean_marketing(raw["marketing"]),
    }

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name, df in cleaned.items():
        output_path = PROCESSED_DATA_DIR / f"{name}.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned {name}: {len(df)} rows -> {output_path}")

    return cleaned


if __name__ == "__main__":
    run_cleaning_pipeline()
    logger.info("Cleaning pipeline completed successfully.")