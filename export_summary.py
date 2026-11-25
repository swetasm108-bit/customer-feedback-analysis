import csv
import mysql.connector
import os
from dotenv import load_dotenv
load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
)
cur = conn.cursor()
cur.execute("SELECT * FROM feedback_summary")
rows = cur.fetchall()
headers = [d[0] for d in cur.description]

with open("feedback_summary.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

print("Exported rows:", len(rows))
cur.close()
conn.close()