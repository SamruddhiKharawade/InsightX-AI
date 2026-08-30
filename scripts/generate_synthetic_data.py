"""
InsightX AI — Synthetic Data Generator
----------------------------------------
Generates realistic, linked business data:
customers, products, orders, reviews, marketing campaigns.

Run this once to create the raw dataset in data/raw/.
"""

import random
from datetime import date, timedelta
import numpy as np
import pandas as pd
from faker import Faker

# Fixed seed so results are reproducible every time you run this script
random.seed(42)
np.random.seed(42)
fake = Faker("en_IN")   # Indian locale for realistic Indian names/context
Faker.seed(42)

# -----------------------------
# CONFIG — change these numbers if you want a bigger/smaller dataset
# -----------------------------
N_CUSTOMERS = 1500
N_PRODUCTS = 60
N_ORDERS = 9000
START_DATE = date(2023, 1, 1)
END_DATE = date(2024, 12, 31)

CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Pune",
          "Hyderabad", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow"]
SEGMENTS = ["New", "Regular", "Premium"]
CATEGORIES = ["Electronics", "Fashion", "Home & Kitchen", "Beauty",
              "Sports", "Books", "Grocery", "Toys"]
BRANDS = ["Nova", "Zenith", "UrbanCraft", "Primo", "Everly",
          "Northline", "Vantage", "Coral", "Brightside", "Kestrel"]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "UPI", "Net Banking", "COD"]
STATUSES = ["Delivered", "Delivered", "Delivered", "Delivered",  # weighted common
            "Cancelled", "Returned", "Pending"]
CAMPAIGNS = ["Diwali Sale", "Republic Day Offer", "Summer Fest",
             "Monsoon Bonanza", "New Year Sale", "Flash Weekend Deal"]

POSITIVE_PHRASES = [
    "Great quality, exactly as described. Very happy with this purchase.",
    "Fast delivery and excellent packaging. Will buy again.",
    "Amazing value for money. Highly recommend this product.",
    "Works perfectly, better than I expected.",
]
NEUTRAL_PHRASES = [
    "Product is okay, nothing special but does the job.",
    "Average quality, delivery took longer than expected.",
    "It's fine, though the price feels a bit high for what you get.",
]
NEGATIVE_PHRASES = [
    "Very disappointed, product arrived damaged.",
    "Poor quality, does not match the description at all.",
    "Delivery was extremely delayed and customer service was unhelpful.",
    "Would not recommend, stopped working within a week.",
]


def random_date(start, end):
    """Return a random date between start and end (inclusive)."""
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def generate_customers():
    rows = []
    for i in range(1, N_CUSTOMERS + 1):
        signup = random_date(START_DATE, END_DATE - timedelta(days=30))
        rows.append({
            "customer_id": i,
            "customer_name": fake.name(),
            "age": np.random.randint(18, 65),
            "gender": random.choice(["Male", "Female"]),
            "city": random.choice(CITIES),
            "signup_date": signup,
            "customer_segment": random.choices(SEGMENTS, weights=[0.3, 0.5, 0.2])[0],
        })
    return pd.DataFrame(rows)


def generate_products():
    rows = []
    for i in range(1, N_PRODUCTS + 1):
        cost = round(np.random.uniform(150, 8000), 2)
        markup = np.random.uniform(1.2, 1.8)  # selling price is 20-80% above cost
        rows.append({
            "product_id": i,
            "category": random.choice(CATEGORIES),
            "brand": random.choice(BRANDS),
            "cost": cost,
            "selling_price": round(cost * markup, 2),
            "inventory": np.random.randint(0, 500),
        })
    return pd.DataFrame(rows)


def generate_orders(customers_df, products_df):
    rows = []
    customer_ids = customers_df["customer_id"].tolist()

    # Mark ~15% of customers as "dormant" — their last order will be forced
    # into the early part of the timeline, creating real churn signal later.
    dormant_customers = set(random.sample(customer_ids, int(N_CUSTOMERS * 0.15)))

    for order_id in range(1, N_ORDERS + 1):
        cust_id = random.choice(customer_ids)
        product_row = products_df.sample(1).iloc[0]

        if cust_id in dormant_customers:
            # Dormant customers only order in the first half of the timeline
            midpoint = START_DATE + (END_DATE - START_DATE) / 2
            order_date = random_date(START_DATE, midpoint)
        else:
            order_date = random_date(START_DATE, END_DATE)

        quantity = np.random.randint(1, 5)
        discount = round(random.choice([0, 0, 0, 5, 10, 15, 20]) / 100, 2)
        price = product_row["selling_price"]

        rows.append({
            "order_id": order_id,
            "customer_id": cust_id,
            "product_id": int(product_row["product_id"]),
            "order_date": order_date,
            "quantity": quantity,
            "price": price,
            "discount": discount,
            "payment_method": random.choice(PAYMENT_METHODS),
            "delivery_time": np.random.randint(1, 10),  # days
            "status": random.choice(STATUSES),
        })

    df = pd.DataFrame(rows)

    # Inject a deliberate anomaly: artificially spike order volume/price
    # in one specific month, for the anomaly detection phase later.
    anomaly_month_mask = (
        (pd.to_datetime(df["order_date"]).dt.year == 2024)
        & (pd.to_datetime(df["order_date"]).dt.month == 11)
    )
    df.loc[anomaly_month_mask, "price"] = df.loc[anomaly_month_mask, "price"] * 1.6

    return df


def generate_reviews(orders_df):
    rows = []
    # Only delivered orders get reviews, and not every delivered order does
    delivered = orders_df[orders_df["status"] == "Delivered"]
    reviewed_orders = delivered.sample(frac=0.4, random_state=42)

    for review_id, (_, order) in enumerate(reviewed_orders.iterrows(), start=1):
        rating = random.choices([1, 2, 3, 4, 5], weights=[0.07, 0.08, 0.15, 0.30, 0.40])[0]
        if rating >= 4:
            text = random.choice(POSITIVE_PHRASES)
        elif rating == 3:
            text = random.choice(NEUTRAL_PHRASES)
        else:
            text = random.choice(NEGATIVE_PHRASES)

        review_date = order["order_date"] + timedelta(days=np.random.randint(2, 15))
        rows.append({
            "review_id": review_id,
            "customer_id": order["customer_id"],
            "order_id": order["order_id"],
            "rating": rating,
            "review_text": text,
            "review_date": review_date,
        })
    return pd.DataFrame(rows)


def generate_marketing(customers_df):
    rows = []
    campaign_id = 1
    # Each customer has a chance of being targeted by 0-3 campaigns
    for cust_id in customers_df["customer_id"]:
        n_campaigns = random.choices([0, 1, 2, 3], weights=[0.3, 0.4, 0.2, 0.1])[0]
        for _ in range(n_campaigns):
            clicks = np.random.randint(0, 50)
            conversion = 1 if random.random() < 0.12 else 0  # ~12% conversion rate
            rows.append({
                "campaign_id": campaign_id,
                "customer_id": cust_id,
                "campaign": random.choice(CAMPAIGNS),
                "spend": round(np.random.uniform(20, 500), 2),
                "clicks": clicks,
                "conversion": conversion,
            })
            campaign_id += 1
    return pd.DataFrame(rows)


def main():
    print("Generating customers...")
    customers_df = generate_customers()

    print("Generating products...")
    products_df = generate_products()

    print("Generating orders...")
    orders_df = generate_orders(customers_df, products_df)

    print("Generating reviews...")
    reviews_df = generate_reviews(orders_df)

    print("Generating marketing campaigns...")
    marketing_df = generate_marketing(customers_df)

    output_dir = "data/raw"
    customers_df.to_csv(f"{output_dir}/customers.csv", index=False)
    products_df.to_csv(f"{output_dir}/products.csv", index=False)
    orders_df.to_csv(f"{output_dir}/orders.csv", index=False)
    reviews_df.to_csv(f"{output_dir}/reviews.csv", index=False)
    marketing_df.to_csv(f"{output_dir}/marketing.csv", index=False)

    print("\nDone. Row counts:")
    print(f"  customers.csv  : {len(customers_df)}")
    print(f"  products.csv   : {len(products_df)}")
    print(f"  orders.csv     : {len(orders_df)}")
    print(f"  reviews.csv    : {len(reviews_df)}")
    print(f"  marketing.csv  : {len(marketing_df)}")


if __name__ == "__main__":
    main()