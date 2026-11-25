-- Sentiment distribution
SELECT sentiment, COUNT(*) AS total FROM feedback GROUP BY sentiment;

-- Category-wise average rating
SELECT category, ROUND(AVG(rating),2) AS avg_rating, COUNT(*) AS total
FROM feedback GROUP BY category ORDER BY avg_rating;

-- Pending negative feedback
SELECT f.feedback_id, c.customer_name, f.category, f.feedback_text
FROM feedback f JOIN customers c ON f.customer_id = c.customer_id
WHERE f.sentiment = 'Negative' AND f.status = 'Pending';

-- State-wise average rating
SELECT c.state, ROUND(AVG(f.rating),2) AS avg_rating
FROM feedback f JOIN customers c ON f.customer_id = c.customer_id
GROUP BY c.state ORDER BY avg_rating;

-- Status summary
SELECT status, COUNT(*) AS total FROM feedback GROUP BY status;
