# Customer Schema Reference

Use this document to accurately formulate SQL queries regarding customers. Always use DB column names directly (no aliases).

## 🚨 CRITICAL SQL GENERATION RULES

**1. STRING SEARCHING**

- Always use `LIKE '%keyword%'` for text searches (e.g., `businessname`, `customername`, `address`).
- Match Case: MySQL is case-insensitive by default for `varchar`.

**2. PERFORMANCE: DENORMALIZED FIELDS**

- When asked for **Business Type**, **Category**, or **Master Channel**, DO NOT JOIN other tables.
- Instead, search directly in these pre-joined denormalized fields:
  - `business_type_name` (e.g., `'Retail'`, `'Wholesale'`)
  - `business_cat_name` (e.g., `'Retail'`, `'Wholesale'`, `'LMT'`, `'Primary Stock Purchase'`)
  - `master_channel_name` (e.g., `'General Trade'`)

**3. BOOLEANS AND FLAGS (0/1)**

- All flags are `INT`.
- `1` = True / Yes / Active / Filer / Verified.
- `0` = False / No / Inactive / Non-Filer / Unverified.
- Applies to: `is_verified`, `gst_status`, `ntn_status`, `tax_active_status`, `is_whatsapp`, `is_countersale`, `is_ba`, `can_book_floor_stock`, `has_asset`.

**4. STATUSES**

- `publishtype`: Uses `ENUM('PUBLISHED', 'UNPUBLISHED')`.
- `status`: Uses `VARCHAR`, defaults to `'ACTIVE'`.

**5. LOCATION & ADDRESS**

- `location`: Stores raw coordinates as a string (e.g., `'34.0157,71.5869'`).
- For city/area searches, use `address LIKE '%Islamabad%'`.

---

## customer table

| Field Name            | Type           | Logical Description                                 | Example SQL Value                     |
| :-------------------- | :------------- | :-------------------------------------------------- | :------------------------------------ |
| `uid`                 | `int(10)` (PK) | Unique primary identifier for the customer.         | `3`                                   |
| `businessname`        | `varchar(250)` | Registered name of the shop or business.            | `'Bilal General Store'`               |
| `customername`        | `varchar(250)` | Name of the primary contact person.                 | `'Bilal'`                             |
| `is_verified`         | `int(2)`       | Flag indicating if the customer is verified.        | `1`                                   |
| `idcard`              | `varchar(20)`  | CNIC or ID card number.                             | `'12345-6789012-3'`                   |
| `cnic_front`          | `varchar(200)` | URL/path to the front image of the CNIC.            | `'http://.../142062720.jpg'`          |
| `cnic_back`           | `varchar(200)` | URL/path to the back image of the CNIC.             | `'http://.../back.jpg'`               |
| `customer_image`      | `varchar(250)` | URL/path to the customer's profile photo.           | `'http://.../customer.jpg'`           |
| `email`               | `varchar(250)` | Customer's email address.                           | `'info@store.com'`                    |
| `address`             | `varchar(250)` | Full physical address of the business.              | `'Street 12, Bilal Town, Abbottabad'` |
| `mobile`              | `varchar(15)`  | Primary mobile contact number.                      | `'03115292701'`                       |
| `location`            | `varchar(50)`  | GPS Coordinates (latitude, longitude).              | `'34.0157938,71.5869079'`             |
| `zoneid`              | `int(10)` (FK) | ID linking to the `zone` table.                     | `21`                                  |
| `category_id`         | `int(3)`       | Internal ID for business category.                  | `2`                                   |
| `typeid`              | `int(11)`      | Internal ID for business type.                      | `2`                                   |
| `is_ba`               | `int(1)`       | Flag for Business Associate status.                 | `0`                                   |
| `shelf_rent`          | `double`       | Monthly rent paid for shelf space.                  | `500.0`                               |
| `credit_limit`        | `double`       | Maximum allowed credit amount.                      | `50000.0`                             |
| `publishtype`         | `enum`         | System visibility (`'PUBLISHED'`, `'UNPUBLISHED'`). | `'PUBLISHED'`                         |
| `status`              | `varchar(300)` | Operational status (e.g., `'ACTIVE'`).              | `'ACTIVE'`                            |
| `is_whatsapp`         | `int(2)`       | Flag for WhatsApp availability.                     | `1`                                   |
| `gst_no`              | `varchar(30)`  | GST Registration number.                            | `'3277876171213'`                     |
| `ntn_no`              | `varchar(50)`  | NTN Tax number.                                     | `'0000'`                              |
| `gst_status`          | `int(2)`       | Tax filer status (1=Filer, 0=Non-filer).            | `1`                                   |
| `tax_active_status`   | `int(2)`       | Flag if tax status is currently active.             | `1`                                   |
| `gst_value`           | `double`       | GST percentage for filers.                          | `18.0`                                |
| `advance_tax`         | `double`       | Advance tax rate for filers.                        | `1.0`                                 |
| `added_by`            | `int(11)` (FK) | ID of the user who added this customer.             | `61`                                  |
| `timestamp`           | `timestamp`    | Record creation/update time.                        | `'2022-10-11 23:48:23'`               |
| `business_type_name`  | `varchar(255)` | **Denormalized** Business Type Name.                | `'Retail'`                            |
| `business_cat_name`   | `varchar(255)` | **Denormalized** Business Category Name.            | `'Retail'`                            |
| `master_channel_name` | `varchar(255)` | **Denormalized** Master Channel Name.               | `'General Trade'`                     |

---

## Supporting Tables (Reference Only)

### zone

| Field Name | Type           | Logical Description             |
| :--------- | :------------- | :------------------------------ |
| `uid`      | `int(11)`      | Unique zone identifier.         |
| `name`     | `varchar(100)` | Name of the zone/sector.        |
| `cityid`   | `int(11)`      | ID linking to `city` table.     |
| `status`   | `enum`         | `'PUBLISHED'`, `'UNPUBLISHED'`. |

### business_category / business_type

_Note: Use `customer.business_cat_name` or `customer.business_type_name` for queries asking by name._

| Table Name          | `name` (Example Values)                                        |
| :------------------ | :------------------------------------------------------------- |
| `business_category` | `'Wholesale'`, `'Retail'`, `'LMT'`, `'Primary Stock Purchase'` |
| `business_type`     | `'Wholesale'`, `'Retail'`, `'LMT'`                             |

### city

| Field Name     | Type           | Logical Description        | Example      |
| :------------- | :------------- | :------------------------- | :----------- |
| `uid`          | `int(10)`      | Unique city identifier.    | `1`          |
| `name`         | `varchar(200)` | Name of the city.          | `'Peshawar'` |
| `territory_id` | `varchar(250)` | ID linking to a territory. | `'1'`        |
