# Dimension: Customer Segmentation (RFM)

## 1. Table Schema

| Column Name                | Data Type | Key Type | Description | Sample Values |
| :------------------------- | :-------- | :------- | :---------- | :------------ |
| `rfm_customer_id`          | INT       | -        |             |               |
| `rfm_employee_id`          | INT       | -        |             |               |
| `first_order_date`         | DATE      | -        |             |               |
| `last_order_date`          | DATE      | -        |             |               |
| `current_period_value`     | FLOAT     | -        |             |               |
| `current_month_net_value`  | FLOAT     | -        |             |               |
| `previous_month_net_value` | FLOAT     | -        |             |               |
| `last_month_net_value`     | FLOAT     | -        |             |               |
| `Recency`                  | FLOAT     | -        |             |               |
| `Frequency`                | FLOAT     | -        |             |               |
| `Monetary`                 | FLOAT     | -        |             |               |
| `RecencyScore`             | INT       | -        |             |               |
| `FrequencyScore`           | INT       | -        |             |               |
| `MonetaryScore`            | INT       | -        |             |               |
| `RFM_SCORE`                | INT       | -        |             |               |
| `Segment`                  | VARCHAR   | -        |             |               |
| `RecencyName`              | VARCHAR   | -        |             |               |
| `FrequencyName`            | VARCHAR   | -        |             |               |
| `MonetaryName`             | VARCHAR   | -        |             |               |
| `Time_Period`              | VARCHAR   | -        |             |               |
| `Analysis_Month`           | VARCHAR   | -        |             |               |

## 2. Relationships & Join Logic

- **Primary Join**: `customer_segmentation.rfm_customer_id = customer.cust_id`
- **Secondary Join**: `customer_segmentation.rfm_employee_id = employee.emp_id` (if applicable)

## 3. Entity Synonyms (Vocabulary)

_Use these to map user terms to database values._

- "Best Customers", "Top Clients" -> `Segment = 'Champions'` or `RFM_SCORE >= 500`
- "Inactive", "Churned" -> `Segment = 'Lost'` or `RecencyScore = 1`
- "Loyal" -> `FrequencyScore >= 4`
- "Big Spenders" -> `MonetaryScore >= 4`

## 4. Business Logic & Filtering Rules

- **Analysis Period**: Always check `Analysis_Month` if multiple months exist. Default to the latest month if not specified.
- **RFM Definition**: Recency (How recent), Frequency (How often), Monetary (How much). High scores (5) are good.

## 5. Common Pitfalls (DO NOT DO)

- Do NOT sum `RFM_SCORE`; it is a qualitative label (555 is a label, not a number 555).
- Do NOT confuse `current_period_value` with `Monetary`. `Monetary` is the derived metric; `current_period_value` is the raw sales.

## 6. Predefined SQL Templates (Strict Usage)

### 6.1 Segment Count

**Intent**: "How many customers are At Risk?"

```sql
SELECT Segment, COUNT(rfm_customer_id) as CustomerCount
FROM customer_segmentation
WHERE Segment LIKE '%{query}%'
GROUP BY Segment;
```

### 6.2 Customer Details by Segment

**Intent**: "List my Champion customers"

```sql
SELECT c.cust_name, s.Segment, s.RFM_SCORE, s.last_order_date
FROM customer_segmentation s
JOIN customer c ON s.rfm_customer_id = c.cust_id
WHERE s.Segment = '{segment_name}'
ORDER BY s.MonetaryScore DESC
LIMIT 50;
```

### 6.3 High Value but At Risk

**Intent**: "Big spenders who haven't bought recently"

```sql
SELECT c.cust_name, s.RecencyScore, s.MonetaryScore, s.last_order_date
FROM customer_segmentation s
JOIN customer c ON s.rfm_customer_id = c.cust_id
WHERE s.MonetaryScore >= 4 AND s.RecencyScore <= 2
ORDER BY s.current_period_value DESC;
```
