# Dimension: DimProduct

## 1. Table Schema

| Column Name           | Data Type | Key Type    | Description                                                | Sample Values                       |
| :-------------------- | :-------- | :---------- | :--------------------------------------------------------- | :---------------------------------- |
| `uid`                 | INT       | Primary Key | Unique system ID for the product table record.             | 1,2,3                               |
| `item_category`       | VARCHAR   | -           | Broad category classification.                             | "Stationery", "Dairy"               |
| `item_category_id`    | INT       | -           | Unique ID assignend to each category.                      |                                     |
| `item_subcategory`    | VARCHAR   | -           | More specific classification of the category.              | "Writing Instruments", "UHT Milk"   |
| `item_subcategory_id` | INT       | -           | Unique ID assigned to each subcategory.                    |                                     |
| `item_brand`          | VARCHAR   | -           | Brand name of the item.                                    | "Dollar", "Nestle"                  |
| `item_brand_id`       | INT       | -           | Unique ID assigned to each brand.                          |                                     |
| `item_group`          | VARCHAR   | -           | Grouping the item based on the similraties of the item.    | "General Trade", "Modern Trade"     |
| `item_group_id`       | INT       | -           | Unique ID assigned to each group.                          |                                     |
| `item_name`           | VARCHAR   | -           | Full name of the product.                                  | "Dollar Pen Blue", "Olpers Milk 1L" |
| `item_id`             | INT       | -           | Unique identifier for the product item.                    | 101, 102                            |
| `item_carton_size`    | INT       | -           | Number of units per carton.                                | 12, 24                              |
| `item_box_size`       | INT       | -           | Number of units per box.                                   | 10, 50                              |
| `item_weight`         | INT       | -           | Weight of the item (grams/kg).                             | 500 kg, 1000 kg                     |
| `item_gst_type`       | INT       | -           |                                                            |                                     |
| `item_code`           | VARCHAR   | -           | SKU or product code.                                       | "SKU-001", "DP-BLU"                 |
| `item_status`         | BINARY    | -           | 1 = Active, 0 = Inactive.                                  | 1, 0                                |
| `item_tax_type`       | INT       | -           |                                                            |                                     |
| `item_timestamp`      | DATETIME  | -           | Timestamp at which the product was enterd into the system. | "2024-01-01 10:00:00"               |

## 2. Relationships & Join Logic

- **Primary Join**: `FactSales.item_id = product.item_id`
- **Hierarchies**: `item_group` -> `item_category` -> `item_subcategory` -> `item_brand` -> `item_name`

## 3. Entity Synonyms (Vocabulary)

_Use these to map user terms to database values._

- "SKU", "Article" -> `item_name` or `item_code`
- "Available Items" -> `item_status = 1`
- "Pack Size" -> `item_carton_size` or `item_box_size`

## 4. Business Logic & Filtering Rules

- **Active Only**: ALWAYS filter `item_status = 1` unless specifically asked for discontinued items.
- **Brand Level**: If user asks about a brand (e.g., "Dollar"), filter by `item_brand` OR `item_name LIKE '%Dollar%'`.

## 5. Common Pitfalls (DO NOT DO)

- Do NOT sum `item_weight` unless calculating shipment load.
- Do NOT assume `item_name` is unique across different pack sizes; check `item_code` if precision is needed.

## 6. Predefined SQL Templates (Strict Usage)

### 6.1 Basic Product Lookup

**Intent**: "Find a product" or "List items in category"

```sql
SELECT item_id, item_name, item_brand, item_category, item_varton_size
FROM product
WHERE (item_name LIKE '%{query}%' OR item_category LIKE '%{query}%')
AND item_status = 1;
```

### 6.2 Count Items per Brand

**Intent**: "How many products does [Brand] have?"

```sql
SELECT item_brand, COUNT(item_id) as ProductCount
FROM product
WHERE item_brand LIKE '%{brand_name}%' AND item_status = 1
GROUP BY item_brand;
```

### 6.3 List Variations (Pack Sizes)

**Intent**: "Show pack sizes for [Product]"

```sql
SELECT item_name, item_carton_size, item_box_size
FROM product
WHERE item_name LIKE '%{product}%' AND item_status = 1;
```
