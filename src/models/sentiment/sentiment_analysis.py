"""
NLP sentiment analysis on customer reviews using VADER (rule-based, no
training data required). Also tags each review with topic keywords
(delivery, product quality, pricing, customer service, payment).

Validation: our synthetic reviews (Phase 3) were generated with sentiment
matching their star rating, so we check VADER's output against rating
as a sanity check before trusting it further.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

import nltk
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer

from src.database.db_connection import get_engine
from src.utils.logger import get_logger

logger = get_logger(__name__)

nltk.download("vader_lexicon", quiet=True)

TOPIC_KEYWORDS = {
    "Delivery": ["delivery", "delivered", "shipping", "arrived", "late"],
    "Product Quality": ["quality", "damaged", "defective", "broken", "works"],
    "Pricing": ["price", "expensive", "value", "money"],
    "Customer Service": ["service", "support", "helpful", "unhelpful", "response"],
    "Payment": ["payment", "refund", "charged", "billing"],
}


def classify_sentiment(compound_score: float) -> str:
    if compound_score >= 0.05:
        return "Positive"
    if compound_score <= -0.05:
        return "Negative"
    return "Neutral"


def tag_topics(text: str) -> str:
    text_lower = text.lower()
    matched = [
        topic for topic, keywords in TOPIC_KEYWORDS.items()
        if any(kw in text_lower for kw in keywords)
    ]
    return ", ".join(matched) if matched else "General"


def run_sentiment_analysis() -> pd.DataFrame:
    engine = get_engine()
    reviews = pd.read_sql("SELECT * FROM reviews", engine)

    sia = SentimentIntensityAnalyzer()
    reviews["sentiment_score"] = reviews["review_text"].apply(
        lambda t: sia.polarity_scores(t)["compound"]
    )
    reviews["sentiment_label"] = reviews["sentiment_score"].apply(classify_sentiment)
    reviews["topics"] = reviews["review_text"].apply(tag_topics)

    # Validation against star rating
    reviews["rating_based_sentiment"] = reviews["rating"].apply(
        lambda r: "Positive" if r >= 4 else ("Negative" if r <= 2 else "Neutral")
    )
    agreement = (reviews["sentiment_label"] == reviews["rating_based_sentiment"]).mean()
    logger.info(f"VADER vs rating-based sentiment agreement: {agreement:.1%}")

    reviews.to_sql("review_sentiment", engine, if_exists="replace", index=False)
    logger.info(f"Saved review_sentiment table: {len(reviews)} reviews")
    logger.info(f"Sentiment distribution:\n{reviews['sentiment_label'].value_counts()}")

    return reviews


if __name__ == "__main__":
    run_sentiment_analysis()