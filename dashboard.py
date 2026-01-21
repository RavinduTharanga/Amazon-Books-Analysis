import os
import pandas as pd
import streamlit as st
import plotly.express as px

import boto3
from botocore.exceptions import ClientError

# =========================
# Page config (must be first Streamlit call)
# =========================
st.set_page_config(page_title="Amazon Books Dashboard", layout="wide")

# =========================
# Paths
# =========================
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# We intentionally DO NOT use processed.parquet in Streamlit Cloud (too big).
AGG_REVIEWS_PER_YEAR     = os.path.join(DATA_DIR, "agg_reviews_per_year.parquet")
AGG_RATING_PER_YEAR      = os.path.join(DATA_DIR, "agg_rating_per_year.parquet")
AGG_SENTIMENT_PER_YEAR   = os.path.join(DATA_DIR, "agg_sentiment_per_year.parquet")
AGG_SENTIMENT_LABELS     = os.path.join(DATA_DIR, "agg_sentiment_labels.parquet")
AGG_HELPFUL_PER_YEAR     = os.path.join(DATA_DIR, "agg_helpful_per_year.parquet")
AGG_TEXTLEN_PER_YEAR     = os.path.join(DATA_DIR, "agg_textlen_per_year.parquet")
AGG_PRICE_PER_YEAR       = os.path.join(DATA_DIR, "agg_price_per_year.parquet")

THEME_CSV = os.path.join(DATA_DIR, "amazon_books_reviews_with_merged_categories.csv")
BAD_THEME_CATS = {"other", "great book", "good book", "nice book"}

REQUIRED_FILES = [
    "agg_reviews_per_year.parquet",
    "agg_rating_per_year.parquet",
    "agg_sentiment_per_year.parquet",
    "agg_sentiment_labels.parquet",
    "agg_helpful_per_year.parquet",
    "agg_textlen_per_year.parquet",
    "agg_price_per_year.parquet",
    "amazon_books_reviews_with_merged_categories.csv",
]

# =========================
# S3 download (runs once per container)
# =========================
def s3_download_if_missing():
    required_secrets = ["S3_BUCKET", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    missing = [k for k in required_secrets if k not in st.secrets]
    if missing:
        st.error(
            "Missing Streamlit secrets: "
            + ", ".join(missing)
            + "\nAdd them in Streamlit Cloud → Manage app → Settings → Secrets."
        )
        st.stop()

    bucket = st.secrets["S3_BUCKET"]
    prefix = st.secrets.get("S3_PREFIX", "data").strip("/")
    region = st.secrets.get("AWS_DEFAULT_REGION", "us-east-1")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
        region_name=region,
    )

    for fname in REQUIRED_FILES:
        local_path = os.path.join(DATA_DIR, fname)
        if os.path.exists(local_path):
            continue

        key = f"{prefix}/{fname}" if prefix else fname
        try:
            s3.download_file(bucket, key, local_path)
        except ClientError as e:
            st.error(f"Failed to download s3://{bucket}/{key}\n{e}")
            st.stop()

# Avoid re-downloading on every widget interaction
if "data_ready" not in st.session_state:
    s3_download_if_missing()
    st.session_state["data_ready"] = True

# =========================
# Loaders
# =========================
@st.cache_data
def load_parquet(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)

@st.cache_data
def load_theme_csv(path: str) -> pd.DataFrame:
    d = pd.read_csv(path)
    d["year"] = pd.to_numeric(d.get("year"), errors="coerce")
    d = d.dropna(subset=["year", "merged_category"]).copy()
    d["year"] = d["year"].astype(int)
    d["merged_category"] = d["merged_category"].astype(str).str.strip()
    d = d[~d["merged_category"].str.lower().isin(BAD_THEME_CATS)]
    d = d[d["merged_category"] != ""].reset_index(drop=True)
    return d

# =========================
# Title
# =========================
st.title("Amazon Books Reviews — Interactive Dashboard")
st.caption("This dashboard uses pre-aggregated files (low memory) + thematic category CSV.")

# =========================
# Load aggregates
# =========================
agg_reviews = load_parquet(AGG_REVIEWS_PER_YEAR) if os.path.exists(AGG_REVIEWS_PER_YEAR) else None
agg_rating  = load_parquet(AGG_RATING_PER_YEAR) if os.path.exists(AGG_RATING_PER_YEAR) else None
agg_sent    = load_parquet(AGG_SENTIMENT_PER_YEAR) if os.path.exists(AGG_SENTIMENT_PER_YEAR) else None
agg_labels  = load_parquet(AGG_SENTIMENT_LABELS) if os.path.exists(AGG_SENTIMENT_LABELS) else None
agg_helpful = load_parquet(AGG_HELPFUL_PER_YEAR) if os.path.exists(AGG_HELPFUL_PER_YEAR) else None
agg_textlen = load_parquet(AGG_TEXTLEN_PER_YEAR) if os.path.exists(AGG_TEXTLEN_PER_YEAR) else None
agg_price   = load_parquet(AGG_PRICE_PER_YEAR) if os.path.exists(AGG_PRICE_PER_YEAR) else None

def available_years(*dfs):
    yrs = set()
    for d in dfs:
        if d is not None and "year" in d.columns:
            y = pd.to_numeric(d["year"], errors="coerce").dropna().astype(int).unique().tolist()
            yrs.update(y)
    return sorted(yrs)

years = available_years(agg_reviews, agg_rating, agg_sent, agg_labels, agg_helpful, agg_textlen, agg_price)

st.sidebar.header("Filters")
if years:
    y_min, y_max = min(years), max(years)
    year_range = st.sidebar.slider("Year range", y_min, y_max, (y_min, y_max), key="year_range")
else:
    year_range = None
    st.sidebar.info("No year data found in aggregates.")

def apply_year_filter(agg: pd.DataFrame, year_col="year"):
    if agg is None or not year_range or year_col not in agg.columns:
        return agg
    a = agg.copy()
    a[year_col] = pd.to_numeric(a[year_col], errors="coerce")
    return a[(a[year_col] >= year_range[0]) & (a[year_col] <= year_range[1])]

# =========================
# Global trends
# =========================
col1, col2 = st.columns(2)

with col1:
    if agg_reviews is not None and {"year", "review_count"}.issubset(agg_reviews.columns):
        a = apply_year_filter(agg_reviews)
        fig = px.bar(a, x="year", y="review_count", title="Number of Reviews Per Year")
        st.plotly_chart(fig, use_container_width=True, key="reviews_per_year")

    if agg_textlen is not None and {"year", "avg_text_len"}.issubset(agg_textlen.columns):
        a = apply_year_filter(agg_textlen)
        fig = px.line(a, x="year", y="avg_text_len", markers=True, title="Average Review Length by Year")
        st.plotly_chart(fig, use_container_width=True, key="avg_text_len_per_year")

    if agg_helpful is not None and {"year", "avg_helpful_vote"}.issubset(agg_helpful.columns):
        a = apply_year_filter(agg_helpful)
        fig = px.line(a, x="year", y="avg_helpful_vote", markers=True, title="Average Helpful Votes by Year")
        st.plotly_chart(fig, use_container_width=True, key="avg_helpful_votes_per_year")

with col2:
    if agg_rating is not None and {"year", "avg_rating"}.issubset(agg_rating.columns):
        a = apply_year_filter(agg_rating)
        fig = px.line(a, x="year", y="avg_rating", markers=True, title="Average Rating Per Year")
        st.plotly_chart(fig, use_container_width=True, key="avg_rating_per_year")

    if agg_sent is not None and {"year", "avg_sentiment"}.issubset(agg_sent.columns):
        a = apply_year_filter(agg_sent)
        fig = px.line(a, x="year", y="avg_sentiment", markers=True, title="Average Sentiment Score Per Year")
        st.plotly_chart(fig, use_container_width=True, key="avg_sentiment_per_year")

    if agg_price is not None and {"year", "avg_price"}.issubset(agg_price.columns):
        a = apply_year_filter(agg_price)
        fig = px.line(a, x="year", y="avg_price", markers=True, title="Average Book Price")
        st.plotly_chart(fig, use_container_width=True, key="avg_price_per_year")

st.divider()

# =========================
# Sentiment label trends (from agg)
# =========================
if agg_labels is not None and {"year", "sentiment_label", "count"}.issubset(agg_labels.columns):
    a = apply_year_filter(agg_labels)
    fig = px.line(
        a,
        x="year",
        y="count",
        color="sentiment_label",
        markers=True,
        title="Sentiment Label Trends Over Years",
    )
    st.plotly_chart(fig, use_container_width=True, key="sentiment_label_trends_agg")

st.divider()

# =========================
# Thematic Categories
# =========================
st.header("Thematic Categories")

if not os.path.exists(THEME_CSV):
    st.warning(f"Thematic CSV not found: {THEME_CSV}")
else:
    theme_df = load_theme_csv(THEME_CSV)

    with st.sidebar.expander("Thematic Categories", expanded=False):
        theme_top_n = st.slider("Top N thematic categories", 5, 28, 20, 1, key="theme_top_n")
        tmin, tmax = int(theme_df["year"].min()), int(theme_df["year"].max())
        theme_year_range = st.slider("Thematic year range", tmin, tmax, (tmin, tmax), 1, key="theme_year_range")

    theme_df_f = theme_df[
        (theme_df["year"] >= theme_year_range[0]) &
        (theme_df["year"] <= theme_year_range[1])
    ].copy()

    st.caption(f"Thematic rows: {len(theme_df_f):,}")

    theme_overall_counts = theme_df_f["merged_category"].value_counts()
    theme_top_cats = theme_overall_counts.head(theme_top_n).index.tolist()
    theme_df_top = theme_df_f[theme_df_f["merged_category"].isin(theme_top_cats)].copy()

    theme_counts_long = (
        theme_df_top.groupby(["year", "merged_category"])
        .size()
        .reset_index(name="count")
    )

    theme_counts_pivot = (
        theme_counts_long.pivot(index="year", columns="merged_category", values="count")
        .fillna(0)
        .sort_index()
    )

    tab1, tab2, tab3 = st.tabs(["Line (log)", "Stacked proportions", "Heatmap"])

    with tab1:
        st.subheader("Review Counts per Thematic Category over Years (log scale)")
        fig_line = px.line(
            theme_counts_long,
            x="year",
            y="count",
            color="merged_category",
            markers=True,
        )
        fig_line.update_yaxes(type="log", title="Number of Reviews (log)")
        fig_line.update_xaxes(title="Year")
        fig_line.update_layout(legend_title_text="Thematic Category", height=600)
        st.plotly_chart(fig_line, use_container_width=True, key="theme_line_log")

    with tab2:
        st.subheader("Thematic Category Proportions per Year (stacked)")
        year_totals = theme_counts_pivot.sum(axis=1).replace(0, 1)
        theme_props_pivot = theme_counts_pivot.div(year_totals, axis=0)

        theme_props_long = (
            theme_props_pivot.reset_index()
            .melt(id_vars="year", var_name="merged_category", value_name="proportion")
        )

        fig_stack = px.bar(
            theme_props_long,
            x="year",
            y="proportion",
            color="merged_category",
            barmode="stack",
        )
        fig_stack.update_yaxes(title="Proportion")
        fig_stack.update_xaxes(title="Year")
        fig_stack.update_layout(legend_title_text="Thematic Category", height=600)
        st.plotly_chart(fig_stack, use_container_width=True, key="theme_stacked_props")

    with tab3:
        st.subheader("Counts Heatmap (Year × Thematic Category)")
        fig_heat = px.imshow(
            theme_counts_pivot,
            aspect="auto",
            labels=dict(x="Thematic Category", y="Year", color="Count"),
        )
        fig_heat.update_layout(height=650)
        st.plotly_chart(fig_heat, use_container_width=True, key="theme_heatmap")
