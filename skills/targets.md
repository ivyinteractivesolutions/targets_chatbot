# Dimension: FactTargets (Table: `targets`)

## 1. Table Schema

| Column Name       | Data Type | Key Type    | Description                                                    | Sample Values         |
| :---------------- | :-------- | :---------- | :------------------------------------------------------------- | :-------------------- |
| `uid`             | INT       | Primary Key | Unique system ID for the target table record.                  | 1, 10                 |
| `tr_uid`          | INT       | -           | Internal unique identifier for the target.                     | 5001, 5002            |
| `tr_Item_id`      | INT       | -           | Item ID that is linked to product table of this system.        | 101, 102              |
| `tr_employee_id`  | INT       | -           | Employe ID that is linked to the employe table of this system, | 501, 502              |
| `tr_month_year`   | VARCHAR   | -           | Target month/year (Format: 'MM-YYYY').                         | "01-2024", "12-2025"  |
| `tr_timestamp`    | DATETIME  | -           | Timestamp of when the target was created or updated.           | "2024-01-01 10:00:00" |
| `tr_target_value` | DOUBLE    | -           | Monetary target value (Currency).                              | 50000.0, 150000.0     |
| `tr_target_pcs`   | DOUBLE    | -           | Quantity/Pieces in the target.                                 | 100.0, 500.0          |

## 2. Relationships & Join Logic

- **Product Join**: `targets.tr_Item_id = product.item_id`
- **Employee Join**: `targets.tr_employee_id = employee.uid` (check if links to `uid` or `emp_id`)
- **Time Logic**: `tr_month_year` is a string 'MM-YYYY'. Need to convert or match against `DimDate` components.

## 3. Entity Synonyms (Vocabulary)

_Use these to map user terms to database values._

- "Goal", "Quota", "Objective", "Assigned Target" -> `tr_target_value` (money) or `tr_target_pcs` (qty)
- "Target Value" -> `tr_target_value`
- "Unit Target", "PCS Target" -> `tr_target_pcs`

## 4. Business Logic & Filtering Rules

- **Monthly Focus**: Targets are typically tracked and assigned per month.
- **Value vs Volume**: If the user asks for "Target" without specifying, use `tr_target_value`. If they mention "Pcs" or "Units", use `tr_target_pcs`.

## 5. Common Pitfalls (DO NOT DO)

- Do NOT sum `tr_uid`.
- Do NOT assume `tr_month_year` can be used in dynamic date arithmetic without casting or string manipulation.

## 6. Predefined SQL Templates (Strict Usage)

### 6.1 Employee Monthly Target

**Intent**: "What is my target for this month?"

```sql
SELECT e.name, t.tr_month_year, t.tr_target_value, t.tr_target_pcs
FROM targets t
JOIN employee e ON t.tr_employee_id = e.uid
WHERE e.name LIKE '%{name}%' AND t.tr_month_year = '{mm-yyyy}';
```

### 6.2 Product Target Comparison

**Intent**: "Compare Target vs Sales for [Product]"

```sql
-- Target Part
SELECT SUM(tr_target_value) as TotalTarget
FROM targets
WHERE tr_Item_id = (SELECT item_id FROM product WHERE item_name = '{product_name}' LIMIT 1)
AND tr_month_year = '{mm-yyyy}';
```

### 6.3 Aggregated Targets (Annual)

**Intent**: "Annual target for 2024"

```sql
SELECT SUM(tr_target_value) as YearlyTarget
FROM targets
WHERE tr_month_year LIKE '%-2024';
```
