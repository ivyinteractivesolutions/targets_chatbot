# Dimension: FactSales (Table: `fact`)

## 1. Table Schema

| Column Name                 | Data Type | Key Type    | Description                                 | Sample Values |
| :-------------------------- | :-------- | :---------- | :------------------------------------------ | :------------ |
| `uid`                       | INT       | Primary Key | Unique system ID for the fact table record. | 1, 234, 523   |
| `fact_employee_id`          | INT       | -           | ID of the employee who took the order.      | 501, 502      |
| `fact_customer_id`          | INT       | -           | ID of the customer who placed the order.    | 1001, 1002    |
| `fact_order_id`             | INT       | -           | Unique ID for the order (not PK of table).  | 5001, 5002    |
| `fact_order_date`           | DATE      | -           | Date the order was placed.                  | "2024-01-01"  |
| `fact_dsr_date`             | DATE      | -           |                                             |               |
| `fact_delivery_date`        | DATE      | -           |                                             |               |
| `fact_order_lat`            | DOUBLE    | -           |                                             |               |
| `fact_order_lng`            | DOUBLE    | -           |                                             |               |
| `fact_order_checkin_time`   | DATETIME  | -           |                                             |               |
| `fact_order_checkout_time`  | DATETIME  | -           |                                             |               |
| `fact_order_initial_status` | INT       | -           |                                             |               |
| `fact_order_status`         | INT       | -           |                                             |               |
| `fact_order_initial_value`  | DOUBLE    | -           |                                             |               |
| `fact_order_revision_count` | INT       | -           |                                             |               |
| `fact_order_notes_id`       | INT       | -           |                                             |               |
| `fact_item_id`              | INT       | -           |                                             |               |
| `fact_item_qty`             | INT       | -           |                                             |               |
| `fact_item_foc`             | INT       | -           |                                             |               |
| `fact_item_unit_price`      | DOUBLE    | -           |                                             |               |
| `fact_item_dp_exc`          | DOUBLE    | -           |                                             |               |
| `fact_item_dp_incl`         | DOUBLE    | -           |                                             |               |
| `fact_item_tp_incl`         | DOUBLE    | -           |                                             |               |
| `fact_item_value`           | DOUBLE    | -           |                                             |               |
| `fact_item_value_after_d1`  | DOUBLE    | -           |                                             |               |
| `fact_item_value_after_d2`  | DOUBLE    | -           |                                             |               |
| `fact_item_value_after_d3`  | DOUBLE    | -           |                                             |               |
| `fact_item_value_after_d4`  | DOUBLE    | -           |                                             |               |
| `fact_item_value_after_d5`  | DOUBLE    | -           |                                             |               |
| `fact_item_value_after_d6`  | DOUBLE    | -           |                                             |               |
| `fact_item_value_after_gst` | DOUBLE    | -           |                                             |               |
| `fact_item_value_after_adt` | DOUBLE    | -           |                                             |               |
| `fact_item_gst_percent`     | DOUBLE    | -           |                                             |               |
| `fact_item_adt_percent`     | DOUBLE    | -           |                                             |               |
| `fact_item_net_value`       | DOUBLE    | -           |                                             |               |
| `fact_timestamp`            | TIMESTAMP | -           |                                             |               |
| `fact_delivery_time`        | TIME      | -           |                                             |               |
| `fact_order_time`           | TIME      | -           |                                             |               |

## 2. Relationships & Join Logic

- **Customer Join**: `fact.fact_customer_id = customer.cust_id`
- **Product Join**: `fact.fact_item_id = product.item_id`
- **Employee Join**: `fact.fact_employee_id = employee.emp_id`
- **Date Join**: `fact.fact_order_date = date.dt_date`

## 3. Entity Synonyms (Vocabulary)

_Use these to map user terms to database values._

- "Revenue", "Sales", "Total Amount" -> `SUM(fact_item_net_value)`
- "Volume", "Quantity", "Units" -> `SUM(fact_item_qty)`
- "Orders" -> `COUNT(DISTINCT fact_order_id)`
- "Productive Calls" -> `COUNT(DISTINCT fact_order_id) WHERE fact_item_net_value > 0`

## 4. Business Logic & Filtering Rules

- **Valid Sales**: ALWAYS filter `fact_order_status != 8` (Cancelled). Usually `status IN (1, 2, 5)` implies valid bookings/deliveries.
- **Net vs Gross**: Default to "Net Value" (`fact_item_net_value`) for revenue unless "Gross" is asked.
- **Date Range**: Always check if a date range is implied. If not, ask or default to "Current Month".

## 5. Common Pitfalls (DO NOT DO)

- Do NOT count `uid` for orders; use `fact_order_id` (a single order has multiple rows, one per item).
- Do NOT sum `fact_item_unit_price`; it makes no sense.

## 6. Predefined SQL Templates (Strict Usage)

### 6.1 Total Sales (Revenue)

**Intent**: "Total sales in [Date/Location]"

```sql
SELECT SUM(f.fact_item_net_value) as TotalRevenue
FROM fact f
JOIN customer c ON f.fact_customer_id = c.cust_id
WHERE f.fact_order_date BETWEEN '{start_date}' AND '{end_date}'
AND f.fact_order_status != 8
AND c.cust_city = '{city}';
```

### 6.2 Top Selling Products

**Intent**: "Best selling items"

```sql
SELECT p.item_name, SUM(f.fact_item_qty) as TotalUnits, SUM(f.fact_item_net_value) as TotalValue
FROM fact f
JOIN product p ON f.fact_item_id = p.item_id
WHERE f.fact_order_status != 8
GROUP BY p.item_name
ORDER BY TotalValue DESC
LIMIT 10;
```

### 6.3 Drop Size (Avg Order Value)

**Intent**: "Average order value?"

```sql
SELECT SUM(fact_item_net_value) / COUNT(DISTINCT fact_order_id) as AvgOrderValue
FROM fact
WHERE fact_order_status != 8;
```
