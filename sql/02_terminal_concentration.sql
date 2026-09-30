-- Find endpoints with unusually high event concentration for investigation.
SELECT Terminal_ID,
       COUNT(*) AS transaction_count,
       COUNT(DISTINCT Customer_ID) AS distinct_customers,
       ROUND(SUM(Amount), 2) AS transaction_value
FROM transactions
GROUP BY Terminal_ID
ORDER BY transaction_count DESC
LIMIT 20;
