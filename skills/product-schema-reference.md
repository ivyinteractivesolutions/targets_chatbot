# Product Schema Reference

Use this document to accurately formulate SQL queries regarding products, SKUs, pricing, and categories. Always use DB column names directly.

## 🚨 CRITICAL SQL GENERATION RULES

**1. SKU VS PRODUCT**

- `item` is the master table for **SKUs** (specific packing/size).
- `product` represents the **Brand/Line** (e.g. 'White Rose Hair Remover').
- Use `item.name` for the full SKU name (e.g., `'WR ROSE LOTION 125G'`).

**2. PRICING AND TAXES**

- `unitprice`: Primary selling price.
- `ctn_size`: Units in a master carton.
- `box_size`: Units in a display/inner box.
- `gst_value` & `gst_nonfiler`: Percentage tax rates (e.g., `18.0`).

**3. PERFORMANCE: DENORMALIZED FIELDS**

- The `item` table is **denormalized**. Use these columns directly for filtering instead of JOINing:
  - `category_name` (e.g., `'White Rose Hair Remover'`)
  - `brand_name` (e.g., `'NL Cosmetics'`)
  - `product_name` (e.g., `'White Rose Hair Remover'`)
  - `group_name`

**4. STATUS**

- `status`: `'PUBLISHED'` or `'UNPUBLISHED'`. Only published items are active in the system.

---

## item table (SKU Level)

| Field Name             | Type           | Logical Description                     | Example SQL Value           |
| :--------------------- | :------------- | :-------------------------------------- | :-------------------------- |
| `uid`                  | `int(11)` (PK) | Unique SKU identifier.                  | `1`                         |
| `name`                 | `varchar(250)` | Full name of the SKU.                   | `'WR ROSE LOTION 125G'`     |
| `sku_code`             | `varchar(100)` | SKU code or Barcode.                    | `'001'`                     |
| `unit_type`            | `varchar(20)`  | Base unit of measure (usually `'Pcs'`). | `'Pcs'`                     |
| `unitprice`            | `double`       | Trade Price (TP) per unit.              | `450.0`                     |
| `purchaseprice`        | `double`       | Cost Price (CP) per unit.               | `400.0`                     |
| `ctn_size`             | `double`       | Number of units per master carton.      | `48`                        |
| `box_size`             | `double`       | Number of units per inner box.          | `6`                         |
| `brand_name`           | `varchar(255)` | **Denormalized** brand name.            | `'NL Cosmetics'`            |
| `category_name`        | `varchar(255)` | **Denormalized** category name.         | `'White Rose Hair Remover'` |
| `product_name`         | `varchar(255)` | **Denormalized** parent product line.   | `'White Rose Hair Remover'` |
| `gst_value`            | `double`       | GST percentage for Filers.              | `18.0`                      |
| `gst_nonfiler`         | `double`       | GST percentage for Non-Filers.          | `22.0`                      |
| `advance_tax`          | `double`       | Advance Income Tax for Filers.          | `0.5`                       |
| `advance_tax_nonfiler` | `double`       | Advance Income Tax for Non-Filers.      | `1.0`                       |
| `status`               | `enum`         | Publication status (`'PUBLISHED'`).     | `'PUBLISHED'`.              |

---

## Supporting Tables

### product (Product Lines)

| Field Name    | Type           | Logical Description                           |
| :------------ | :------------- | :-------------------------------------------- |
| `uid`         | `int(10)`      | Product ID.                                   |
| `name`        | `varchar(200)` | Line name (e.g. `'Nine Leaves Beauty Soap'`). |
| `category_id` | `int(11)`      | Links to `product_category`.                  |

### product_category (Top Level)

| Field Name | Type           | Logical Description                 |
| :--------- | :------------- | :---------------------------------- |
| `uid`      | `int(11)`      | Category ID.                        |
| `name`     | `varchar(150)` | Category name (e.g. `'Cosmetics'`). |
