"""
Loads cleaned CSVs from data/processed/ into their matching PostgreSQL tables.

Load order:
customers -> products -> orders -> reviews -> marketing

Reviews are validated against existing orders before loading.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
from sqlalchemy import text

from config.settings import PROCESSED_DATA_DIR
from src.database.db_connection import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)

LOAD_ORDER = [
    "customers",
    "products",
    "orders",
    "reviews",
    "marketing"
]

TABLE_NAME_MAP = {
    "marketing": "marketing_campaigns"
}


def load_table(engine, csv_name: str):
    table_name = TABLE_NAME_MAP.get(csv_name, csv_name)

    # Read CSV
    df = pd.read_csv(
        PROCESSED_DATA_DIR / f"{csv_name}.csv"
    )

    # Check whether table already contains data
    with engine.connect() as connection:
        existing_count = connection.execute(
            text(f"SELECT COUNT(*) FROM {table_name}")
        ).scalar()

    if existing_count > 0:
        logger.info(
            f"Skipping '{table_name}' — "
            f"table already contains {existing_count} rows."
        )
        return

    # Special validation for reviews
    if csv_name == "reviews":

        logger.info(
            "Validating reviews against existing orders..."
        )

        with engine.connect() as connection:
            valid_order_ids = pd.read_sql(
                text("SELECT order_id FROM orders"),
                connection
            )["order_id"]

        valid_order_ids = set(valid_order_ids)

        original_count = len(df)

        df = df[
            df["order_id"].isin(valid_order_ids)
        ].copy()

        skipped_count = original_count - len(df)

        if skipped_count > 0:
            logger.warning(
                f"Skipped {skipped_count} reviews "
                f"with invalid order_id values."
            )

    # Load data
    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False
    )

    logger.info(
        f"Loaded {len(df)} rows into '{table_name}'"
    )


def main():

    engine = get_engine()

    for csv_name in LOAD_ORDER:
        load_table(engine, csv_name)

    logger.info(
        "All tables loaded into PostgreSQL successfully."
    )


if __name__ == "__main__":
    main()