import os
import pandas as pd
import streamlit as st
import plotly.express as px

# =========================
# Paths
# =========================
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

PROCESSED_PATH = os.path.join(DATA_DIR, "processed.parquet")
AGG_REVIEWS_PER_YEAR = os.path.join(DATA_DIR, "agg_reviews_per_year.parquet")
AGG_RATING_PER_YEAR = os.path.join(DATA_DIR, "agg_rating_per_year.parquet")
AGG_SENTIMENT_PER_YEAR = os.path.join(DATA_DIR, "agg_sentiment_per_year.parquet")
AGG_SENTIMENT_LABELS = os.path.join(DATA_DIR, "agg_sentiment_labels.parquet")
AGG_HELPFUL_PER_YEAR = os.path.join(DATA_DIR, "agg_helpful_per_year.parquet")
AGG_TEXTLEN_PER_YEAR = os.path.join(DATA_DIR, "agg_textlen_per_year.parquet")
AGG_PRICE_PER_YEAR = os.path.join(DATA_DIR, "agg_price_per_year.parquet")

THEME_CSV = os.path.join(DATA_DIR, "amazon_books_reviews_with_merged_categories.csv")
BAD_THEME_CATS = {"other", "great book", "good book", "nice book"}



import boto3
from botocore.exceptions import ClientError

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

REQUIRED_FILES = [
    "processed.parquet",
    "agg_reviews_per_year.parquet",
    "agg_rating_per_year.parquet",
    "agg_sentiment_per_year.parquet",
    "agg_sentiment_labels.parquet",
    "agg_helpful_per_year.parquet",
    "agg_textlen_per_year.parquet",
    "agg_price_per_year.parquet",
    "amazon_books_reviews_with_merged_categories.csv",
]

def s3_download_if_missing():
    bucket = st.secrets["S3_BUCKET"]
    prefix = st.secrets.get("S3_PREFIX", "data").strip("/")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
        region_name=st.secrets.get("AWS_DEFAULT_REGION", "us-east-1"),

    )

    for fname in REQUIRED_FILES:
        local_path = os.path.join(DATA_DIR, fname)
        if os.path.exists(local_path):
            continue

        key = f"{prefix}/{fname}"
        try:
            s3.download_file(bucket, key, local_path)
        except ClientError as e:
            st.error(f"Failed to download s3://{bucket}/{key}\n{e}")
            st.stop()

s3_download_if_missing()


st.set_page_config(page_title="Amazon Books Dashboard", layout="wide")

@st.cache_data
def load_df(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)

@st.cache_data
def load_theme_csv(path: str) -> pd.DataFrame:
    d = pd.read_csv(path)
    d["year"] = pd.to_numeric(d["year"], errors="coerce")
    d = d.dropna(subset=["year", "merged_category"]).copy()
    d["year"] = d["year"].astype(int)
    d["merged_category"] = d["merged_category"].astype(str).str.strip()
    d = d[~d["merged_category"].str.lower().isin(BAD_THEME_CATS)]
    d = d[d["merged_category"] != ""].reset_index(drop=True)
    return d

st.title("Amazon Books Reviews — Interactive Dashboard")

# =========================
# Safety checks
# =========================
if not os.path.exists(PROCESSED_PATH):
    st.warning("Processed data not found. Run: python prepare_data.py")
    st.stop()

df = load_df(PROCESSED_PATH)

if "year" not in df.columns:
    st.error("Column 'year' not found in processed.parquet")
    st.stop()

# ensure numeric year
df["year"] = pd.to_numeric(df["year"], errors="coerce")

# =========================
# Sidebar filters (controls only)
# =========================
st.sidebar.header("Filters")

years = sorted([int(y) for y in df["year"].dropna().unique().tolist()])
if years:
    y_min, y_max = int(min(years)), int(max(years))
    year_range = st.sidebar.slider("Year range", y_min, y_max, (y_min, y_max), key="year_range")
else:
    year_range = None

category_col = "category_level_3_detail" if "category_level_3_detail" in df.columns else None
author_col   = "author_name" if "author_name" in df.columns else None

# Category filter
if category_col:
    cats = ["All"] + sorted(df[category_col].fillna("Unknown").unique().tolist())
    selected_cat = st.sidebar.selectbox("Category", cats, index=0, key="selected_cat")
else:
    selected_cat = "All"

# Author filter (safe, avoids huge dropdown)
if author_col:
    st.sidebar.subheader("Author filter")
    TOP_N_AUTHORS = 300

    # build counts on year-filtered df later; for now use full df
    author_counts_all = df[author_col].fillna("Unknown").value_counts()
    top_authors_all = author_counts_all.head(TOP_N_AUTHORS).index.tolist()
    authors = ["All"] + top_authors_all
    selected_author = st.sidebar.selectbox("Author (Top 300)", authors, index=0, key="selected_author")
else:
    selected_author = "All"

# =========================
# Base filter: YEAR ONLY (affects everything)
# =========================
df_year = df.copy()
if year_range:
    df_year = df_year[(df_year["year"] >= year_range[0]) & (df_year["year"] <= year_range[1])]

st.caption(f"Rows (year-filtered): {len(df_year):,}")

# =========================
# Separate dataframes per chart
# =========================
df_for_category = df_year
if category_col and selected_cat != "All":
    df_for_category = df_year[df_year[category_col].fillna("Unknown") == selected_cat]

df_for_author = df_year
if author_col and selected_author != "All":
    df_for_author = df_year[df_year[author_col].fillna("Unknown") == selected_author]

df_for_sentiment = df_year
df_for_books = df_year

# =========================
# Pre-aggregated global trends (year-only)
# =========================
agg_reviews = load_df(AGG_REVIEWS_PER_YEAR) if os.path.exists(AGG_REVIEWS_PER_YEAR) else None
agg_rating  = load_df(AGG_RATING_PER_YEAR) if os.path.exists(AGG_RATING_PER_YEAR) else None
agg_sent    = load_df(AGG_SENTIMENT_PER_YEAR) if os.path.exists(AGG_SENTIMENT_PER_YEAR) else None
agg_labels  = load_df(AGG_SENTIMENT_LABELS) if os.path.exists(AGG_SENTIMENT_LABELS) else None
agg_helpful = load_df(AGG_HELPFUL_PER_YEAR) if os.path.exists(AGG_HELPFUL_PER_YEAR) else None
agg_textlen = load_df(AGG_TEXTLEN_PER_YEAR) if os.path.exists(AGG_TEXTLEN_PER_YEAR) else None
agg_price   = load_df(AGG_PRICE_PER_YEAR) if os.path.exists(AGG_PRICE_PER_YEAR) else None

def apply_year_filter(agg: pd.DataFrame, year_col="year"):
    if agg is None or not year_range:
        return agg
    if year_col not in agg.columns:
        return agg
    agg2 = agg.copy()
    agg2[year_col] = pd.to_numeric(agg2[year_col], errors="coerce")
    return agg2[(agg2[year_col] >= year_range[0]) & (agg2[year_col] <= year_range[1])]

col1, col2 = st.columns(2)

with col1:
    if agg_reviews is not None and {"year", "review_count"}.issubset(agg_reviews.columns):
        a = apply_year_filter(agg_reviews)
        fig = px.bar(a, x="year", y="review_count", title="Number of Reviews Per Year")
        st.plotly_chart(fig, width="stretch", key="reviews_per_year")

    if agg_textlen is not None and {"year", "avg_text_len"}.issubset(agg_textlen.columns):
        a = apply_year_filter(agg_textlen)
        fig = px.line(a, x="year", y="avg_text_len", markers=True, title="Average Review Length by Year")
        st.plotly_chart(fig, width="stretch", key="avg_text_len_per_year")

    if agg_helpful is not None and {"year", "avg_helpful_vote"}.issubset(agg_helpful.columns):
        a = apply_year_filter(agg_helpful)
        fig = px.line(a, x="year", y="avg_helpful_vote", markers=True, title="Average Helpful Votes by Year")
        st.plotly_chart(fig, width="stretch", key="avg_helpful_votes_per_year")

with col2:
    if agg_rating is not None and {"year", "avg_rating"}.issubset(agg_rating.columns):
        a = apply_year_filter(agg_rating)
        fig = px.line(a, x="year", y="avg_rating", markers=True, title="Average Rating Per Year")
        st.plotly_chart(fig, width="stretch", key="avg_rating_per_year")

    if agg_sent is not None and {"year", "avg_sentiment"}.issubset(agg_sent.columns):
        a = apply_year_filter(agg_sent)
        fig = px.line(a, x="year", y="avg_sentiment", markers=True, title="Average Sentiment Score Per Year")
        st.plotly_chart(fig, width="stretch", key="avg_sentiment_per_year")

    if agg_price is not None and {"year", "avg_price"}.issubset(agg_price.columns):
        a = apply_year_filter(agg_price)
        fig = px.line(a, x="year", y="avg_price", markers=True, title="Average Book Price")
        st.plotly_chart(fig, width="stretch", key="avg_price_per_year")

st.divider()

# =========================
# Category popularity over years
# =========================
if category_col and len(df_for_category) > 0:
    if selected_cat == "All":
        top_l3 = df_for_category[category_col].fillna("Unknown").value_counts().head(10).index.tolist()
        df_l3 = df_for_category[df_for_category[category_col].fillna("Unknown").isin(top_l3)]
        if len(df_l3) > 0:
            grp = df_l3.groupby(["year", category_col]).size().rename("count").reset_index()
            fig = px.line(grp, x="year", y="count", color=category_col, markers=True,
                          title="Category Popularity Over Years (Top 10)")
            st.plotly_chart(fig, width="stretch", key="category_popularity_top10")
    else:
        grp = df_for_category.groupby(["year"]).size().rename("count").reset_index()
        fig = px.line(grp, x="year", y="count", markers=True,
                      title=f"Category Popularity Over Years — {selected_cat}")
        st.plotly_chart(fig, width="stretch", key="category_popularity_selected")

# =========================
# Sentiment label trends (year only)
# =========================
if "sentiment_label" in df_for_sentiment.columns and len(df_for_sentiment) > 0:
    grp = df_for_sentiment.groupby(["year", "sentiment_label"]).size().rename("count").reset_index()
    fig = px.line(grp, x="year", y="count", color="sentiment_label", markers=True,
                  title="Sentiment Label Trends Over Years (Year only)")
    st.plotly_chart(fig, width="stretch", key="sentiment_label_trends")

# =========================
# Top 10 Books — popularity over years (year only)
# =========================
if "title" in df_for_books.columns and len(df_for_books) > 0:
    top_books = df_for_books["title"].fillna("Unknown").value_counts().head(10).index.tolist()
    df_tb = df_for_books[df_for_books["title"].fillna("Unknown").isin(top_books)]
    if len(df_tb) > 0:
        grp = df_tb.groupby(["year", "title"]).size().rename("count").reset_index()
        fig = px.line(grp, x="year", y="count", color="title", markers=True,
                      title="Top 10 Books — Popularity Over the Years")
        st.plotly_chart(fig, width="stretch", key="top10_books_popularity")

# =========================
# Top 10 Authors — popularity over years
# =========================
if author_col and len(df_for_author) > 0:
    if selected_author == "All":
        top_auth = df_for_author[author_col].fillna("Unknown").value_counts().head(10).index.tolist()
        df_ta = df_for_author[df_for_author[author_col].fillna("Unknown").isin(top_auth)]
        if len(df_ta) > 0:
            grp = df_ta.groupby(["year", author_col]).size().rename("count").reset_index()
            fig = px.line(grp, x="year", y="count", color=author_col, markers=True,
                          title="Top 10 Authors — Popularity Over the Years")
            st.plotly_chart(fig, width="stretch", key="top10_authors_popularity")
    else:
        grp = df_for_author.groupby(["year"]).size().rename("count").reset_index()
        fig = px.line(grp, x="year", y="count", markers=True,
                      title=f"Author Popularity Over the Years — {selected_author}")
        st.plotly_chart(fig, width="stretch", key="author_popularity_selected")

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
        theme_year_range = st.slider(
            "Thematic year range",
            tmin, tmax,
            (tmin, tmax),
            1,
            key="theme_year_range",
        )

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
        st.plotly_chart(fig_line, width="stretch", key="theme_line_log")

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
        st.plotly_chart(fig_stack, width="stretch", key="theme_stacked_props")

    with tab3:
        st.subheader("Counts Heatmap (Year × Thematic Category)")
        fig_heat = px.imshow(
            theme_counts_pivot,
            aspect="auto",
            labels=dict(x="Thematic Category", y="Year", color="Count"),
        )
        fig_heat.update_layout(height=650)
        st.plotly_chart(fig_heat, width="stretch", key="theme_heatmap")

