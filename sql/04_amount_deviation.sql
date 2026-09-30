-- Compare amounts with the customer's profile; unusual is a signal, not proof.
SELECT Transaction_ID, Timestamp, Customer_ID, Amount,
       Typical_Spend, ROUND(Amount_To_Typical_Spend, 2) AS spend_multiple,
       Rule_Score, Rule_Reasons
FROM behavior_features
WHERE Amount_To_Typical_Spend >= 3
ORDER BY Amount_To_Typical_Spend DESC
LIMIT 100;
