-- Observe authentication changes and outcomes by channel and time of day.
SELECT Channel, Auth_Type, Auth_Result,
       COUNT(*) AS transaction_count,
       ROUND(AVG(Amount), 2) AS average_amount,
       ROUND(AVG(Is_Night), 3) AS night_share
FROM behavior_features
GROUP BY Channel, Auth_Type, Auth_Result
ORDER BY transaction_count DESC;
