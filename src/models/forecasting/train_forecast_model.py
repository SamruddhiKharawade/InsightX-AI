"""
Sales forecasting: builds a daily revenue time series, evaluates a Prophet
model against a simple baseline using a holdout period, then trains on the
full dataset to produce a genuine 90-day-ahead forecast.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

import joblib
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.database.db_connection import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_DIR = Path(__file__).resolve().parent
HOLDOUT_DAYS = 60


def get_daily_revenue_series() -> pd.DataFrame:
    engine = get_engine()
    orders = pd.read_sql(
        "SELECT order_date, revenue FROM orders WHERE status = 'Delivered'", engine
    )
    orders["order_date"] = pd.to_datetime(orders["order_date"])

    daily = orders.groupby("order_date")["revenue"].sum()
    daily = daily.asfreq("D", fill_value=0)  # fill days with no orders as 0 revenue
    daily = daily.reset_index()
    daily.columns = ["ds", "y"]
    return daily


def evaluate_forecast(actual: pd.Series, predicted, label: str) -> dict:
    mae = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    # Avoid divide-by-zero on any day with genuinely zero actual revenue
    safe_actual = actual.replace(0, np.nan)
    mape = np.mean(np.abs((actual - predicted) / safe_actual)) * 100

    logger.info(f"{label} -> MAE: {mae:.2f} | RMSE: {rmse:.2f} | MAPE: {mape:.1f}%")
    return {"mae": mae, "rmse": rmse, "mape": mape}


def baseline_forecast(train: pd.DataFrame, horizon: int) -> np.ndarray:
    """Naive baseline: repeat the average of the last 7 training days."""
    avg_last_week = train["y"].tail(7).mean()
    return np.full(horizon, avg_last_week)


def main():
    daily = get_daily_revenue_series()

    train = daily.iloc[:-HOLDOUT_DAYS]
    test = daily.iloc[-HOLDOUT_DAYS:]
    logger.info(f"Train days: {len(train)} | Holdout (test) days: {len(test)}")

    # --- Baseline ---
    baseline_preds = baseline_forecast(train, HOLDOUT_DAYS)
    evaluate_forecast(test["y"], baseline_preds, "Baseline (7-day average)")

    # --- Prophet, evaluated on the same holdout ---
    model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
    model.fit(train)

    future = model.make_future_dataframe(periods=HOLDOUT_DAYS)
    forecast = model.predict(future)
    test_forecast = forecast.tail(HOLDOUT_DAYS)["yhat"].values
    evaluate_forecast(test["y"], test_forecast, "Prophet")

    # --- Retrain on FULL data for genuine future forecasting ---
    full_model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
    full_model.fit(daily)

    future_90 = full_model.make_future_dataframe(periods=90)
    forecast_90 = full_model.predict(future_90)

    forecast_output = forecast_90[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(90)
    forecast_output.to_csv(MODEL_DIR / "sales_forecast_90day.csv", index=False)
    joblib.dump(full_model, MODEL_DIR / "sales_forecast_model.pkl")

    logger.info("Forecast saved: 30/60/90-day values all included in sales_forecast_90day.csv")
    logger.info(f"Next 7 days preview:\n{forecast_output.head(7).to_string(index=False)}")


if __name__ == "__main__":
    main()