-- Rank shared endpoints by connected customers and transaction activity.
-- This is a lead-generation view, not a finding of fraud.
SELECT Terminal_ID, Merchant_ID, Distinct_Customers, Transaction_Count,
       Distinct_Days, ROUND(Total_Amount, 2) AS total_amount
FROM terminal_network_summary
ORDER BY Distinct_Customers DESC, Transaction_Count DESC
LIMIT 25;
