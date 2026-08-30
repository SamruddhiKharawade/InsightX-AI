"""
Central configuration for InsightX AI.
All file paths and expected table schemas live here so every other script
imports from a single, consistent source instead of hardcoding paths.
"""

from pathlib import Path

# BASE_DIR = the project root (InsightX-AI/).
# __file__ is this file's own path; .parent.parent walks up:
# settings.py -> config/ -> InsightX-AI/
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
LOG_DIR = BASE_DIR / "logs"

# Expected columns for each raw file — used to validate ingestion.
# If a CSV is missing any of these columns, ingestion should fail loudly
# rather than let bad data quietly flow further into the pipeline.
EXPECTED_SCHEMAS = {
    "customers": ["customer_id", "customer_name", "age", "gender", "city",
                  "signup_date", "customer_segment"],
    "products": ["product_id", "category", "brand", "cost", "selling_price", "inventory"],
    "orders": ["order_id", "customer_id", "product_id", "order_date", "quantity",
               "price", "discount", "payment_method", "delivery_time", "status"],
    "reviews": ["review_id", "customer_id", "order_id", "rating", "review_text", "review_date"],
    "marketing": ["campaign_id", "customer_id", "campaign", "spend", "clicks", "conversion"],
}