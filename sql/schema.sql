CREATE DATABASE IF NOT EXISTS customer_intelligence;
USE customer_intelligence;

CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE,
    city VARCHAR(100),
    state VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    feedback_text TEXT NOT NULL,
    rating INT,
    category VARCHAR(50),
    sentiment VARCHAR(20),
    sentiment_score DECIMAL(4,2),
    status VARCHAR(30),
    feedback_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE OR REPLACE VIEW feedback_summary AS
SELECT f.feedback_id, c.customer_name, c.city, c.state,
       f.category, f.rating, f.sentiment, f.sentiment_score,
       f.status, f.feedback_date
FROM feedback f
JOIN customers c ON f.customer_id = c.customer_id;
