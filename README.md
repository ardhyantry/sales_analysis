# Sales Analysis

## Problem

The project analyzes a Superstore sales dataset to turn raw transaction records
into reliable business metrics. The raw workbook contains order, customer,
product, sales, quantity, discount, and profit data, but it is not immediately
ready for analysis:

- The input file is a binary Excel workbook (`data/raw/superstore.xls`), not a
  CSV file.
- Column names contain spaces and punctuation that make them inconvenient to
  use in code.
- The data needs quality checks and type conversion before aggregation.
- Business users need summaries and charts that make sales and profitability
  easier to understand.

## What We Aim to Achieve

This project aims to:

1. Load the Excel dataset correctly.
2. Validate that the required sales, profit, and quantity fields exist.
3. Check for missing values and duplicate rows.
4. Clean dates and numeric fields without hiding valid negative profits.
5. Calculate key performance indicators (KPIs).
6. Produce summaries by category, sub-category, region, segment, and customer.
7. Generate reusable CSV reports and visualizations.

## How We Do It

The analysis is implemented in [sales_analysis.py](./sales_analysis.py).

1. Read `data/raw/superstore.xls` with pandas using the `calamine` engine.
2. Normalize column names to lowercase `snake_case`.
3. Validate required columns and fail with a clear error if they are missing.
4. Report missing values and exact duplicate rows.
5. Remove duplicate rows, convert dates and numeric fields, and create:
   - order year and month
   - monthly order period
   - shipping days
   - profit margin percentage
6. Calculate revenue, profit, orders, customers, quantity, average order value,
   and overall profit margin.
7. Save business summaries and charts in `outputs/`.

### Run the Analysis

Install the dependencies from [requirements.txt](./requirements.txt), then run:

```bash
/workspaces/sales_analysis/.venv/bin/python sales_analysis.py
```

The script creates the `outputs/` directory automatically.

## Results

The current dataset produced these KPIs:

| Metric | Result |
|---|---:|
| Total revenue | $2,326,534.35 |
| Total profit | $292,296.81 |
| Total orders | 5,111 |
| Total customers | 804 |
| Total quantity sold | 38,654 |
| Average order value | $455.20 |
| Overall profit margin | 12.56% |

Data-quality checks found **0 exact duplicate rows** and no missing values in
the source columns.

Generated reports include:

- [kpi_summary.csv](./outputs/kpi_summary.csv)
- [data_quality_before_cleaning.csv](./outputs/data_quality_before_cleaning.csv)
- [cleaned_sales.csv](./outputs/cleaned_sales.csv)
- [category_performance.csv](./outputs/category_performance.csv)
- [subcategory_performance.csv](./outputs/subcategory_performance.csv)
- [regional_performance.csv](./outputs/regional_performance.csv)
- [customer_segment_performance.csv](./outputs/customer_segment_performance.csv)
- [top_10_customers.csv](./outputs/top_10_customers.csv)
- [monthly_sales.png](./outputs/monthly_sales.png)
- [sales_by_category.png](./outputs/sales_by_category.png)

## Important Fixes

The original script attempted to read the `.xls` workbook with
`pd.read_csv`, which caused a UTF-8 decoding error because the file is a
binary Excel document. The script now uses `pd.read_excel(..., engine="calamine")`
and declares `python-calamine` as a dependency.
