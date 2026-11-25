import os

import mysql.connector
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

load_dotenv()

st.set_page_config(page_title="Customer Feedback Analytics", layout="wide")
st.title("Customer Feedback Sentiment Analytics")

COLORS = {"Positive": "green", "Neutral": "gold", "Negative": "red"}


# ---------- DB connection ----------
def get_conn():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


# ---------- Data loaders ----------
@st.cache_data
def load_data():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM feedback_summary")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    df = pd.DataFrame(rows, columns=cols)
    df["feedback_date"] = pd.to_datetime(df["feedback_date"])
    return df


@st.cache_data
def load_ai_data():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT feedback_id, feedback_text, rating, category FROM feedback")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    d = pd.DataFrame(rows, columns=["feedback_id", "feedback_text", "rating", "category"])

    analyzer = SentimentIntensityAnalyzer()

    def ai_label(text):
        s = analyzer.polarity_scores(text)["compound"]
        if s >= 0.05:
            return "Positive"
        if s <= -0.05:
            return "Negative"
        return "Neutral"

    def rating_label(r):
        if r >= 4:
            return "Positive"
        if r == 3:
            return "Neutral"
        return "Negative"

    d["ai_sentiment"] = d["feedback_text"].apply(ai_label)
    d["rating_sentiment"] = d["rating"].apply(rating_label)
    d["match"] = d["ai_sentiment"] == d["rating_sentiment"]
    return d


df = load_data()

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
categories = st.sidebar.multiselect(
    "Category", sorted(df["category"].unique()), default=sorted(df["category"].unique())
)
sentiments = st.sidebar.multiselect(
    "Sentiment", sorted(df["sentiment"].unique()), default=sorted(df["sentiment"].unique())
)
statuses = st.sidebar.multiselect(
    "Status", sorted(df["status"].unique()), default=sorted(df["status"].unique())
)

fdf = df[
    df["category"].isin(categories)
    & df["sentiment"].isin(sentiments)
    & df["status"].isin(statuses)
]

tab1, tab2 = st.tabs(["Overview", "AI vs Rating Sentiment"])

# ================= TAB 1: OVERVIEW =================
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Feedback", len(fdf))
    c2.metric("Average Rating", round(fdf["rating"].mean(), 2) if len(fdf) else 0)
    c3.metric("Pending", int((fdf["status"] == "Pending").sum()))
    neg_pct = (fdf["sentiment"] == "Negative").mean() * 100 if len(fdf) else 0
    c4.metric("Negative %", f"{neg_pct:.1f}%")

    left, right = st.columns(2)

    with left:
        sent_count = fdf["sentiment"].value_counts().reset_index()
        sent_count.columns = ["sentiment", "count"]
        fig1 = px.pie(
            sent_count, names="sentiment", values="count", hole=0.5,
            title="Sentiment Distribution", color="sentiment",
            color_discrete_map=COLORS,
        )
        st.plotly_chart(fig1, use_container_width=True)

    with right:
        cat_rating = fdf.groupby("category")["rating"].mean().reset_index()
        fig2 = px.bar(cat_rating, x="category", y="rating", title="Average Rating by Category")
        st.plotly_chart(fig2, use_container_width=True)

    left2, right2 = st.columns(2)

    with left2:
        status_count = fdf["status"].value_counts().reset_index()
        status_count.columns = ["status", "count"]
        fig3 = px.bar(status_count, x="status", y="count", title="Status Breakdown")
        st.plotly_chart(fig3, use_container_width=True)

    with right2:
        state_rating = fdf.groupby("state")["rating"].mean().sort_values().reset_index()
        fig4 = px.bar(
            state_rating, x="rating", y="state", orientation="h",
            title="Average Rating by State",
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("Feedback Records")
    st.dataframe(fdf, use_container_width=True)

# ================= TAB 2: AI vs RATING =================
with tab2:
    ai = load_ai_data()

    st.subheader("AI (VADER) vs Rating-based Sentiment")

    m1, m2 = st.columns(2)
    m1.metric("Match %", f"{ai['match'].mean() * 100:.1f}%")
    m2.metric("Mismatched records", int((~ai["match"]).sum()))

    col_a, col_b = st.columns(2)

    with col_a:
        ai_count = ai["ai_sentiment"].value_counts().reset_index()
        ai_count.columns = ["sentiment", "count"]
        fig5 = px.pie(
            ai_count, names="sentiment", values="count", hole=0.5,
            title="VADER Sentiment Distribution", color="sentiment",
            color_discrete_map=COLORS,
        )
        st.plotly_chart(fig5, use_container_width=True)

    with col_b:
        cmp = ai.groupby(["rating_sentiment", "ai_sentiment"]).size().reset_index(name="count")
        fig6 = px.bar(
            cmp, x="rating_sentiment", y="count", color="ai_sentiment", barmode="group",
            title="Rating Sentiment vs VADER Sentiment",
            color_discrete_map=COLORS,
        )
        st.plotly_chart(fig6, use_container_width=True)

    st.subheader("Mismatched Records")
    st.dataframe(
        ai[~ai["match"]][["feedback_id", "feedback_text", "rating", "rating_sentiment", "ai_sentiment"]],
        use_container_width=True,
    )