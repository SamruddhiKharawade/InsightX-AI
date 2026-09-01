"""
RFM (Recency, Frequency, Monetary) customer segmentation.

Computes each customer's RFM values from the orders table, scores them
into quintiles, assigns a business-readable segment, and saves the result
to both the database (table: customer_rfm) and data/processed/customer_rfm.csv.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
from config.settings import PROCESSED_DATA_DIR
from src.database.db_connection import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)


def compute_rfm(orders: pd.DataFrame) -> pd.DataFrame:
    """Compute raw Recency, Frequency, Monetary values per customer."""
    orders = orders.copy()
    orders["order_date"] = pd.to_datetime(orders["order_date"])

    reference_date = orders["order_date"].max() + pd.Timedelta(days=1)

    rfm = orders.groupby("customer_id").agg(
        recency_days=("order_date", lambda x: (reference_date - x.max()).days),
        frequency=("order_id", "count"),
        monetary=("revenue", "sum"),
    ).reset_index()

    return rfm


def score_rfm(rfm: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw RFM values into 1-5 quintile scores.
    Recency is reverse-scored: fewer days since last order = higher score.
    """
    rfm = rfm.copy()

    # duplicates="drop" handles cases where many customers share identical
    # values, which would otherwise make qcut unable to form 5 distinct bins
    rfm["r_score"] = pd.qcut(rfm["recency_days"], 5, labels=[5, 4, 3, 2, 1], duplicates="drop").astype(int)
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"], 5, labels=[1, 2, 3, 4, 5], duplicates="drop").astype(int)

    rfm["rfm_score"] = rfm["r_score"].astype(str) + rfm["f_score"].astype(str) + rfm["m_score"].astype(str)

    return rfm


def assign_segment(row) -> str:
    r, f = row["r_score"], row["f_score"]

    if r >= 4 and f >= 4:
        return "Champions"
    if r >= 3 and f >= 4:
        return "Loyal Customers"
    if r >= 4 and 2 <= f <= 3:
        return "Potential Loyalists"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f <= 2:
        return "Lost"
    return "Needs Attention"


def segment_customers(rfm: pd.DataFrame) -> pd.DataFrame:
    rfm = rfm.copy()
    rfm["segment"] = rfm.apply(assign_segment, axis=1)
    return rfm


def run_rfm_pipeline():
    engine = get_engine()
    orders = pd.read_sql("SELECT * FROM orders WHERE status = 'Delivered'", engine)

    rfm = compute_rfm(orders)
    rfm = score_rfm(rfm)
    rfm = segment_customers(rfm)

    # Save to database — if_exists="replace" is correct here because this
    # is a DERIVED/computed table, safe to fully regenerate each run,
    # unlike the raw tables in Phase 6 which we only ever appended to once.
    rfm.to_sql("customer_rfm", engine, if_exists="replace", index=False)
    logger.info(f"Saved customer_rfm table: {len(rfm)} customers")

    output_path = PROCESSED_DATA_DIR / "customer_rfm.csv"
    rfm.to_csv(output_path, index=False)
    logger.info(f"Saved {output_path}")

    segment_counts = rfm["segment"].value_counts()
    logger.info(f"Segment distribution:\n{segment_counts}")

    return rfm


if __name__ == "__main__":
    run_rfm_pipeline()
    logger.info("RFM analysis completed successfully.")