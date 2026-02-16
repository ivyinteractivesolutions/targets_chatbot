# Dimension: DimEmployee (Table: `employee`)

## 1. Table Schema

| Column Name                 | Data Type | Key Type | Description                                | Sample Values            |
| :-------------------------- | :-------- | :------- | :----------------------------------------- | :----------------------- |
| `uid`                       | INT       | PK       | Unique system ID for the record.           | 1, 100                   |
| `name`                      | VARCHAR   | -        | Full name of the employee.                 | "Ali Ahmed", "Sara Khan" |
| `email`                     | VARCHAR   | -        | Work email address.                        | "ali@targets.com"        |
| `android_token`             | VARCHAR   | -        | Push notification token for Android.       | "fCM123..."              |
| `ios_device_token`          | VARCHAR   | -        | Push notification token for iOS.           | "aPN456..."              |
| `device_id`                 | VARCHAR   | -        | Unique ID of the physical device.          | "uuid-789"               |
| `check_device_id`           | INT       | -        | Flag to verify device binding (1=Yes).     | 1, 0                     |
| `emp_display_order`         | INT       | -        | Ordering sequence for UI lists.            | 1, 2, 3                  |
| `license_id`                | INT       | -        | License level ID for the user.             | 101, 105                 |
| `current_loc`               | VARCHAR   | -        | Last known GPS coordinates (Lat,Long).     | "33.6,73.0"              |
| `distributor_loc`           | VARCHAR   | -        | GPS of assigned distributor branch.        | "33.7,73.1"              |
| `status`                    | ENUM      | -        | Current app status (ONLINE, OFFLINE, etc). | "ONLINE"                 |
| `password`                  | VARCHAR   | -        | Hashed application password.               | **\*\*\*\***             |
| `passcode`                  | VARCHAR   | -        | App-lock passcode.                         | "1234"                   |
| `img`                       | VARCHAR   | -        | Path to profile avatar.                    | "images/avatar.png"      |
| `mobile`                    | VARCHAR   | -        | Primary contact mobile number.             | "03001234567"            |
| `ismobile_user`             | INT       | -        | Flag if user uses mobile app (1=Yes).      | 1, 0                     |
| `idcard`                    | VARCHAR   | -        | Government ID / CNIC number.               | "37405-1234567-1"        |
| `address`                   | VARCHAR   | -        | Residential address.                       | "House 1, Street 2"      |
| `emptype`                   | ENUM      | -        | Physical description of employment.        | "Full-time", "Intern"    |
| `emptype_id`                | INT       | -        | ID for employment type category.           | 1, 2                     |
| `gst_reg`                   | DOUBLE    | -        | Total GST registered value.                | 500.0                    |
| `gst_non_reg`               | DOUBLE    | -        | Total GST non-registered value.            | 200.0                    |
| `gst_net`                   | INT       | -        | Net GST accumulated.                       | 700                      |
| `advance_gst`               | DOUBLE    | -        | Advance GST payments.                      | 100.0                    |
| `gst_nonfiler`              | DOUBLE    | -        | GST for non-filer status.                  | 50.0                     |
| `gst_value`                 | DOUBLE    | -        | General GST value.                         | 0.17                     |
| `advance_tax`               | DOUBLE    | -        | Advance income tax.                        | 1000.0                   |
| `advance_tax_nonfiler`      | DOUBLE    | -        | Advance tax for non-filers.                | 2000.0                   |
| `bdo`                       | INT       | -        | Business Development Officer flag.         | 1, 0                     |
| `ismerchant`                | INT       | -        | Flag if user is a merchant.                | 0, 1                     |
| `isfoc`                     | INT       | -        | Flag if user can handle FOC items.         | 1, 0                     |
| `edit_scheme`               | INT       | -        | Permission to edit schemes (1=Yes).        | 0, 1                     |
| `edit_order`                | INT       | -        | Permission to edit orders.                 | 1, 0                     |
| `edit_scheme_on_delivery`   | INT       | -        | Edit scheme at delivery time.              | 0                        |
| `stock_availability`        | INT       | -        | Can check stock availability.              | 1                        |
| `is_spotseller`             | INT       | -        | Flag for spot selling capability.          | 0                        |
| `ischeckinenable`           | INT       | -        | Is GPS check-in required.                  | 1                        |
| `customerMandatoryField`    | INT       | -        | Customer fields mandatory (1=Yes).         | 1                        |
| `shift_start`               | TIME      | -        | Working shift start time.                  | "09:00:00"               |
| `shift_end`                 | TIME      | -        | Working shift end time.                    | "18:00:00"               |
| `emp_code`                  | VARCHAR   | -        | Employee's internal company code.          | "EMP-001"                |
| `isstock_order`             | INT       | -        | Can perform stock orders.                  | 1                        |
| `is_brandAmbassador`        | INT       | -        | Is a brand ambassador.                     | 0                        |
| `canEditCustomer`           | INT       | -        | Permission to edit customer data.          | 1                        |
| `app_version`               | INT       | -        | Current mobile app version.                | 25                       |
| `is_formvisible`            | INT       | -        | Permission to see custom forms.            | 1                        |
| `is_quotationvisible`       | INT       | -        | Permission to see quotations.              | 1                        |
| `checkin_radius`            | INT       | -        | Allowed radius for check-in (meters).      | 300                      |
| `job_status`                | ENUM      | -        | Employment status (ACTIVE/DISCONTINUE).    | "ACTIVE"                 |
| `joiningdate`               | DATE      | -        | Official date of joining.                  | "2023-01-01"             |
| `bdo_id`                    | INT       | -        | Associated BDO ID.                         | 10                       |
| `discount_limit_percent`    | DOUBLE    | -        | Max % discount allowed.                    | 5.0                      |
| `discount_limit_value`      | DOUBLE    | -        | Max $ discount value.                      | 500.0                    |
| `is_checkoutlocked`         | INT       | -        | Block checkout if location unmatched.      | 1                        |
| `is_checkinlocked`          | INT       | -        | Block checkin if location unmatched.       | 1                        |
| `enter_stock`               | INT       | -        | Permission to enter inventory.             | 1                        |
| `is_primaryOrder`           | INT       | -        | Can book primary orders.                   | 0                        |
| `can_add_customer`          | INT       | -        | Can create new customers.                  | 1                        |
| `book_oao`                  | INT       | -        | Book Order Against Order flag.             | 0                        |
| `unique_outlets_assigned`   | INT       | -        | Count of unique outlets in route.          | 50                       |
| `total_outlets_assigned`    | INT       | -        | Total outlets in periodic visit plan.      | 150                      |
| `can_bypass_discounts`      | INT       | -        | Overwrite automated discounts.             | 0                        |
| `can_deliver_order`         | INT       | -        | Dedicated delivery capability.             | 1                        |
| `booking_radius`            | INT       | -        | Radius for booking orders.                 | 300                      |
| `can_charge_manual`         | INT       | -        | Can manually charge customer.              | 0                        |
| `can_add_cat`               | VARCHAR   | -        | Allowed categories to add.                 | "1,2"                    |
| `can_add_payment`           | INT       | -        | Can record incoming payments.              | 1                        |
| `can_edit_tp`               | INT       | -        | Can edit Trade Price.                      | 0                        |
| `sku_img`                   | INT       | -        | Visual SKU list enabled.                   | 1                        |
| `emp_off_day`               | INT       | -        | Designated off day (e.g. 5=Friday).        | 5                        |
| `timestamp`                 | TIMESTAMP | -        | Record last update time.                   | ...                      |
| `licensed`                  | INT       | -        | Licensing flag.                            | 1                        |
| `active_license`            | INT       | -        | Active license state.                      | 1                        |
| `booking`                   | INT       | -        | Permission: Manage Bookings.               | 1                        |
| `returns`                   | INT       | -        | Permission: Manage Returns.                | 1                        |
| `damages`                   | INT       | -        | Permission: Manage Damages.                | 1                        |
| `expiries`                  | INT       | -        | Permission: Manage Expiries.               | 1                        |
| `quotes`                    | INT       | -        | Permission: Manage Quotes.                 | 1                        |
| `notes`                     | INT       | -        | Permission: Manage Notes.                  | 1                        |
| `photos`                    | INT       | -        | Permission: Manage Photos.                 | 1                        |
| `tertiary`                  | INT       | -        | Permission: Manage Tertiary Sales.         | 1                        |
| `merchant`                  | INT       | -        | Permission: Manage Merchandising.          | 1                        |
| `forms`                     | INT       | -        | Permission: Manage Forms.                  | 1                        |
| `spotsale`                  | INT       | -        | Permission: Manage Spot Sales.             | 1                        |
| `assets`                    | INT       | -        | Permission: Manage Assets.                 | 1                        |
| `payment`                   | INT       | -        | Permission: Manage Payments.               | 1                        |
| `designation`               | VARCHAR   | -        | Official job title.                        | "Sales Officer"          |
| `position`                  | VARCHAR   | -        | Org hierarchy position.                    | "Standard"               |
| `user_email`                | VARCHAR   | -        | Secondary Login Email.                     | "user@example.com"       |
| `token`                     | VARCHAR   | -        | Auth Token.                                | ...                      |
| `password_reset_token`      | VARCHAR   | -        | Reset token.                               | ...                      |
| `email_verified`            | INT       | -        | Email verification status.                 | 1                        |
| `region_id`                 | INT       | FK       | Assigned Region ID.                        | 5                        |
| `territory_id`              | INT       | FK       | Assigned Territory ID.                     | 12                       |
| `distributor_id`            | INT       | FK       | Primary Distributor ID.                    | 100                      |
| `regionaldistributor_id`    | INT       | FK       | Regional Distributor ID.                   | 100                      |
| `access_role_ids`           | VARCHAR   | -        | List of assigned role IDs.                 | "1,5,9"                  |
| `assigned_skus`             | VARCHAR   | -        | List of specific SKU IDs assigned.         | "10,12,14"               |
| `last_password_change`      | DATETIME  | -        | Timestamp of last password update.         | ...                      |
| `user_phone`                | VARCHAR   | -        | Work phone number.                         | "03001111111"            |
| `admin_check`               | INT       | -        | Admin check level.                         | 0                        |
| `assigned_distributors`     | VARCHAR   | -        | Comma-separated list of Dist IDs.          | "100,101"                |
| `location_from_distributor` | INT       | -        | Inherit loc from distributor.              | 0                        |
| `fb_device_id`              | VARCHAR   | -        | Firebase device ID.                        | ...                      |
| `marital_status`            | VARCHAR   | -        | Marital status.                            | "Single"                 |
| `dob`                       | DATE      | -        | Date of Birth.                             | "1990-01-01"             |
| `gender`                    | ENUM      | -        | Gender (Male/Female/Other).                | "Male"                   |
| `age`                       | INT       | -        | Current age in years.                      | 34                       |
| `joining_date`              | DATE      | -        | Redundant joining date field.              | "2023-01-01"             |
| `resign_date`               | DATE      | -        | Date of resignation.                       | NULL                     |
| `contract_start_date`       | DATE      | -        | Start of current contract.                 | ...                      |
| `contract_end_date`         | DATE      | -        | End of current contract.                   | ...                      |
| `reason`                    | VARCHAR   | -        | Reason for leaving/status change.          | ...                      |
| `salary`                    | VARCHAR   | -        | String representing general salary.        | "50000"                  |
| `about`                     | LONGTEXT  | -        | Personal bio/notes.                        | ...                      |
| `islocation_locked`         | INT       | -        | Lock actions to GPS location.              | 1                        |
| `checkin_location`          | VARCHAR   | -        | Hardcoded check-in location coords.        | "0,0"                    |
| `can_approve_journey`       | INT       | -        | Can approve travel/route plans.            | 0                        |
| `user_ids`                  | VARCHAR   | -        | Associated user IDs.                       | "1,2,3"                  |
| `project_participant`       | VARCHAR   | -        | Role in specific projects.                 | "participant"            |
| `department_id`             | INT       | FK       | Department ID.                             | 5                        |
| `admin_id`                  | INT       | FK       | Admin Manager ID.                          | 1                        |
| `manager_id`                | INT       | FK       | Immediate Manager ID.                      | 10                       |
| `role`                      | ENUM      | -        | System role (employee/manager).            | "employee"               |
| `company_id`                | INT       | FK       | Associated Company ID.                     | 1                        |
| `access_group`              | VARCHAR   | -        | Permission group name.                     | "Default"                |
| `can_mark_attendance`       | TINYINT   | -        | Can mark attendance from app.              | 1                        |
| `user_type`                 | VARCHAR   | -        | Type code (e.g. 101).                      | "101"                    |
| `is_active`                 | TINYINT   | -        | Master active flag (1=Yes).                | 1                        |
| `is_approval_required`      | TINYINT   | -        | Are actions pending approval.              | 0                        |
| `base_salary`               | DECIMAL   | -        | Numeric base salary value.                 | 45000.00                 |
| `designation_id`            | INT       | FK       | ID for designation matching.               | 2                        |
| `grade_id`                  | INT       | FK       | Salary/Org grade ID.                       | 4                        |
| `branch_id`                 | INT       | FK       | Assigned branch ID.                        | 1                        |
| `father_name`               | VARCHAR   | -        | Father's name.                             | "Ahmed Ali"              |
| `cnic`                      | VARCHAR   | -        | National Identity Card number.             | "37405..."               |
| `passport_no`               | VARCHAR   | -        | International passport number.             | ...                      |
| `personal_email`            | VARCHAR   | -        | Private contact email.                     | ...                      |
| `work_phone`                | VARCHAR   | -        | Landline/Office extension.                 | ...                      |
| `bank_name`                 | VARCHAR   | -        | Salary bank name.                          | "HBL"                    |
| `bank_account_number`       | VARCHAR   | -        | IBAN/Account Number.                       | "PK..."                  |
| `employment_type`           | ENUM      | -        | Standard employment category.              | "Full-time"              |
| `confirmation_date`         | DATE      | -        | Date of permanent status.                  | ...                      |
| `sku_group_id`              | INT       | FK       | Specific SKU portfolio group ID.           | 10                       |

## 2. Relationships & Join Logic

- **Primary Join**: `FactSales.fact_employee_id = employee.uid` (or `emp_id` equivalent)
- **Reporting Hierarchy**: `manager_id` links back to `employee.uid`
- **Location Hierarchy**: `region_id`, `territory_id`, `distributor_id` link to their respective dimensions.

## 3. Entity Synonyms (Vocabulary)

_Use these to map user terms to database values._

- "Sales Rep", "Agent", "Salesman", "Staff", "User" -> `employee`
- "Designation", "Rank", "Position" -> `designation`
- "Salary", "Earnings", "Pay" -> `base_salary` or `salary`
- "Mobile Users" -> `ismobile_user = 1`
- "Active Employees" -> `is_active = 1` AND `job_status = 'ACTIVE'`

## 4. Business Logic & Filtering Rules

- **Status Check**: Always verify both `is_active = 1` AND `job_status = 'ACTIVE'` for current workforce.
- **Role Scoping**: If user asks for "Managers", use `role = 'manager'`.
- **Permissions**: Use the 0/1 flags (like `booking`, `returns`, `payment`) to check if a user _is allowed_ to do something.

## 5. Common Pitfalls (DO NOT DO)

- Do NOT share `password` or `passcode` in plaintext if the system outputs them; mask them.
- Do NOT confuse `joiningdate` (DATE) with `joining_date` (DATE); they are redundant, use `joining_date` if possible.
- Do NOT assume `mobile` is the same as `user_phone`.

## 6. Predefined SQL Templates (Strict Usage)

### 6.1 Employee Profile Lookup

**Intent**: "Who is [Name]?" or "Find employee [Mobile]"

```sql
SELECT name, designation, mobile, emp_code, job_status, emptype
FROM employee
WHERE (name LIKE '%{query}%' OR mobile LIKE '%{query}%' OR emp_code = '{query}')
AND is_active = 1;
```

### 6.2 Team List (by Manager)

**Intent**: "Who reports to [Manager Name]?"

```sql
SELECT name, designation, role
FROM employee
WHERE manager_id = (SELECT uid FROM employee WHERE name LIKE '%{manager_name}%' LIMIT 1)
AND is_active = 1;
```

### 6.3 Capacity/Permissions Audit

**Intent**: "Who can collect payments?"

```sql
SELECT name, mobile, designation
FROM employee
WHERE can_add_payment = 1 AND is_active = 1;
```
