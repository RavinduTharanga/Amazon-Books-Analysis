# streamlit_app.py
import pandas as pd
import streamlit as st
import plotly.express as px

# ================================
# CONFIG
# ================================
INPUT_FILE = "data/amazon_books_reviews_with_merged_categories.csv"
DEFAULT_TOP_N = 20
BAD_CATS = {"other", "great book", "good book", "nice book"}

st.set_page_config(page_title="Amazon Category Trends", layout="wide")

# ================================
# LOAD + CLEAN
# ================================
@st.cache_data
def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year", "merged_category"]).copy()

    df["year"] = df["year"].astype(int)
    df["merged_category"] = df["merged_category"].astype(str).str.strip()

    df = df[~df["merged_category"].str.lower().isin(BAD_CATS)]
    df = df[df["merged_category"] != ""].reset_index(drop=True)

    return df

df = load_and_clean(INPUT_FILE)

# ================================
# SIDEBAR CONTROLS
# ================================
st.sidebar.header("Filters")
top_n = st.sidebar.slider("Top N categories", 5, 50, DEFAULT_TOP_N, 1)

min_year, max_year = int(df["year"].min()), int(df["year"].max())
year_range = st.sidebar.slider("Year range", min_year, max_year, (min_year, max_year), 1)

df = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])].copy()

# Compute top categories AFTER year filter (usually what you want)
overall_counts = df["merged_category"].value_counts()
top_cats = overall_counts.head(top_n).index.tolist()

df_top = df[df["merged_category"].isin(top_cats)].copy()

st.title("Amazon Book Reviews: Category Trends")
st.caption(f"Rows after cleaning: {len(df):,} | Showing top {top_n} categories within selected years")

# ================================
# 1) YEAR × CATEGORY COUNTS (long + pivot)
# ================================
counts_long = (
    df_top.groupby(["year", "merged_category"])
    .size()
    .reset_index(name="count")
)

counts_pivot = (
    counts_long.pivot(index="year", columns="merged_category", values="count")
    .fillna(0)
    .sort_index()
)

# ================================
# CHARTS LAYOUT
# ================================
tab1, tab2, tab3 = st.tabs(["Line (log)", "Stacked proportions", "Heatmap"])

with tab1:
    st.subheader("Review Counts per Category over Years (log scale)")

    fig_line = px.line(
        counts_long,
        x="year",
        y="count",
        color="merged_category",
        markers=True,
        hover_data={"merged_category": True, "year": True, "count": True},
    )
    fig_line.update_yaxes(type="log", title="Number of Reviews (log)")
    fig_line.update_xaxes(title="Year")
    fig_line.update_layout(legend_title_text="Category", height=600)

    st.plotly_chart(fig_line, use_container_width=True)

with tab2:
    st.subheader("Category Proportions per Year (stacked)")

    # proportions: each year sums to 1 (for selected top cats)
    year_totals = counts_pivot.sum(axis=1).replace(0, 1)
    props_pivot = counts_pivot.div(year_totals, axis=0)

    props_long = (
        props_pivot.reset_index()
        .melt(id_vars="year", var_name="merged_category", value_name="proportion")
    )

    fig_stack = px.bar(
        props_long,
        x="year",
        y="proportion",
        color="merged_category",
        barmode="stack",
        hover_data={"merged_category": True, "year": True, "proportion": ":.3f"},
    )
    fig_stack.update_yaxes(title="Proportion")
    fig_stack.update_xaxes(title="Year")
    fig_stack.update_layout(legend_title_text="Category", height=600)

    st.plotly_chart(fig_stack, use_container_width=True)

with tab3:
    st.subheader("Counts Heatmap (Year × Category)")

    # plotly heatmap wants a matrix + labels
    fig_heat = px.imshow(
        counts_pivot,
        aspect="auto",
        labels=dict(x="Category", y="Year", color="Count"),
    )
    fig_heat.update_layout(height=650)

    st.plotly_chart(fig_heat, use_container_width=True)

# Optional: show the underlying tables
with st.expander("Show tables"):
    st.write("Top categories:", top_cats)
    st.dataframe(counts_pivot)
