"""
Connects review sentiment to RFM segment, churn status, and revenue —
so sentiment analysis is tied directly to business outcomes rather than
sitting in isolation.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
from src.database.db_connection import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)

CHURN_THRESHOLD_DAYS = 90  # must match src/features/churn_features.py


def analyze_sentiment_business_link() -> pd.DataFrame:
    engine = get_engine()

    sentiment = pd.read_sql(
        "SELECT customer_id, sentiment_score FROM review_sentiment", engine
    )
    rfm = pd.read_sql(
        "SELECT customer_id, segment, monetary, frequency, recency_days FROM customer_rfm",
        engine,
    )

    # Average sentiment per customer (some customers left multiple reviews)
    customer_sentiment = (
        sentiment.groupby("customer_id")["sentiment_score"].mean().reset_index()
    )
    customer_sentiment.columns = ["customer_id", "avg_sentiment_score"]

    merged = rfm.merge(customer_sentiment, on="customer_id", how="inner")
    merged["churned"] = (merged["recency_days"] > CHURN_THRESHOLD_DAYS).astype(int)

    by_segment = merged.groupby("segment")["avg_sentiment_score"].mean().sort_values(ascending=False)
    logger.info(f"Average sentiment by RFM segment:\n{by_segment}")

    by_churn = merged.groupby("churned")["avg_sentiment_score"].mean()
    logger.info(f"Average sentiment by churn status (0=active, 1=churned):\n{by_churn}")

    corr_monetary = merged["avg_sentiment_score"].corr(merged["monetary"])
    corr_frequency = merged["avg_sentiment_score"].corr(merged["frequency"])
    logger.info(f"Correlation - sentiment vs monetary value: {corr_monetary:.3f}")
    logger.info(f"Correlation - sentiment vs order frequency (repeat purchases): {corr_frequency:.3f}")

    merged.to_sql("sentiment_business_link", engine, if_exists="replace", index=False)
    logger.info("Saved sentiment_business_link table")

    return merged


if __name__ == "__main__":
    analyze_sentiment_business_link()