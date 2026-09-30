-- Surface low-value events occurring after rapid prior customer activity.
SELECT Transaction_ID, Timestamp, Customer_ID, Terminal_ID, Amount,
       Tx_Count_Prior_24h, Customer_Terminal_Prior_Count
FROM behavior_features
WHERE Amount <= 5 AND Tx_Count_Prior_24h >= 2
ORDER BY Tx_Count_Prior_24h DESC, Timestamp;
