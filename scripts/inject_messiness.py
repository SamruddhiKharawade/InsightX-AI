"""
Deliberately introduces realistic data-quality problems into data/raw/*.csv:
missing values, duplicate rows, inconsistent text casing/whitespace, and a
few impossible values. This simulates messy real-world data so the cleaning
pipeline (Phase 5) has genuine problems to fix.

Run this ONCE, after generate_synthetic_data.py, before any cleaning happens.
"""

import random
import numpy as np
import pandas as pd

random.seed(7)
np.random.seed(7)

RAW_DIR = "data/raw"


def mess_up_customers():
    df = pd.read_csv(f"{RAW_DIR}/customers.csv")

    # Missing values: 3% of ages, 2% of genders
    df.loc[df.sample(frac=0.03, random_state=1).index, "age"] = np.nan
    df.loc[df.sample(frac=0.02, random_state=2).index, "gender"] = np.nan

    # Inconsistent city text: random casing + stray whitespace
    def mess_city(city):
        variant = random.choice(["lower", "upper", "pad", "keep"])
        if variant == "lower":
            return city.lower()
        if variant == "upper":
            return city.upper()
        if variant == "pad":
            return f"  {city}  "
        return city

    df["city"] = df["city"].apply(mess_city)

    # Duplicate a handful of rows entirely
    duplicates = df.sample(frac=0.01, random_state=3)
    df = pd.concat([df, duplicates], ignore_index=True)

    df.to_csv(f"{RAW_DIR}/customers.csv", index=False)


def mess_up_products():
    df = pd.read_csv(f"{RAW_DIR}/products.csv")

    # A few impossible inventory values (data entry errors)
    df.loc[df.sample(n=3, random_state=4).index, "inventory"] = -5

    # Missing inventory for a few products
    df.loc[df.sample(frac=0.05, random_state=5).index, "inventory"] = np.nan

    df.to_csv(f"{RAW_DIR}/products.csv", index=False)


def mess_up_orders():
    df = pd.read_csv(f"{RAW_DIR}/orders.csv")

    # Missing delivery_time for some rows
    df.loc[df.sample(frac=0.04, random_state=6).index, "delivery_time"] = np.nan

    # Inconsistent payment_method casing
    def mess_payment(method):
        variant = random.choice(["lower", "upper", "keep"])
        return method.lower() if variant == "lower" else method.upper() if variant == "upper" else method

    df["payment_method"] = df["payment_method"].apply(mess_payment)

    # A few impossible values: negative quantity, zero price
    df.loc[df.sample(n=5, random_state=7).index, "quantity"] = -1
    df.loc[df.sample(n=5, random_state=8).index, "price"] = 0

    # Duplicate a handful of orders entirely
    duplicates = df.sample(frac=0.005, random_state=9)
    df = pd.concat([df, duplicates], ignore_index=True)

    df.to_csv(f"{RAW_DIR}/orders.csv", index=False)


def mess_up_reviews():
    df = pd.read_csv(f"{RAW_DIR}/reviews.csv")

    # Missing review_text for a few rows (rating still present)
    df.loc[df.sample(frac=0.03, random_state=10).index, "review_text"] = np.nan

    df.to_csv(f"{RAW_DIR}/reviews.csv", index=False)


def mess_up_marketing():
    df = pd.read_csv(f"{RAW_DIR}/marketing.csv")

    # Missing spend values
    df.loc[df.sample(frac=0.04, random_state=11).index, "spend"] = np.nan

    df.to_csv(f"{RAW_DIR}/marketing.csv", index=False)


def main():
    mess_up_customers()
    mess_up_products()
    mess_up_orders()
    mess_up_reviews()
    mess_up_marketing()
    print("Messiness injected into data/raw/*.csv. Ready for cleaning (Phase 5).")


if __name__ == "__main__":
    main()