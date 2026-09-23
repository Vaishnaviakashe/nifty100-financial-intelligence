-- Q1: Total companies
SELECT COUNT(*) AS company_count
FROM companies;


-- Q2: Row counts for all tables
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL
SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL
SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL
SELECT 'market_cap', COUNT(*) FROM market_cap
UNION ALL
SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL
SELECT 'peer_groups', COUNT(*) FROM peer_groups;


-- Q3: P&L year range
SELECT
    MIN(year) AS earliest_year,
    MAX(year) AS latest_year
FROM profitandloss;


-- Q4: Companies with P&L coverage
SELECT
    company_id,
    COUNT(DISTINCT year) AS year_count
FROM profitandloss
GROUP BY company_id
ORDER BY year_count DESC;


-- Q5: Companies with fewer than 5 P&L years
SELECT
    company_id,
    COUNT(DISTINCT year) AS year_count
FROM profitandloss
GROUP BY company_id
HAVING COUNT(DISTINCT year) < 5
ORDER BY year_count;


-- Q6: NULL values in important P&L fields
SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) AS null_sales,
    SUM(CASE WHEN operating_profit IS NULL THEN 1 ELSE 0 END)
        AS null_operating_profit,
    SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END)
        AS null_net_profit,
    SUM(CASE WHEN eps IS NULL THEN 1 ELSE 0 END) AS null_eps
FROM profitandloss;


-- Q7: Sector distribution
SELECT
    broad_sector,
    COUNT(*) AS company_count
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;


-- Q8: Financial-ratio coverage by company
SELECT
    company_id,
    COUNT(DISTINCT year) AS ratio_years
FROM financial_ratios
GROUP BY company_id
ORDER BY ratio_years DESC;


-- Q9: Peer-group distribution
SELECT
    peer_group_name,
    COUNT(*) AS company_count,
    SUM(CASE WHEN is_benchmark = 1 THEN 1 ELSE 0 END)
        AS benchmark_count
FROM peer_groups
GROUP BY peer_group_name
ORDER BY company_count DESC;


-- Q10: P&L + Balance Sheet join coverage
SELECT
    COUNT(*) AS matching_company_years
FROM profitandloss AS p
INNER JOIN balancesheet AS b
    ON p.company_id = b.company_id
    AND p.year = b.year;