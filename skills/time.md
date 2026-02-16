# Dimension: DimDate (Time)

## 1. Table Schema

| Column Name          | Data Type | Key Type    | Description                                     | Sample Values                                                                                                                |
| :------------------- | :-------- | :---------- | :---------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------- |
| `uid`                | INT       | Primary Key | Unique system ID for the date table record.     | 1, 299, 531, etc.                                                                                                            |
| `dt_date`            | DATE      | -           | The specific calendar date.                     | Format: YYYY/MM/DD where Y=year, M=month, D=day. Example: "2024-01-01", "2024-12-31"                                         |
| `dt_year`            | INT       | -           | The year part of the date.                      | 2024, 2025                                                                                                                   |
| `dt_month_name`      | VARCHAR   | -           | Full name of the month.                         | "January", "August"                                                                                                          |
| `dt_days_in_month`   | INT       | -           | Total number of days in 1 month.                | 31=Jan,28=Feb,31=March,30=April,31=May,30=June,31=July,31,30,31,30,31                                                        |
| `dt_day`             | INT       | -           | Day in numeric format                           | 1=Monday, 2=Tuesday, 3=wednesday, 4=Thursday, 5=Friday, 6=Saturday, 7=Sunday                                                 |
| `dt_day_name`        | VARCHAR   | -           | Name of the weekday.                            | "Monday","Tuesday","Wednesday","Thursday", "Friday", "Saturday", "Sunday"                                                    |
| `dt_day_of_week`     | INT       | -           | Day number of week (usually 1=Monday).          | 1,2,3,4,5,6,7                                                                                                                |
| `dt_day_of_year`     | INT       | -           | Day number in numric format for the whole year. | 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,,25,26,27,28,29,30,31,32,33,34,3,36,37,38,39,40,41,42,....365 |
| `dt_quarter_of_year` | INT       | -           | Quarter number (1,2,3,4).                       | 1=[January,Februray,March], 2=[April,May,June], 3=[July,August,September], 4=[October,November,December]                     |
| `dt_week_of_year`    | INT       | -           | Week number (1-52).                             | 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,....,52 |
| `dt_week_of_month`   | INT       | -           | Week number in the month                        | 1=First week,2=Second week, 3= Third week, 4= Fourth week                                                                    |
| `dt_month_of_qt`     | INT       | -           |                                                 |                                                                                                                              |
| `dt_month_of_year`   | INT       | -           | Specfic month number of the year.               | 1=January,2=February, 3=March, 4=April, 5=May, 6=June, 7= July, 8=August, 9=September, 10= October, 11=November, 12=December |
| `dt_month_year`      | DATE      | -           |                                                 |                                                                                                                              |

## 2. Relationships & Join Logic

- **Primary Join**: `FactSales.Date = date.dt_date` (Ensure Fact table has a date column)
- **Secondary Usage**: Often used to filter other tables by joining on date ranges.

## 3. Entity Synonyms (Vocabulary)

_Use these to map user terms to database values._

- "This Year" -> `dt_year = YEAR(CURDATE())`
- "Last Month" -> `dt_month_of_year = MONTH(CURDATE()) - 1`
- "Q1", "First Quarter" -> `dt_quarter_of_year = 1`
- "Weekend" -> `dt_day_name IN ('Saturday', 'Sunday')`

## 4. Business Logic & Filtering Rules

- **Fiscal vs Calendar**: Assume **Calendar Year** unless Fiscal is explicitly requested (Schema implies Calendar).
- **Date Format**: Always use 'YYYY-MM-DD' for string literals in SQL.

## 5. Common Pitfalls (DO NOT DO)

- Do NOT use string matching for dates (e.g., `LIKE '2024%'`); use `dt_year = 2024`.
- Do NOT assume `dt_week_of_year` aligns perfectly with months (weeks can cross month boundaries).

## 6. Predefined SQL Templates (Strict Usage)

### 6.1 Filter by Month/Year

**Intent**: "Sales in August 2024"

```sql
SELECT dt_date
FROM date
WHERE dt_month_name = 'August' AND dt_year = 2024;
```

_(Note: Usually joined with Fact table)_

### 6.2 Quarterly Aggregation Helper

**Intent**: "Group by Quarter"

```sql
SELECT dt_year, dt_quarter_of_year, COUNT(*) as DaysCount
FROM date
WHERE dt_year = 2024
GROUP BY dt_year, dt_quarter_of_year;
```

### 6.3 Dynamic Relative Dates

**Intent**: "Last 7 days"

```sql
SELECT dt_date
FROM date
WHERE dt_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY);
```
