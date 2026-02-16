# Dimension: customer

## 1. Table Schema

| Column Name               | Data Type | Key Type    | Description                                                                                 | Sample Values                                                                     |
| :------------------------ | :-------- | :---------- | :------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------- |
| `uid`                     | INT       | Unique Key  | Unique system ID for the customers table record.                                            | 1,40, etc                                                                         |
| `cust_id`                 | INT       | Primary Key | Unique identifier for the customer .                                                        | 1001, 1002                                                                        |
| `cust_name`               | VARCHAR   | -           | Name of the company.                                                                        | "Islambad Tea", "UWF Utlimate Whole Foods"                                        |
| `cust_address`            | VARCHAR   | -           | Physical address of the customer.                                                           | "I-10, Islambad", "Gulzaar e Qaid, Rawalpindi", "Near Railway Station Rawalpindi" |
| `cust_gst`                | BINARY    | -           | General Sales Tax on the customer.                                                          | 2.5%, 0.5%                                                                        |
| `cust_ntn`                | BINARY    | -           | National tax number of the customer.                                                        |                                                                                   |
| `cust_lat`                | DOUBLE    | -           | Latitude coordinate of the company's adrress.                                               | 33.6844                                                                           |
| `cust_long`               | DOUBLE    | -           | Longitude coordinate of the company's address.                                              | 73.0479                                                                           |
| `cust_credit_limit`       | INT       | -           |                                                                                             |                                                                                   |
| `cust_registeration_date` | DATE      | -           | The date on which customer got registered.                                                  | Format: YYYY/MM/DD. Example: "2025-03-12"                                         |
| `cust_status`             | BINARY    | -           | Status of the customer (1=Active, 0=Inactive).                                              | 1 for active , 0 for inactive                                                     |
| `cust_publish_type`       | BINARY    | -           | The status of the end customer (not the company but retailer/wholesaler/LMT)                | 1=Publish or 0=unpublish.                                                         |
| `cust_category`           | VARCHAR   | -           | The categories of customer (retailers) based on the amount they are giving for the services | Platinum, Gold,                                                                   |
| `cust_category_last`      | VARCHAR   | -           |                                                                                             |                                                                                   |
| `cust_master_channel`     | VARCHAR   | -           | Top level heirachy that contains name Master Channel and HORICA.                            | HORICA stands for Hotel Office Restaurant Institution Cafe Airport                |
| `cust_master_channel_id`  | INT       | -           | Unique ID assigned to master channel.                                                       | 1,2,3,4,5                                                                         |
| `cust_channel`            | VARCHAR   | -           | Sub level after master channel heirachy that contains LMT, Wholsesale, Retail.              | "Retail", "Wholesale", "Local Modern Trade"                                       |
| `cust_channel_id`         | INT       | -           | Unique ID assigned to customer channel.                                                     | 134, 34, 67                                                                       |
| `cust_sub_channel`        | VARCHAR   | -           | Sub level after customer channel that contains local retailers information.                 | "General Store", "Karyana Store", "Pharmacy", "Medical Store"                     |
| `cust_sub_channel_id`     | INT       | -           | Unique ID assigned to customer sub channel.                                                 | 32, 45, 78                                                                        |
| `cust_section`            | VARCHAR   | -           |                                                                                             |                                                                                   |
| `cust_section_id`         | INT       | -           | Unique ID assigned to Section.                                                              | 1,2,3,5                                                                           |
| `cust_sector`             | VARCHAR   | -           | Specific sector within the city.                                                            | "I-8", "DHA Phase 5"                                                              |
| `cust_sector_id`          | INT       | -           | Unique ID assigned to sector.                                                               | 1,2,3,4,5                                                                         |
| `cust_city`               | VARCHAR   | -           | City where the customer is located.                                                         | "Lahore", "Karachi"                                                               |
| `cust_city_id`            | int       | -           | Unique ID assigned to Customer City.                                                        | 45, 65, 37                                                                        |
| `cust_timestamp`          | DATETIME  | -           | Timestamp at which the customer was created or updated                                      | "2024-01-01 10:00:00", "2023-11-21 03:15:30"                                      |
| `dist_id`                 | VARCHAR   | -           | Code of the distributor.                                                                    | ""                                                                                |

## 2. Relationships & Join Logic

- **Primary Join**: `FactSales.cust_id = customer.cust_id`
- **Secondary Join**: `customer.dist_id = distributor.dist_id` (if applicable)

## 3. Entity Synonyms (Vocabulary)

_Use these to map user terms to database values._

- "Shop", "Store", "Outlet", "Client" -> `cust_name`
- "Location", "Area" -> `cust_sector`, `cust_city`
- "Active Shops" -> `cust_status = 1`

## 4. Business Logic & Filtering Rules

- **Active Only**: ALWAYS filter `cust_status = 1` unless specifically asked for "all" or "inactive".
- **Geography**: Use `cust_city` for broad location and `cust_sector` for specific neighborhood.

## 5. Common Pitfalls (DO NOT DO)

- Do NOT join `cust_city_id` with `DimCity` unless necessary; use `cust_city` name directly if available for simple queries.
- Do NOT assume `cust_name` is unique; always use `cust_id` for distinct counts.

## 6. Predefined SQL Templates (Strict Usage)

### 6.1 Basic Customer Lookup

**Intent**: "Find a shop" or "Details of [Customer]"

```sql
SELECT cust_id, cust_name, cust_address, cust_city, cust_sector, cust_channel
FROM customer
WHERE cust_name LIKE '%{query}%' AND cust_status = 1;
```

### 6.2 Customer Count by Location

**Intent**: "How many shops in [City/Sector]?"

```sql
SELECT COUNT(cust_id) as total_customers
FROM customer
WHERE (cust_city LIKE '%{location}%' OR cust_sector LIKE '%{location}%')
AND cust_status = 1;
```

### 6.3 List Customers in Channel

**Intent**: "List all retail shops"

```sql
SELECT cust_name, cust_address
FROM customer
WHERE cust_channel LIKE '%{channel}%' AND cust_status = 1
LIMIT 50;
```
