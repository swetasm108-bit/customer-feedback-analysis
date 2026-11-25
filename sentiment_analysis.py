import pandas as pd
import mysql.connector
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
from dotenv import load_dotenv
load_dotenv()

def validate_data(df):
    print("\n--- DATA VALIDATION REPORT ---")

    print("Missing values:")
    print(df.isnull().sum())

    print("Duplicate feedback IDs:",
          df["feedback_id"].duplicated().sum())

    print("Invalid ratings:",
          (~df["rating"].between(1, 5)).sum())

    print("Empty feedback:",
          df["feedback_text"].fillna("").str.strip().eq("").sum())

    print("Feedback with extra spaces:",
          (df["feedback_text"].fillna("") !=
           df["feedback_text"].fillna("").str.strip()
           ).sum())
    if (
        df.isnull().sum().sum() == 0
        and df["feedback_id"].duplicated().sum() == 0
        and df["rating"].between(1, 5).all()
        and df["feedback_text"].fillna("").str.strip().ne("").all()
    ):
        print("\nData validation successful!")
    else:
        print("\nData validation failed! Please check the data.")
# 1. MySQL se data padho
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
)
cursor = conn.cursor()
cursor.execute("SELECT feedback_id, feedback_text, rating, category FROM feedback")
rows = cursor.fetchall()
df = pd.DataFrame(rows, columns=["feedback_id", "feedback_text", "rating", "category"])
validate_data(df)
print(df.isnull().sum())
print("Duplicate feedback IDs:", df["feedback_id"].duplicated().sum())
print("Invalid ratings:", (~df["rating"].between(1, 5)).sum())
empty_feedback = df["feedback_text"].str.strip().eq("").sum()

print("Empty feedback:", empty_feedback)
df["feedback_length"] = df["feedback_text"].str.len()

print("Shortest feedback:", df["feedback_length"].min())
print("Longest feedback:", df["feedback_length"].max())
print("Average feedback length:", round(df["feedback_length"].mean(), 2))
extra_spaces = (
    df["feedback_text"] != df["feedback_text"].str.strip()
).sum()

print("Feedback with extra spaces:", extra_spaces)
cursor.close()
conn.close()

# 2. VADER se text ka sentiment nikalo
analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    score = analyzer.polarity_scores(text)["compound"]
    if score >= 0.05:
        return "Positive", score
    elif score <= -0.05:
        return "Negative", score
    return "Neutral", score

df[["ai_sentiment", "ai_score"]] = df["feedback_text"].apply(
    lambda t: pd.Series(get_sentiment(t))
)

# 3. Rating-based sentiment se compare
def rating_sentiment(r):
    if r >= 4:
        return "Positive"
    elif r == 3:
        return "Neutral"
    return "Negative"

df["rating_sentiment"] = df["rating"].apply(rating_sentiment)
df["match"] = df["ai_sentiment"] == df["rating_sentiment"]

# 4. Save aur dekho
df.to_csv("feedback_ai_sentiment.csv", index=False)
print(df[["feedback_id", "rating", "rating_sentiment", "ai_sentiment", "match"]])
print("Match %:", round(df["match"].mean() * 100, 1))