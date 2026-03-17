# Distributor Schema Reference

Use this document to accurately formulate SQL queries regarding distributors and geographical regions. Always use DB column names directly (no aliases).

## 🚨 CRITICAL SQL GENERATION RULES

**1. TEXT SEARCHING**

- Always use `LIKE '%keyword%'` for text searches (e.g., `name`, `contact_person_name`, `address`).
- Case-insensitivity is preferred for `varchar` fields.

**2. PERFORMANCE: DENORMALIZED FIELDS**

- The `distributor` table is **denormalized**. When the user asks for distributors by Region, Territory, or Cluster, use these columns directly instead of JOINing:
  - `region_name` (e.g., `'North'`, `'South'`)
  - `regional_distributor_name` (e.g., `'KPK Belt'`, `'Sargoda Belt'`)
  - `territory_name` (e.g., `'Peshawar'`, `'Sheikhupura'`)

**3. CHANNELS AND TYPES (ENUMS)**

- `distributor_type`: `'MT'` (Modern Trade), `'GT'` (General Trade).
- `distributor_for`: `'ALL'`, `'SECONDARY'`, `'PRIMARY'`.
- `status`: `'PUBLISHED'`, `'UNPUBLISHED'`, `'ACTIVE'`, `'INACTIVE'`.

**4. BOOLEANS AND FLAGS (0/1)**

- All flags are `INT`. `1` = True/Yes/Active/Locked, `0` = False/No/Inactive/Unlocked.
- Applies to: `gst_status`, `distributor_ntn_status`, `is_verified`, `islocation_locked`.

**5. LOCATION**

- `distributor_loc`: Stores coordinates as a string (e.g., `'33.6204,73.1227'`).
- `checkin_radius`: Allowed distance in meters (e.g., `300.0`).

---

## distributor table

| Field Name                  | Type                | Logical Description                                  | Example SQL Value                       |
| :-------------------------- | :------------------ | :--------------------------------------------------- | :-------------------------------------- |
| `uid`                       | `int(10)` (PK)      | Unique identifier for the distributor.               | `127`                                   |
| `name`                      | `varchar(100)`      | Official business name of the distributor.           | `'Shabbir Enterprises'`                 |
| `contact_person_name`       | `varchar(250)`      | Name of the primary contact person.                  | `'Shabbir Husain'`                      |
| `contact_no`                | `varchar(100)`      | Primary contact phone number.                        | `'03009512009'`                         |
| `distributor_code`          | `varchar(50)`       | Internal ERP or distributor code.                    | `'D-001'`                               |
| `address`                   | `varchar(300)`      | Physical business address.                           | `'Khanna east service Road, Islamabad'` |
| `region_id`                 | `int(15)` (FK)      | ID linking to `region` table.                        | `3`                                     |
| `region_name`               | `varchar(255)`      | **Denormalized** name of the region.                 | `'North'`                               |
| `regionaldistributorid`     | `int(11)` (FK)      | ID linking to `regional_distributor` (Cluster).      | `1`                                     |
| `regional_distributor_name` | `varchar(255)`      | **Denormalized** name of the cluster/area.           | `'KPK Belt'`                            |
| `territory_id`              | `varchar(100)` (FK) | ID linking to `territory` table.                     | `'1'`                                   |
| `territory_name`            | `varchar(255)`      | **Denormalized** name of the territory.              | `'Peshawar'`                            |
| `distributor_type`          | `enum`              | Channel classification (`'MT'`, `'GT'`).             | `'GT'`                                  |
| `distributor_for`           | `enum`              | Trading scope (`'ALL'`, `'SECONDARY'`, `'PRIMARY'`). | `'ALL'`                                 |
| `status`                    | `enum`              | Operational status.                                  | `'PUBLISHED'`                           |
| `gst_status`                | `int(2)`            | Tax status (1=Filer, 0=Non-Filer).                   | `1`                                     |
| `distributor_ntn_status`    | `int(11)`           | NTN registration status.                             | `1`                                     |
| `ntn`                       | `varchar(100)`      | NTN Tax Number.                                      | `'33554005'`                            |
| `stn`                       | `varchar(100)`      | Sales Tax Number.                                    | `'2600210600173'`                       |
| `distributor_loc`           | `varchar(100)`      | GPS Coordinates (latitude, longitude).               | `'33.6204023,73.1227816'`               |
| `islocation_locked`         | `int(2)`            | Flag if check-in location is restricted.             | `1`                                     |
| `checkin_radius`            | `double`            | Allowed radius for check-ins in meters.              | `300.0`                                 |
| `joining_date`              | `date`              | Date when the distributor was onboarded.             | `'2024-01-15'`                          |
| `added_by`                  | `int(11)`           | User ID who added this record.                       | `1`                                     |

---

## Supporting Geography Tables

### region

| Field Name | Type          | Logical Description                      |
| :--------- | :------------ | :--------------------------------------- |
| `uid`      | `int(11)`     | Unique region ID.                        |
| `name`     | `varchar(50)` | Region name (e.g. `'North'`, `'South'`). |
| `status`   | `enum`        | `'PUBLISHED'`, `'UNPUBLISHED'`.          |

### regional_distributor (Area/Cluster)

| Field Name  | Type           | Logical Description            |
| :---------- | :------------- | :----------------------------- |
| `uid`       | `int(11)`      | Unique cluster ID.             |
| `name`      | `varchar(100)` | Area name (e.g. `'KPK Belt'`). |
| `region_id` | `int(11)`      | Links to `region.uid`.         |

### territory

| Field Name      | Type           | Logical Description                  |
| :-------------- | :------------- | :----------------------------------- |
| `uid`           | `int(11)`      | Unique territory ID.                 |
| `territoryname` | `varchar(254)` | Territory name (e.g. `'Peshawar'`).  |
| `regionalid`    | `int(11)`      | Links to `regional_distributor.uid`. |
