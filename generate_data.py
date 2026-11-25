import random
from datetime import date, timedelta

import mysql.connector
from faker import Faker
import os
from dotenv import load_dotenv
load_dotenv()

fake = Faker("en_IN")
random.seed(42)

N_CUSTOMERS = 100
N_FEEDBACK = 500

# ---------- 1. Rating ke hisaab se feedback text ----------
TEXTS = {
    "Positive": [
        "Excellent service, very satisfied.",
        "Fast delivery and great packaging.",
        "Product quality is amazing.",
        "Support team was very helpful.",
        "Smooth payment and quick refund.",
    ],
    "Neutral": [
        "Average experience, nothing special.",
        "Delivery was okay but could be faster.",
        "Product is fine, packaging was average.",
        "Service was acceptable.",
    ],
    "Negative": [
        "Very bad experience, I am disappointed.",
        "Payment was deducted but order was not placed.",
        "Delivery was delayed by many days.",
        "The app keeps crashing and is very slow.",
        "Customer support did not respond to my complaint.",
        "Product arrived damaged and refund is pending.",
    ],
}
CATEGORIES = ["Product", "Payment", "Delivery", "Service", "Technical"]

def pick_text(rating):
    if rating >= 4:
        return random.choice(TEXTS["Positive"])
    if rating == 3:
        return random.choice(TEXTS["Neutral"])
    return random.choice(TEXTS["Negative"])

# ---------- 2. Data generate karo (Extract) ----------
customers, used_emails = [], set()
while len(customers) < N_CUSTOMERS:
    name = fake.name()
    email = f"{name.lower().replace(' ', '.')}{random.randint(1, 999)}@gmail.com"
    if email in used_emails:
        continue
    used_emails.add(email)
    customers.append((name, email, fake.city(), fake.state()))

feedback = []
start = date(2026, 1, 1)
for _ in range(N_FEEDBACK):
    rating = random.choices([1, 2, 3, 4, 5], weights=[15, 15, 20, 25, 25])[0]
    status = random.choice(["Resolved", "Pending", "In Progress"])
    fdate = start + timedelta(days=random.randint(0, 320))
    feedback.append([
        random.randint(1, N_CUSTOMERS),
        pick_text(rating),
        rating,
        random.choice(CATEGORIES),
        status,
        fdate,
    ])

# ---------- 3. Clean / validate (Transform) ----------
before = len(feedback)
feedback = [f for f in feedback if 1 <= f[2] <= 5]          # invalid ratings
feedback = [f for f in feedback if f[1] and f[1].strip()]   # missing text
seen, clean = set(), []
for f in feedback:                                          # duplicates
    key = (f[0], f[5])   # same customer + same date
    if key not in seen:
        seen.add(key)
        clean.append(f)
print(f"Cleaning: {before} -> {len(clean)} rows (removed {before - len(clean)})")

# ---------- 4. MySQL mein load karo (Load) ----------
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
)
cur = conn.cursor()

cur.execute("SET FOREIGN_KEY_CHECKS = 0")
cur.execute("TRUNCATE TABLE feedback")
cur.execute("TRUNCATE TABLE customers")
cur.execute("SET FOREIGN_KEY_CHECKS = 1")

cur.executemany(
    "INSERT INTO customers (customer_name, email, city, state) VALUES (%s, %s, %s, %s)",
    customers,
)
cur.executemany(
    "INSERT INTO feedback (customer_id, feedback_text, rating, category, status, feedback_date) "
    "VALUES (%s, %s, %s, %s, %s, %s)",
    clean,
)
conn.commit()

# ---------- 5. Verify ----------
cur.execute("SELECT COUNT(*) FROM customers")
print("customers:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM feedback")
print("feedback:", cur.fetchone()[0])
cur.close()
conn.close()