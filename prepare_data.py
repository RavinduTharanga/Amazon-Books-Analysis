import os
import pandas as pd
import kagglehub

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

PROCESSED_PATH = os.path.join(DATA_DIR, "processed.parquet")
AGG_REVIEWS_PER_YEAR = os.path.join(DATA_DIR, "agg_reviews_per_year.parquet")
AGG_RATING_PER_YEAR = os.path.join(DATA_DIR, "agg_rating_per_year.parquet")
AGG_SENTIMENT_PER_YEAR = os.path.join(DATA_DIR, "agg_sentiment_per_year.parquet")
AGG_SENTIMENT_LABELS = os.path.join(DATA_DIR, "agg_sentiment_labels.parquet")
AGG_HELPFUL_PER_YEAR = os.path.join(DATA_DIR, "agg_helpful_per_year.parquet")
AGG_TEXTLEN_PER_YEAR = os.path.join(DATA_DIR, "agg_textlen_per_year.parquet")
AGG_PRICE_PER_YEAR = os.path.join(DATA_DIR, "agg_price_per_year.parquet")

def ensure_vader():
    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        nltk.download("vader_lexicon")

def label_sentiment(score: float) -> str:
    if score > 0.05:
        return "Positive"
    if score < -0.05:
        return "Negative"
    return "Neutral"

def main():
    print("Downloading dataset via kagglehub...")
    path = kagglehub.dataset_download("hadifariborzi/amazon-books-dataset-20k-books-727k-reviews")

    reviews_path = os.path.join(path, "amazon_books_reviews_sample_20k.csv")
    meta_path    = os.path.join(path, "amazon_books_metadata_sample_20k.csv")

    print("Loading CSVs...")
    df_reviews = pd.read_csv(reviews_path)
    df_meta    = pd.read_csv(meta_path)

    # Date/year
    df_reviews["date"] = pd.to_datetime(df_reviews.get("date"), errors="coerce")
    df_reviews["year"] = df_reviews["date"].dt.year

    # Review length
    df_reviews["text"] = df_reviews.get("text").astype(str)
    df_reviews["text_len"] = df_reviews["text"].str.len()

    # Sentiment
    ensure_vader()
    sia = SentimentIntensityAnalyzer()
    df_reviews["sentiment"] = df_reviews["text"].apply(lambda x: sia.polarity_scores(x)["compound"])
    df_reviews["sentiment_label"] = df_reviews["sentiment"].apply(label_sentiment)

    # Merge metadata (include what you need)
    keep_cols = [c for c in [
        "parent_asin",
        "price_numeric",
        "category_level_3_detail",
        "author_name",
        "title"
    ] if c in df_meta.columns]

    df = df_reviews.merge(df_meta[keep_cols], on="parent_asin", how="left")

    # Clean a few fields
    if "category_level_3_detail" in df.columns:
        df["category_level_3_detail"] = df["category_level_3_detail"].fillna("Unknown")
    if "author_name" in df.columns:
        df["author_name"] = df["author_name"].fillna("Unknown")
    if "title" in df.columns:
        df["title"] = df["title"].fillna("Unknown Title")

    # Save processed
    print(f"Writing {PROCESSED_PATH} ...")
    df.to_parquet(PROCESSED_PATH, index=False)

    # Aggregations (fast charts)
    print("Writing aggregates...")

    df.groupby("year").size().rename("review_count").reset_index().to_parquet(AGG_REVIEWS_PER_YEAR, index=False)

    if "rating" in df.columns:
        df.groupby("year")["rating"].mean().rename("avg_rating").reset_index().to_parquet(AGG_RATING_PER_YEAR, index=False)

    df.groupby("year")["sentiment"].mean().rename("avg_sentiment").reset_index().to_parquet(AGG_SENTIMENT_PER_YEAR, index=False)

    df.groupby(["year", "sentiment_label"]).size().rename("count").reset_index().to_parquet(AGG_SENTIMENT_LABELS, index=False)

    if "helpful_vote" in df.columns:
        df.groupby("year")["helpful_vote"].mean().rename("avg_helpful_vote").reset_index().to_parquet(AGG_HELPFUL_PER_YEAR, index=False)

    df.groupby("year")["text_len"].mean().rename("avg_text_len").reset_index().to_parquet(AGG_TEXTLEN_PER_YEAR, index=False)

    if "price_numeric" in df.columns:
        df.groupby("year")["price_numeric"].mean().rename("avg_price").reset_index().to_parquet(AGG_PRICE_PER_YEAR, index=False)

    print("Done.")

if __name__ == "__main__":
    main()
