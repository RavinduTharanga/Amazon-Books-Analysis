# import os
# import pandas as pd
# import streamlit as st
# import plotly.express as px

# DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# PROCESSED_PATH = os.path.join(DATA_DIR, "processed.parquet")
# AGG_REVIEWS_PER_YEAR = os.path.join(DATA_DIR, "agg_reviews_per_year.parquet")
# AGG_RATING_PER_YEAR = os.path.join(DATA_DIR, "agg_rating_per_year.parquet")
# AGG_SENTIMENT_PER_YEAR = os.path.join(DATA_DIR, "agg_sentiment_per_year.parquet")
# AGG_SENTIMENT_LABELS = os.path.join(DATA_DIR, "agg_sentiment_labels.parquet")
# AGG_HELPFUL_PER_YEAR = os.path.join(DATA_DIR, "agg_helpful_per_year.parquet")
# AGG_TEXTLEN_PER_YEAR = os.path.join(DATA_DIR, "agg_textlen_per_year.parquet")
# AGG_PRICE_PER_YEAR = os.path.join(DATA_DIR, "agg_price_per_year.parquet")

# st.set_page_config(page_title="Amazon Books Dashboard", layout="wide")

# @st.cache_data
# def load_df(path: str) -> pd.DataFrame:
#     return pd.read_parquet(path)

# st.title("Amazon Books Reviews — Interactive Dashboard")

# # Safety checks
# if not os.path.exists(PROCESSED_PATH):
#     st.warning("Processed data not found. Run: python prepare_data.py")
#     st.stop()

# df = load_df(PROCESSED_PATH)

# # Sidebar filters
# st.sidebar.header("Filters")

# years = sorted([y for y in df["year"].dropna().unique().tolist() if y is not None])
# if years:
#     y_min, y_max = int(min(years)), int(max(years))
#     year_range = st.sidebar.slider("Year range", y_min, y_max, (y_min, y_max))
# else:
#     year_range = None

# category_col = "category_level_3_detail" if "category_level_3_detail" in df.columns else None
# author_col   = "author_name" if "author_name" in df.columns else None

# if category_col:
#     cats = ["All"] + sorted(df[category_col].fillna("Unknown").unique().tolist())
#     selected_cat = st.sidebar.selectbox("Category (L3)", cats, index=0)
# else:
#     selected_cat = "All"

# if author_col:
#     authors = ["All"] + sorted(df[author_col].fillna("Unknown").unique().tolist())
#     selected_author = st.sidebar.selectbox("Author", authors, index=0)
# else:
#     selected_author = "All"

# filtered = df.copy()
# if year_range:
#     filtered = filtered[(filtered["year"] >= year_range[0]) & (filtered["year"] <= year_range[1])]
# if category_col and selected_cat != "All":
#     filtered = filtered[filtered[category_col] == selected_cat]
# if author_col and selected_author != "All":
#     filtered = filtered[filtered[author_col] == selected_author]

# st.caption(f"Rows: {len(filtered):,}")

# # Load pre-aggregated files for global trends
# agg_reviews = load_df(AGG_REVIEWS_PER_YEAR) if os.path.exists(AGG_REVIEWS_PER_YEAR) else None
# agg_rating  = load_df(AGG_RATING_PER_YEAR) if os.path.exists(AGG_RATING_PER_YEAR) else None
# agg_sent    = load_df(AGG_SENTIMENT_PER_YEAR) if os.path.exists(AGG_SENTIMENT_PER_YEAR) else None
# agg_labels  = load_df(AGG_SENTIMENT_LABELS) if os.path.exists(AGG_SENTIMENT_LABELS) else None
# agg_helpful = load_df(AGG_HELPFUL_PER_YEAR) if os.path.exists(AGG_HELPFUL_PER_YEAR) else None
# agg_textlen = load_df(AGG_TEXTLEN_PER_YEAR) if os.path.exists(AGG_TEXTLEN_PER_YEAR) else None
# agg_price   = load_df(AGG_PRICE_PER_YEAR) if os.path.exists(AGG_PRICE_PER_YEAR) else None

# # Apply year filter to aggregates (optional)
# def apply_year_filter(agg: pd.DataFrame, year_col="year"):
#     if agg is None or not year_range:
#         return agg
#     return agg[(agg[year_col] >= year_range[0]) & (agg[year_col] <= year_range[1])]

# col1, col2 = st.columns(2)

# with col1:
#     if agg_reviews is not None:
#         a = apply_year_filter(agg_reviews)
#         fig = px.bar(a, x="year", y="review_count", title="Number of Reviews Per Year")
#         st.plotly_chart(fig, use_container_width=True)

#     if agg_textlen is not None:
#         a = apply_year_filter(agg_textlen)
#         fig = px.line(a, x="year", y="avg_text_len", markers=True, title="Average Review Length by Year")
#         st.plotly_chart(fig, use_container_width=True)

#     if agg_helpful is not None:
#         a = apply_year_filter(agg_helpful)
#         fig = px.line(a, x="year", y="avg_helpful_vote", markers=True, title="Average Helpful Votes by Year")
#         st.plotly_chart(fig, use_container_width=True)

# with col2:
#     if agg_rating is not None:
#         a = apply_year_filter(agg_rating)
#         fig = px.line(a, x="year", y="avg_rating", markers=True, title="Average Rating Per Year")
#         st.plotly_chart(fig, use_container_width=True)

#     if agg_sent is not None:
#         a = apply_year_filter(agg_sent)
#         fig = px.line(a, x="year", y="avg_sentiment", markers=True, title="Average Sentiment Score Per Year")
#         st.plotly_chart(fig, use_container_width=True)

#     if agg_price is not None:
#         a = apply_year_filter(agg_price)
#         fig = px.line(a, x="year", y="avg_price", markers=True, title="Average Book Price (by Review Year)")
#         st.plotly_chart(fig, use_container_width=True)

# st.divider()

# # Category popularity over years (top 10 inside the *filtered* set)
# if category_col:
#     top_l3 = filtered[category_col].value_counts().head(10).index.tolist()
#     df_l3 = filtered[filtered[category_col].isin(top_l3)]
#     if len(df_l3) > 0:
#         grp = df_l3.groupby(["year", category_col]).size().rename("count").reset_index()
#         fig = px.line(grp, x="year", y="count", color=category_col, markers=True,
#                       title="Category Popularity Over Years (Top 10 in current filter)")
#         st.plotly_chart(fig, use_container_width=True)

# # Sentiment label trends (inside filtered set)
# if "sentiment_label" in filtered.columns and len(filtered) > 0:
#     grp = filtered.groupby(["year", "sentiment_label"]).size().rename("count").reset_index()
#     fig = px.line(grp, x="year", y="count", color="sentiment_label", markers=True,
#                   title="Sentiment Label Trends Over Years (filtered)")
#     st.plotly_chart(fig, use_container_width=True)

# # Top books / authors over years (optional)
# if "title" in filtered.columns and len(filtered) > 0:
#     top_books = filtered["title"].value_counts().head(10).index.tolist()
#     df_tb = filtered[filtered["title"].isin(top_books)]
#     grp = df_tb.groupby(["year", "title"]).size().rename("count").reset_index()
#     fig = px.line(grp, x="year", y="count", color="title", markers=True,
#                   title="Top 10 Books — Popularity Over the Years (filtered)")
#     st.plotly_chart(fig, use_container_width=True)

# if author_col and len(filtered) > 0:
#     top_auth = filtered[author_col].value_counts().head(10).index.tolist()
#     df_ta = filtered[filtered[author_col].isin(top_auth)]
#     grp = df_ta.groupby(["year", author_col]).size().rename("count").reset_index()
#     fig = px.line(grp, x="year", y="count", color=author_col, markers=True,
#                   title="Top 10 Authors — Popularity Over the Years (filtered)")
#     st.plotly_chart(fig, use_container_width=True)


from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

# -------------------------
# Paths
# -------------------------
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

PROCESSED_PATH = DATA_DIR / "processed.parquet"
AGG_REVIEWS_PER_YEAR = DATA_DIR / "agg_reviews_per_year.parquet"
AGG_RATING_PER_YEAR = DATA_DIR / "agg_rating_per_year.parquet"
AGG_SENTIMENT_PER_YEAR = DATA_DIR / "agg_sentiment_per_year.parquet"
AGG_SENTIMENT_LABELS = DATA_DIR / "agg_sentiment_labels.parquet"
AGG_HELPFUL_PER_YEAR = DATA_DIR / "agg_helpful_per_year.parquet"
AGG_TEXTLEN_PER_YEAR = DATA_DIR / "agg_textlen_per_year.parquet"
AGG_PRICE_PER_YEAR = DATA_DIR / "agg_price_per_year.parquet"

st.set_page_config(page_title="Amazon Books Dashboard", layout="wide")


# -------------------------
# Helpers
# -------------------------
def is_lfs_pointer(path: Path) -> bool:
    """
    Git LFS stores files as tiny text pointers like:
      version https://git-lfs.github.com/spec/v1
      oid sha256:...
      size ...
    If Streamlit Cloud doesn't pull LFS objects, parquet/csv files are pointers and will crash reads.
    """
    try:
        if not path.exists() or path.is_dir():
            return False
        head = path.read_bytes()[:200]
        return b"git-lfs.github.com/spec" in head
    except Exception:
        return False


def must_exist_and_not_lfs(path: Path, label: str) -> None:
    if not path.exists():
        st.error(f"Missing file: **{label}**\n\nExpected at: `{path}`")
        st.info("If you haven't created it yet, run `python prepare_data.py` locally and push the output.")
        st.stop()

    if is_lfs_pointer(path):
        st.error(
            f"**{label}** exists, but it looks like a **Git LFS pointer file** (the real data was not downloaded).\n\n"
            "This commonly happens on Streamlit Cloud when LFS objects aren’t pulled.\n\n"
            "✅ Fix options:\n"
            "1) Move big data out of GitHub (S3 / Drive / HuggingFace / Kaggle) and download in the app.\n"
            "2) Or ensure LFS objects are actually available to the runtime.\n"
        )
        st.code(path.read_text(errors="ignore")[:500])
        st.stop()


@st.cache_data(show_spinner=False)
def load_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


def load_optional_parquet(path: Path) -> pd.DataFrame | None:
    if path.exists() and not is_lfs_pointer(path):
        return load_parquet(path)
    return None


def apply_year_filter(agg: pd.DataFrame | None, year_range: tuple[int, int] | None, year_col: str = "year"):
    if agg is None or year_range is None:
        return agg
    return agg[(agg[year_col] >= year_range[0]) & (agg[year_col] <= year_range[1])]


# -------------------------
# App
# -------------------------
st.title("Amazon Books Reviews — Interactive Dashboard")

# Required data
must_exist_and_not_lfs(PROCESSED_PATH, "processed.parquet")
df = load_parquet(PROCESSED_PATH)

# Sidebar filters
st.sidebar.header("Filters")

year_range = None
if "year" in df.columns:
    years = sorted([y for y in df["year"].dropna().unique().tolist() if y is not None])
    if years:
        y_min, y_max = int(min(years)), int(max(years))
        year_range = st.sidebar.slider("Year range", y_min, y_max, (y_min, y_max))

category_col = "category_level_3_detail" if "category_level_3_detail" in df.columns else None
author_col = "author_name" if "author_name" in df.columns else None

selected_cat = "All"
if category_col:
    cats = ["All"] + sorted(df[category_col].fillna("Unknown").unique().tolist())
    selected_cat = st.sidebar.selectbox("Category (L3)", cats, index=0)

selected_author = "All"
if author_col:
    authors = ["All"] + sorted(df[author_col].fillna("Unknown").unique().tolist())
    selected_author = st.sidebar.selectbox("Author", authors, index=0)

filtered = df.copy()
if year_range and "year" in filtered.columns:
    filtered = filtered[(filtered["year"] >= year_range[0]) & (filtered["year"] <= year_range[1])]
if category_col and selected_cat != "All":
    filtered = filtered[filtered[category_col] == selected_cat]
if author_col and selected_author != "All":
    filtered = filtered[filtered[author_col] == selected_author]

st.caption(f"Rows: {len(filtered):,}")

# Optional pre-aggregates
agg_reviews = load_optional_parquet(AGG_REVIEWS_PER_YEAR)
agg_rating  = load_optional_parquet(AGG_RATING_PER_YEAR)
agg_sent    = load_optional_parquet(AGG_SENTIMENT_PER_YEAR)
agg_labels  = load_optional_parquet(AGG_SENTIMENT_LABELS)
agg_helpful = load_optional_parquet(AGG_HELPFUL_PER_YEAR)
agg_textlen = load_optional_parquet(AGG_TEXTLEN_PER_YEAR)
agg_price   = load_optional_parquet(AGG_PRICE_PER_YEAR)

col1, col2 = st.columns(2)

with col1:
    if agg_reviews is not None:
        a = apply_year_filter(agg_reviews, year_range)
        if a is not None and len(a) > 0:
            fig = px.bar(a, x="year", y="review_count", title="Number of Reviews Per Year")
            st.plotly_chart(fig, width="stretch")

    if agg_textlen is not None:
        a = apply_year_filter(agg_textlen, year_range)
        if a is not None and len(a) > 0:
            fig = px.line(a, x="year", y="avg_text_len", markers=True, title="Average Review Length by Year")
            st.plotly_chart(fig, width="stretch")

    if agg_helpful is not None:
        a = apply_year_filter(agg_helpful, year_range)
        if a is not None and len(a) > 0:
            fig = px.line(a, x="year", y="avg_helpful_vote", markers=True, title="Average Helpful Votes by Year")
            st.plotly_chart(fig, width="stretch")

with col2:
    if agg_rating is not None:
        a = apply_year_filter(agg_rating, year_range)
        if a is not None and len(a) > 0:
            fig = px.line(a, x="year", y="avg_rating", markers=True, title="Average Rating Per Year")
            st.plotly_chart(fig, width="stretch")

    if agg_sent is not None:
        a = apply_year_filter(agg_sent, year_range)
        if a is not None and len(a) > 0:
            fig = px.line(a, x="year", y="avg_sentiment", markers=True, title="Average Sentiment Score Per Year")
            st.plotly_chart(fig, width="stretch")

    if agg_price is not None:
        a = apply_year_filter(agg_price, year_range)
        if a is not None and len(a) > 0:
            fig = px.line(a, x="year", y="avg_price", markers=True, title="Average Book Price (by Review Year)")
            st.plotly_chart(fig, width="stretch")

st.divider()

# Category popularity over years (top 10 inside the filtered set)
if category_col and len(filtered) > 0 and "year" in filtered.columns:
    top_l3 = filtered[category_col].value_counts().head(10).index.tolist()
    df_l3 = filtered[filtered[category_col].isin(top_l3)]
    if len(df_l3) > 0:
        grp = df_l3.groupby(["year", category_col]).size().rename("count").reset_index()
        fig = px.line(
            grp, x="year", y="count", color=category_col, markers=True,
            title="Category Popularity Over Years (Top 10 in current filter)"
        )
        st.plotly_chart(fig, width="stretch")

# Sentiment label trends (inside filtered set)
if "sentiment_label" in filtered.columns and len(filtered) > 0 and "year" in filtered.columns:
    grp = filtered.groupby(["year", "sentiment_label"]).size().rename("count").reset_index()
    fig = px.line(
        grp, x="year", y="count", color="sentiment_label", markers=True,
        title="Sentiment Label Trends Over Years (filtered)"
    )
    st.plotly_chart(fig, width="stretch")

# Top books over years (optional)
if "title" in filtered.columns and len(filtered) > 0 and "year" in filtered.columns:
    top_books = filtered["title"].value_counts().head(10).index.tolist()
    df_tb = filtered[filtered["title"].isin(top_books)]
    if len(df_tb) > 0:
        grp = df_tb.groupby(["year", "title"]).size().rename("count").reset_index()
        fig = px.line(
            grp, x="year", y="count", color="title", markers=True,
            title="Top 10 Books — Popularity Over the Years (filtered)"
        )
        st.plotly_chart(fig, width="stretch")

# Top authors over years (optional)
if author_col and len(filtered) > 0 and "year" in filtered.columns:
    top_auth = filtered[author_col].value_counts().head(10).index.tolist()
    df_ta = filtered[filtered[author_col].isin(top_auth)]
    if len(df_ta) > 0:
        grp = df_ta.groupby(["year", author_col]).size().rename("count").reset_index()
        fig = px.line(
            grp, x="year", y="count", color=author_col, markers=True,
            title="Top 10 Authors — Popularity Over the Years (filtered)"
        )
        st.plotly_chart(fig, width="stretch")
