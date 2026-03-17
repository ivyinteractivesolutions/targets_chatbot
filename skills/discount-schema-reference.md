# Discount and Schemes Schema Reference

Use this document to accurately formulate SQL queries regarding discounts, trade offers, and promotional schemes. Always use DB column names directly.

## 🚨 CRITICAL SQL GENERATION RULES

**1. DISCOUNT TYPES**

- `discounttype`: `'PERCENT'`, `'WEIGHT'`, `'QTY'`, `'VALUE'`.
- Always check the `discounttype` to interpret the `discount` value correctly.

**2. DATE VALIDITY**

- Always filter by `startdate` and `enddate` to find currently active schemes.
- Example: `WHERE NOW() BETWEEN startdate AND enddate`.

**3. SLABS (QUANTITY RANGES)**

- `slabstart` and `slabend`: Use these for tiered discounts (e.g., "Buy 10 to 20 products for 5% off").
- `slabend = 0` or extremely high values often indicate "and above".

**4. SCOPE AND PRIORITY**

- `item_discount`: Applies to specific items.
- `customer_discount`: Applies to specific customers.
- `discount_on_sum`: Applies to the total order value.

**5. STATUS**

- `publishtype`: `'PUBLISHED'` or `'UNPUBLISHED'`.
- `verification_status`: `'VERIFIED'`.
- `approval_status`: `'APPROVED'`.

---

## item_discount table (Standard Item Schemes)

| Field Name        | Type           | Logical Description                              | Example SQL Value       |
| :---------------- | :------------- | :----------------------------------------------- | :---------------------- |
| `uid`             | `int(11)` (PK) | Unique discount identifier.                      | `501`                   |
| `itemid`          | `int(11)` (FK) | ID of the item this discount applies to.         | `1`                     |
| `distributorid`   | `int(11)` (FK) | Optional: Limit to a specific distributor.       | `0` (Applies to all)    |
| `customer_id`     | `int(11)` (FK) | Optional: Limit to a specific customer.          | `0` (Applies to all)    |
| `slabstart`       | `double`       | Minimum quantity/weight to trigger the discount. | `12.0`                  |
| `slabend`         | `double`       | Maximum quantity/weight for this slab.           | `24.0`                  |
| `discount`        | `varchar(50)`  | The actual discount value.                       | `'5.0'`                 |
| `discounttype`    | `enum`         | Type of discount (`'PERCENT'`, `'QTY'`, etc.).   | `'PERCENT'`             |
| `startdate`       | `datetime`     | When the scheme becomes active.                  | `'2024-01-01 00:00:00'` |
| `enddate`         | `datetime`     | When the scheme expires.                         | `'2024-12-31 23:59:59'` |
| `publishtype`     | `enum`         | `'PUBLISHED'`, `'UNPUBLISHED'`.                  | `'PUBLISHED'`           |
| `approval_status` | `enum`         | `'APPROVED'`, `'NOTAPPROVED'`.                   | `'APPROVED'`            |

---

## group_discount table (Offer/Bundle Schemes)

| Field Name        | Type           | Logical Description                        | Example SQL Value |
| :---------------- | :------------- | :----------------------------------------- | :---------------- |
| `uid`             | `int(11)` (PK) | Unique group discount identifier.          | `1`               |
| `name`            | `varchar(100)` | Name of the promotion.                     | `'Test Group'`    |
| `primary_item_id` | `int(11)` (FK) | The item that must be bought.              | `1`               |
| `offer_item_id`   | `int(11)` (FK) | The item given as a free/discounted offer. | `1`               |
| `status`          | `enum`         | `'ACTIVE'`, `'INACTIVE'`.                  | `'ACTIVE'`        |

---

## discount_on_sum table (Total Order Discounts)

| Field Name     | Type           | Logical Description                      | Example SQL Value |
| :------------- | :------------- | :--------------------------------------- | :---------------- |
| `uid`          | `int(11)` (PK) | Unique identifier.                       | `5`               |
| `startvalue`   | `double`       | Minimum order value to trigger.          | `10000.0`         |
| `endvalue`     | `double`       | Maximum order value for this slab.       | `20000.0`         |
| `discount`     | `double`       | Discount value.                          | `500.0`           |
| `discounttype` | `enum`         | Type (usually `'VALUE'` or `'PERCENT'`). | `'VALUE'`         |
