# Employee Schema Reference

Use this document to accurately formulate SQL queries regarding employees, hierarchy, and field activities. Always use DB column names directly.

## 🚨 CRITICAL SQL GENERATION RULES

**1. EMPLOYEE TYPES (`emptype`)**

- Common values include: `'S.R'` (Sales Representative), `'B.A'` (Brand Ambassador), `'T.S.O'` (Territory Sales Officer), `'A.S.M'` (Area Sales Manager), `'Z.S.M'` (Zonal Sales Manager).
- Always use `LIKE` for searching if the user describes a role loosely.

**2. HIERARCHY AND ASSIGNMENTS**

- `assigned_distributors`: A comma-separated string of distributor IDs (e.g., `'1,5,10'`). Use `FIND_IN_SET()` or `LIKE` for matching specific distributors.
- `user_ids`: Often used for subordinates or related user mappings.

**3. AVAILABILITY AND STATUS**

- `status`: `'ONLINE'` or `'OFFLINE'`. Use for real-time app status.
- `job_status`: `'ACTIVE'` or `'DISCONTINUE'`. Use to filter currently employed staff.

**4. ACTIVITY LIMITS**

- `checkin_radius` & `booking_radius`: Integer values in meters (e.g., `300`).
- `is_checkoutlocked` & `is_checkinlocked`: Flags (0/1) for location-based locking.

**5. LOCATION**

- `current_loc`: Stores `'lat,long'` string.

---

## employee table

| Field Name              | Type            | Logical Description                                   | Example SQL Value            |
| :---------------------- | :-------------- | :---------------------------------------------------- | :--------------------------- |
| `uid`                   | `int(11)` (PK)  | Unique employee identifier.                           | `15`                         |
| `name`                  | `varchar(250)`  | Full name of the employee.                            | `'Muhammad Ali'`             |
| `emp_code`              | `varchar(100)`  | Employee code or HR ID.                               | `'EMP-102'`                  |
| `email`                 | `varchar(300)`  | Email address (often used as login).                  | `'ali@example.com'`          |
| `mobile`                | `varchar(50)`   | Contact mobile number.                                | `'0301-1234567'`             |
| `address`               | `varchar(250)`  | Physical address of the employee.                     | `'Street 5, Area 2, Lahore'` |
| `emptype`               | `varchar(100)`  | Role/Designation code.                                | `'S.R'`                      |
| `job_status`            | `enum`          | Employment status (`'ACTIVE'`, `'DISCONTINUE'`).      | `'ACTIVE'`                   |
| `status`                | `enum`          | App connection status (`'ONLINE'`, `'OFFLINE'`).      | `'OFFLINE'`                  |
| `current_loc`           | `varchar(100)`  | Last recorded GPS position.                           | `'31.5204,74.3587'`          |
| `assigned_distributors` | `varchar(2000)` | Comma-separated list of Distributor IDs.              | `'1,6,12'`                   |
| `is_brandAmbassador`    | `int(2)`        | Flag if employee is a BA (1=Yes, 0=No).               | `0`                          |
| `can_approve_journey`   | `tinyint(4)`    | Management permission for PJP approval (1=Yes, 0=No). | `1`                          |
| `checkin_radius`        | `int(5)`        | Allowed radius (meters) for customer check-in.        | `300`                        |
| `booking_radius`        | `int(5)`        | Allowed radius (meters) for placing orders.           | `300`                        |
| `joiningdate`           | `date`          | Date of joining the company.                          | `'2023-05-10'`               |
| `license_id`            | `int(250)`      | Links to `license` table.                             | `1`                          |
| `emp_off_day`           | `int(2)`        | Weekly off day index.                                 | `5`                          |

---

## Supporting Tables

### license

| Field Name     | Type           | Logical Description                |
| :------------- | :------------- | :--------------------------------- |
| `uid`          | `int(11)`      | Unique license ID.                 |
| `company_name` | `varchar(250)` | Name of the sub-company or entity. |
