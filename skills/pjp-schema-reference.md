# PJP (Permanent Journey Plan) Schema Reference

Use this document to accurately formulate SQL queries regarding journey plans, route schedules, and salesman field activities. Always use DB column names directly.

## 🚨 CRITICAL SQL GENERATION RULES

**1. PLAN TYPES**

- `employee_pjp`: Standard weekly/monthly schedule for Sales Personnel (SR/TSO).
- `ba_pjp_customers`: Customer-wise visitation schedule for Brand Ambassadors (BA).
- `manager_journey_plan`: Date-specific travel plans for Managers/Admins.

**2. DATE AND DAY MAPPING**

- `day_id`: Integers `1` (Monday) through `7` (Sunday).
- `week_id`: Usually `1` to `4` for the week of the month.
- `day1`, `day2`, ..., `day7` (in `ba_pjp_customers`): Flags (1=Visited, 0=Not Visited).

**3. SCOPE AND HIERARCHY**

- `sector_id`: Foreign key linking to `zone.uid`.
- `town_id`: Often used interchangeably with Cluster/Territory IDs in legacy queries.

**4. APPROVALS**

- `approved_status`: `1` = Approved, `0` = Pending.

---

## employee_pjp table (SR/TSO Plans)

| Field Name       | Type           | Logical Description                      | Example SQL Value |
| :--------------- | :------------- | :--------------------------------------- | :---------------- |
| `uid`            | `int(11)` (PK) | Unique plan record identifier.           | `1`               |
| `emp_id`         | `int(11)` (FK) | ID of the employee.                      | `3`               |
| `sector_id`      | `int(11)` (FK) | Links to `zone.uid` (The route/sector).  | `1`               |
| `day_id`         | `int(2)`       | Day of the week (1=Mon, 7=Sun).          | `1`               |
| `week_id`        | `int(2)`       | Week of the month (1-4).                 | `2`               |
| `distributor_id` | `int(11)` (FK) | Optional link to a specific distributor. | `6`               |
| `publishtype`    | `int(2)`       | Publication status (1=Live).             | `1`               |

---

## ba_pjp_customers table (BA Plans)

| Field Name        | Type           | Logical Description               | Example SQL Value |
| :---------------- | :------------- | :-------------------------------- | :---------------- |
| `uid`             | `int(11)` (PK) | Unique record identifier.         | `10`              |
| `customer_id`     | `int(11)` (FK) | ID of the customer to be visited. | `542`             |
| `emp_id`          | `varchar(200)` | ID of the BA.                     | `'22'`            |
| `day1` ... `day7` | `int(11)`      | Visit frequency flags (1=Active). | `1`               |

---

## manager_journey_plan table (Admin/Manager)

| Field Name        | Type           | Logical Description                     | Example SQL Value |
| :---------------- | :------------- | :-------------------------------------- | :---------------- |
| `uid`             | `int(11)` (PK) | Unique journey identifier.              | `5`               |
| `admin_id`        | `int(11)` (FK) | Links to `admin.uid`.                   | `1`               |
| `journey_date`    | `date`         | Date of the planned field visit.        | `'2024-03-20'`    |
| `town_id`         | `int(11)`      | Primary location ID (Cluster/Area).     | `3`               |
| `approved_status` | `int(11)`      | Approval state (1=Approved, 0=Pending). | `1`               |
| `approved_by`     | `int(11)`      | ID of the approver.                     | `2`               |
