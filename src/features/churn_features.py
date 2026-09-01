"""
Builds the customer-level feature table used for churn prediction.

IMPORTANT - Data leakage: recency_days is used to DEFINE the churn label
itself, so it is intentionally EXCLUDED from the feature set. Including it
would let the model "cheat" with a trivial threshold rule instead of
learning genuine behavioral patterns.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
from src.database.db_connection import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)

CHURN_THRESHOLD_DAYS = 90


def build_churn_features() -> pd.DataFrame:
    engine = get_engine()

    customers = pd.read_sql("SELECT * FROM customers", engine)
    rfm = pd.read_sql("SELECT customer_id, recency_days, frequency, monetary FROM customer_rfm", engine)
    orders = pd.read_sql("SELECT * FROM orders WHERE status = 'Delivered'", engine)
    reviews = pd.read_sql("SELECT * FROM reviews", engine)
    marketing = pd.read_sql("SELECT * FROM marketing_campaigns", engine)

    # Define the label here, then DROP recency_days before returning features
    rfm["churned"] = (rfm["recency_days"] > CHURN_THRESHOLD_DAYS).astype(int)

    # Order-level behavioral features (legitimate: don't directly encode recency)
    order_features = orders.groupby("customer_id").agg(
        avg_order_value=("revenue", "mean"),
        avg_discount_used=("discount", "mean"),
        avg_delivery_time=("delivery_time", "mean"),
        preferred_payment_method=(
            "payment_method", lambda x: x.mode()[0] if not x.mode().empty else "Unknown"
        ),
    ).reset_index()

    review_features = reviews.groupby("customer_id").agg(
        avg_rating=("rating", "mean"),
        review_count=("review_id", "count"),
    ).reset_index()

    marketing_features = marketing.groupby("customer_id").agg(
        campaigns_targeted=("campaign_id", "count"),
        total_marketing_spend=("spend", "sum"),
        total_conversions=("conversion", "sum"),
    ).reset_index()

    df = customers.merge(
        rfm[["customer_id", "frequency", "monetary", "churned"]], on="customer_id", how="inner"
    )
    df = df.merge(order_features, on="customer_id", how="left")
    df = df.merge(review_features, on="customer_id", how="left")
    df = df.merge(marketing_features, on="customer_id", how="left")

    # Customers with no reviews or no marketing touches get 0, not NaN —
    # "zero engagement" is meaningfully different from "missing data" here
    fill_zero_cols = ["avg_rating", "review_count", "campaigns_targeted",
                       "total_marketing_spend", "total_conversions"]
    df[fill_zero_cols] = df[fill_zero_cols].fillna(0)

    logger.info(
        f"Built churn feature table: {len(df)} customers, "
        f"{df['churned'].mean():.1%} churn rate"
    )
    return df


if __name__ == "__main__":
    df = build_churn_features()
    print(df.head())
    print(df["churned"].value_counts())