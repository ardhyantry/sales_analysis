from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def find_column(dataframe: pd.DataFrame, column_name: str) -> str | None:
    """Return a column name when it exists, otherwise None."""
    return column_name if column_name in dataframe.columns else None


def main() -> None:
    input_path = Path("data/raw/superstore.xls")
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("[1/8] Loading data...")
    df = pd.read_excel(input_path, engine="calamine")
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    required = ["sales", "profit", "quantity"]
    missing_required = [column for column in required if column not in df.columns]
    if missing_required:
        raise ValueError(
            "This does not appear to be a compatible Superstore dataset. "
            f"Missing required columns: {missing_required}. "
            f"Available columns: {df.columns.tolist()}"
        )

    print("Columns:", ", ".join(df.columns))

    # 3. Initial data-quality report
    print("\n[3/8] Checking data quality...")
    initial_rows = len(df)
    missing_before = df.isna().sum()
    duplicate_count = int(df.duplicated().sum())

    quality_report = pd.DataFrame({
        "missing_values": missing_before,
        "missing_percentage": (missing_before / max(len(df), 1) * 100).round(2),
    })
    quality_report.to_csv(output_dir / "data_quality_before_cleaning.csv")

    print(f"Exact duplicate rows found: {duplicate_count:,}")
    print("Missing values by column:")
    print(quality_report.to_string())

    # 4. Cleaning
    print("\n[4/8] Cleaning data...")
    df = df.drop_duplicates().copy()

    for date_column in ["order_date", "ship_date"]:
        if date_column in df.columns:
            df[date_column] = pd.to_datetime(df[date_column], errors="coerce")

    for numeric_column in ["sales", "profit", "quantity", "discount"]:
        if numeric_column in df.columns:
            df[numeric_column] = pd.to_numeric(
                df[numeric_column], errors="coerce"
            )

    # Do not remove negative profit: it represents a loss.
    # Do not automatically remove missing postal codes.
    if "order_date" in df.columns:
        invalid_dates = int(df["order_date"].isna().sum())
        if invalid_dates:
            print(f"Rows with invalid/missing order_date: {invalid_dates:,}")

    # Create useful analytical features.
    if "order_date" in df.columns:
        df["order_year"] = df["order_date"].dt.year
        df["order_month"] = df["order_date"].dt.month
        df["month_name"] = df["order_date"].dt.month_name()
        df["order_period"] = df["order_date"].dt.to_period("M").astype("string")

    if "ship_date" in df.columns and "order_date" in df.columns:
        df["shipping_days"] = (
            df["ship_date"] - df["order_date"]
        ).dt.days

    df["profit_margin_pct"] = np.where(
        df["sales"].notna() & (df["sales"] != 0),
        (df["profit"] / df["sales"]) * 100,
        np.nan,
    )

    cleaned_path = output_dir / "cleaned_sales.csv"
    df.to_csv(cleaned_path, index=False)
    print(f"Cleaned dataset saved to: {cleaned_path}")

    # 5. KPI summary
    print("\n[5/8] Calculating key performance indicators...")
    order_col = find_column(df, "order_id")
    customer_col = find_column(df, "customer_id")
    quantity_col = find_column(df, "quantity")

    total_revenue = df["sales"].sum()
    total_profit = df["profit"].sum()
    total_orders = df[order_col].nunique() if order_col else np.nan
    total_customers = df[customer_col].nunique() if customer_col else np.nan
    total_quantity = df[quantity_col].sum() if quantity_col else np.nan
    average_order_value = (
        total_revenue / total_orders
        if pd.notna(total_orders) and total_orders != 0
        else np.nan
    )
    overall_margin = (
        total_profit / total_revenue * 100
        if total_revenue != 0
        else np.nan
    )

    kpis = pd.DataFrame({
        "metric": [
            "Total Revenue",
            "Total Profit",
            "Total Orders",
            "Total Customers",
            "Total Quantity Sold",
            "Average Order Value",
            "Overall Profit Margin (%)",
        ],
        "value": [
            total_revenue,
            total_profit,
            total_orders,
            total_customers,
            total_quantity,
            average_order_value,
            overall_margin,
        ],
    })
    kpis.to_csv(output_dir / "kpi_summary.csv", index=False)

    print("\nKEY PERFORMANCE INDICATORS")
    print("-" * 45)
    print(f"Total Revenue:          ${total_revenue:,.2f}")
    print(f"Total Profit:           ${total_profit:,.2f}")
    print(f"Total Orders:           {total_orders:,.0f}" if pd.notna(total_orders) else "Total Orders: N/A")
    print(f"Total Customers:        {total_customers:,.0f}" if pd.notna(total_customers) else "Total Customers: N/A")
    print(f"Total Quantity Sold:    {total_quantity:,.0f}" if pd.notna(total_quantity) else "Total Quantity Sold: N/A")
    print(f"Average Order Value:    ${average_order_value:,.2f}" if pd.notna(average_order_value) else "Average Order Value: N/A")
    print(f"Overall Profit Margin:  {overall_margin:.2f}%" if pd.notna(overall_margin) else "Overall Profit Margin: N/A")

    # 6. Business summaries
    print("\n[6/8] Creating business analysis summaries...")

    category_col = find_column(df, "category")
    subcategory_col = find_column(df, "sub_category")
    region_col = find_column(df, "region")
    segment_col = find_column(df, "segment")
    product_col = find_column(df, "product_name")
    name_col = find_column(df, "customer_name")

    if category_col:
        category_summary = (
            df.groupby(category_col, dropna=False)
            .agg(
                total_sales=("sales", "sum"),
                total_profit=("profit", "sum"),
                total_quantity=(quantity_col, "sum") if quantity_col else ("sales", "size"),
            )
            .sort_values("total_sales", ascending=False)
            .reset_index()
        )
        category_summary.to_csv(output_dir / "category_performance.csv", index=False)

    if subcategory_col:
        subcategory_summary = (
            df.groupby(subcategory_col, dropna=False)
            .agg(total_sales=("sales", "sum"), total_profit=("profit", "sum"))
            .sort_values("total_profit", ascending=True)
            .reset_index()
        )
        subcategory_summary.to_csv(output_dir / "subcategory_performance.csv", index=False)

    if region_col:
        region_summary = (
            df.groupby(region_col, dropna=False)
            .agg(total_sales=("sales", "sum"), total_profit=("profit", "sum"))
            .sort_values("total_sales", ascending=False)
            .reset_index()
        )
        region_summary.to_csv(output_dir / "regional_performance.csv", index=False)

    if segment_col:
        segment_summary = (
            df.groupby(segment_col, dropna=False)
            .agg(total_sales=("sales", "sum"), total_profit=("profit", "sum"))
            .sort_values("total_sales", ascending=False)
            .reset_index()
        )
        segment_summary.to_csv(output_dir / "customer_segment_performance.csv", index=False)

    if name_col:
        customer_summary = (
            df.groupby(name_col, dropna=False)
            .agg(total_sales=("sales", "sum"), total_profit=("profit", "sum"))
            .sort_values("total_sales", ascending=False)
            .head(10)
            .reset_index()
        )
        customer_summary.to_csv(output_dir / "top_10_customers.csv", index=False)

    # 7. Visualizations
    print("\n[7/8] Generating charts...")

    if "order_period" in df.columns:
        monthly = (
            df.dropna(subset=["order_date"])
            .groupby("order_period", as_index=False)["sales"]
            .sum()
        )
        monthly["order_period"] = monthly["order_period"].astype(str)
        plt.figure(figsize=(12, 6))
        sns.lineplot(data=monthly, x="order_period", y="sales", marker="o")
        plt.xticks(rotation=45, ha="right")
        plt.title("Monthly Sales")
        plt.tight_layout()
        plt.savefig(output_dir / "monthly_sales.png", dpi=150)
        plt.close()

    if category_col:
        category_chart = (
            df.groupby(category_col, as_index=False)["sales"]
            .sum()
            .sort_values("sales", ascending=False)
        )
        plt.figure(figsize=(8, 5))
        sns.barplot(data=category_chart, x=category_col, y="sales")
        plt.title("Sales by Category")
        plt.tight_layout()
        plt.savefig(output_dir / "sales_by_category.png", dpi=150)
        plt.close()

    print(f"\n[8/8] Analysis complete. Results saved to: {output_dir}")


if __name__ == "__main__":
    main()