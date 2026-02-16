# Dimension: DimGeography (Table: `geography`)

## 1. Table Schema

| Column Name                   | Data Type | Key Type | Description                                  | Sample Values               |
| :---------------------------- | :-------- | :------- | :------------------------------------------- | :-------------------------- |
| `uid`                         | INT       | PK       | Unique system ID for the hierarchy record.   | 1, 100                      |
| `geo_region`                  | VARCHAR   | -        | Name of the administrative region.           | "North", "South", "Central" |
| `geo_region_id`               | INT       | FK       | ID of the region.                            | 1, 2                        |
| `geo_area`                    | VARCHAR   | -        | Name of the sub-region or area.              | "Islamabad", "Rawalpindi"   |
| `geo_area_id`                 | INT       | FK       | ID of the area.                              | 10, 11                      |
| `geo_territory`               | VARCHAR   | -        | Name of the specific sales territory.        | "I-8 Sector", "Blue Area"   |
| `geo_territory_id`            | INT       | FK       | ID of the territory.                         | 101, 102                    |
| `geo_distributor`             | VARCHAR   | -        | Name of the distributor in this territory.   | "Ali Traders", "Khan Dist"  |
| `geo_distributor_id`          | INT       | FK       | Unique ID of the distributor.                | 5001                        |
| `geo_distributor_status`      | BINARY    | -        | Status (1=Active).                           | 1, 0                        |
| `geo_distributor_code`        | VARCHAR   | -        | Business code of the distributor.            | "D-001"                     |
| `geo_distributor_publishtype` | BINARY    | -        | Flag for visibility.                         | 1                           |
| `geo_employee`                | VARCHAR   | -        | Name of the employee assigned to this level. | "John Doe"                  |
| `geo_employee_id`             | INT       | FK       | ID of the employee.                          | 2001                        |
| `geo_employee_joining_date`   | DATE      | -        | Date employee joined this hierarchy level.   | "2023-01-01"                |
| `geo_employee_Status`         | BINARY    | -        | Status of the employee (1=Active).           | 1                           |
| `geo_employee_type`           | VARCHAR   | -        | Role type (e.g. Sales Officer).              | "SO", "ASM"                 |
| `geo_employee_category`       | INT       | -        | Category level of the employee.              | 1, 2                        |
| `geo_employee_unique_shops`   | INT       | -        | Count of shops assigned to this employee.    | 45, 60                      |
| `geo_timestamp`               | DATETIME  | -        | Last update timestamp.                       | ...                         |

## 2. Relationships & Join Logic

- **Fact Table Join**: Frequently joined with `FactSales` on `geo_employee_id` or `geo_distributor_id`.
- **Level Joins**: This table is already denormalized (flattened), so no internal joins between Area/Region/Territory are needed.

## 3. Entity Synonyms (Vocabulary)

_Use these to map user terms to database values._

- "Location Hierarchy", "Org Tree", "Sales Structure" -> `geography`
- "Zone", "Region" -> `geo_region`
- "City", "Area" -> `geo_area`
- "Sector", "Territory" -> `geo_territory`
- "Staff assigned to area" -> `geo_employee`

## 4. Business Logic & Filtering Rules

- **Status Filter**: Use `geo_distributor_status = 1` and `geo_employee_Status = 1` for active mapping checks.
- **Deduplication**: Since one area can have multiple entries (e.g. per employee), use `DISTINCT` when listing areas or regions.

## 5. Common Pitfalls (DO NOT DO)

- Do NOT sum `geo_employee_unique_shops` across multiple rows without deduplicating by employee, as they might appear in multiple territory mappings.
- Do NOT confuse `geo_distributor_id` with `geo_distributor_code`.

## 6. Predefined SQL Templates (Strict Usage)

### 6.1 Hierarchy Lookup

**Intent**: "What area does [Territory] belong to?"

```sql
SELECT geo_region, geo_area, geo_territory
FROM geography
WHERE geo_territory LIKE '%{territory_name}%'
LIMIT 1;
```

### 6.2 Team by Region

**Intent**: "List all employees in the [Region] region"

```sql
SELECT DISTINCT geo_employee, geo_employee_type
FROM geography
WHERE geo_region LIKE '%{region_name}%'
AND geo_employee_Status = 1;
```

### 6.3 Distributor Geographic Reach

**Intent**: "Which territories are covered by [Distributor]?"

```sql
SELECT DISTINCT geo_territory, geo_area
FROM geography
WHERE geo_distributor LIKE '%{distributor_name}%'
OR geo_distributor_code = '{query}';
```
