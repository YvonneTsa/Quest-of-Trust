-- Observable transaction volume and value by date; no fraud label is referenced.
SELECT date(Timestamp) AS transaction_date,
       COUNT(*) AS transaction_count,
       ROUND(SUM(Amount), 2) AS transaction_value,
       ROUND(AVG(Amount), 2) AS average_amount
FROM transactions
GROUP BY date(Timestamp)
ORDER BY transaction_date;
