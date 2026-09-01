"""
Anomaly detection on daily business metrics using two complementary methods:
1. Statistical thresholds (z-scores) - simple, explainable, single-metric
2. Isolation Forest - unsupervised ML, catches multivariate anomalies that
   single-metric thresholds might miss

Both methods are checked against the anomaly month deliberately injected
in Phase 3 (November 2024, inflated order prices) as a sanity test.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.database.db_connection import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_daily_metrics() -> pd.DataFrame:
    engine = get_engine()
    orders = pd.read_sql("SELECT order_date, status, revenue, delivery_time FROM orders", engine)
    orders["order_date"] = pd.to_datetime(orders["order_date"])

    delivered = orders[orders["status"] == "Delivered"]

    daily_revenue = delivered.groupby("order_date")["revenue"].sum()
    daily_orders = orders.groupby("order_date").size()
    daily_avg_delivery = delivered.groupby("order_date")["delivery_time"].mean()

    cancelled_or_returned = (
        orders[orders["status"].isin(["Cancelled", "Returned"])].groupby("order_date").size()
    )
    daily_cancel_rate = (cancelled_or_returned / daily_orders).fillna(0)

    daily = pd.DataFrame({
        "daily_revenue": daily_revenue,
        "daily_orders": daily_orders,
        "daily_avg_delivery_time": daily_avg_delivery,
        "daily_cancel_rate": daily_cancel_rate,
    })
    daily = daily.asfreq("D", fill_value=0).reset_index().rename(columns={"index": "order_date"})

    return daily


def detect_statistical_anomalies(daily: pd.DataFrame, metric: str):
    mean = daily[metric].mean()
    std = daily[metric].std()

    daily[f"{metric}_zscore"] = (daily[metric] - mean) / std
    daily[f"{metric}_anomaly"] = "Normal"
    daily.loc[daily[f"{metric}_zscore"].abs() > 3, f"{metric}_anomaly"] = "HIGH"
    daily.loc[daily[f"{metric}_zscore"].abs().between(2, 3), f"{metric}_anomaly"] = "MEDIUM"

    return daily, mean, std


def detect_isolation_forest_anomalies(daily: pd.DataFrame) -> pd.DataFrame:
    features = daily[["daily_revenue", "daily_orders", "daily_avg_delivery_time", "daily_cancel_rate"]]
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    iso_forest = IsolationForest(contamination=0.05, random_state=42)
    flags = iso_forest.fit_predict(features_scaled)
    daily["isolation_forest_flag"] = pd.Series(flags).map({1: "Normal", -1: "Anomaly"})

    return daily


def print_alert(row, metric, mean, std):
    label = metric.replace("_", " ").title()
    lower, upper = mean - 2 * std, mean + 2 * std
    print(f"\n\U0001F6A8 ANOMALY DETECTED")
    print(f"Metric: {label}")
    print(f"Date: {row['order_date'].date()}")
    print(f"Expected: {lower:,.0f} - {upper:,.0f}")
    print(f"Actual: {row[metric]:,.0f}")
    print(f"Severity: {row[f'{metric}_anomaly']}")


def run_anomaly_detection() -> pd.DataFrame:
    daily = build_daily_metrics()

    stats_summary = {}
    for metric in ["daily_revenue", "daily_orders", "daily_avg_delivery_time", "daily_cancel_rate"]:
        daily, mean, std = detect_statistical_anomalies(daily, metric)
        stats_summary[metric] = (mean, std)

    daily = detect_isolation_forest_anomalies(daily)

    high_alerts = daily[daily["daily_revenue_anomaly"] == "HIGH"]
    for _, row in high_alerts.iterrows():
        print_alert(row, "daily_revenue", *stats_summary["daily_revenue"])

    # Sanity check: was the Phase 3 injected November 2024 anomaly caught?
    nov_2024 = daily[(daily["order_date"].dt.year == 2024) & (daily["order_date"].dt.month == 11)]
    caught_statistical = nov_2024["daily_revenue_anomaly"].isin(["MEDIUM", "HIGH"]).any()
    caught_isolation = (nov_2024["isolation_forest_flag"] == "Anomaly").any()
    logger.info(
        f"Injected Nov 2024 anomaly caught -> Statistical: {caught_statistical} | "
        f"Isolation Forest: {caught_isolation}"
    )

    engine = get_engine()
    daily.to_sql("daily_anomalies", engine, if_exists="replace", index=False)
    logger.info(f"Saved daily_anomalies table: {len(daily)} days")

    return daily


if __name__ == "__main__":
    run_anomaly_detection()