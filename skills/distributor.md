# Dimension: DimDistributor (Table: `distributor`)

## 1. Table Schema

| Column Name              | Data Type | Key Type    | Description                                                                                 | Sample Values                           |
| :----------------------- | :-------- | :---------- | :------------------------------------------------------------------------------------------ | :-------------------------------------- |
| `uid`                    | INT       | Primary Key | Unique system ID for the distributor.                                                       | 1, 693                                  |
| `name`                   | VARCHAR   | -           | Name of the distributor company.                                                            | "Capital Trading", "Metro Distributors" |
| `contact_person_name`    | VARCHAR   | -           | Name of the primary contact person.                                                         | "Ali Khan"                              |
| `contact_no`             | VARCHAR   | -           | Contact phone number of the primary contact person.                                         | "0300-1234567"                          |
| `regionaldistributorid`  | INT       | -           | ID of the regional distributor parent.                                                      | 10, 20                                  |
| `distributor_code`       | VARCHAR   | -           | Internal code for the distributor.                                                          | "DIST-001"                              |
| `distributor_loc`        | VARCHAR   | -           | GPS coordinates (Lat,Long).                                                                 | "33.6844,73.0479"                       |
| `territory_id`           | VARCHAR   | -           | Territory code assigned to distributor.                                                     | "T-05", "T-12"                          |
| `email`                  | VARCHAR   | -           | Official communication email.                                                               | "info@distributor.com"                  |
| `address`                | VARCHAR   | -           | Physical warehouse/office address.                                                          | "Warehouse 4, Industrial Area"          |
| `gst_status`             | INT       | -           | GST registration status (1=Reg, 0=Non).                                                     | 1, 0                                    |
| `ntn`                    | VARCHAR   | -           | National Tax Number.                                                                        | "1234567-8"                             |
| `stn`                    | VARCHAR   | -           | Sales Tax Number.                                                                           | "7654321-0"                             |
| `status`                 | ENUM      | -           | Current status (PUBLISHED/UNPUBLISHED).                                                     | "PUBLISHED"                             |
| `timestamp`              | TIMESTAMP | -           | Last update timestamp.                                                                      | ...                                     |
| `sole_type`              | INT       | -           | Sole proprietorship type ID.                                                                | 1                                       |
| `region_id`              | INT       | -           | Associated Region ID.                                                                       | 5                                       |
| `sole_id`                | INT       | -           | Unique sole identifier. The distributor that distributes the product to other distributors. | 0                                       |
| `is_verified`            | INT       | -           | verification flag.                                                                          | 1                                       |
| `province`               | VARCHAR   | -           | Province of operation.                                                                      | "Punjab"                                |
| `distributor_for`        | ENUM      | -           | Channel focus (ALL/PRIMARY/SECONDARY).                                                      | "SECONDARY"                             |
| `distributor_ntn_status` | INT       | -           | Specific NTN verification status for distributor.                                           | 1                                       |
| `cnic`                   | VARCHAR   | -           | National Identity Card number of distributor.                                               | "37405-..."                             |
| `fbr_name`               | VARCHAR   | -           | Official FBR registered name for the distributor.                                           | "Capital Trading FBR"                   |

## 2. Relationships & Join Logic

- **Primary Join**: `FactSales.distributor_id = distributor.uid`
- **Employee Join**: `employee.distributor_id = distributor.uid`
- **Customer Join**: `customer.dist_id = distributor.uid` (Note: Check if `dist_id` is VARCHAR or INT in `customer`)
- **Hierarchy**: `regionaldistributorid` links to parent distributor record.

## 3. Entity Synonyms (Vocabulary)

_Use these to map user terms to database values._

- "Distributor", "Dist", "Wholesaler", "Partner" -> `distributor`
- "Distributor Code" -> `distributor_code`
- "Tax ID", "NTN" -> `ntn`
- "FBR Registration" -> `gst_status` or `fbr_name`
- "Primary Focus" -> `distributor_for = 'PRIMARY'`
- "Active Distributors" -> `status = 'PUBLISHED'`

## 4. Business Logic & Filtering Rules

- **Active Only**: ALWAYS filter `status = 'PUBLISHED'` unless specifically asked for unpublished records.
- **Hierarchy**: If user asks for "Sub-distributors", filter by `regionaldistributorid`.
- **Location**: Use `region_name` or `province` for broad geography.

## 5. Common Pitfalls (DO NOT DO)

- Do NOT assume `uid` and `distributor_code` are the same; always join on `uid` for foreign keys.
- Do NOT share `password` or `license_id` in responses.

## 6. Predefined SQL Templates (Strict Usage)

### 6.1 Distributor Profile Lookup

**Intent**: "Details of distributor [Name/Code]"

```sql
SELECT name, distributor_code, contact_person_name, contact_no, address, province
FROM distributor
WHERE (name LIKE '%{query}%' OR distributor_code = '{query}')
AND status = 'PUBLISHED';
```

### 6.2 Revenue by Category (Join Hint)

**Intent**: "Total sales for distributor [Name]"

```sql
SELECT d.name, SUM(f.fact_item_net_value) as TotalRevenue
FROM fact f
JOIN distributor d ON f.fact_employee_id = (SELECT uid FROM employee WHERE distributor_id = d.uid LIMIT 1) -- Note: Complex join via employee
-- OR if Fact has distributor_id:
-- JOIN distributor d ON f.distributor_id = d.uid
WHERE d.name LIKE '%{name}%'
GROUP BY d.name;
```

### 6.3 Compliance Audit

**Intent**: "List non-filer distributors"

```sql
SELECT name, distributor_code, email
FROM distributor
WHERE gst_status = 0 AND status = 'PUBLISHED';
```
