# Task 11 — Visualize return rates and monthly revenue.
# Both charts are regenerated from the original CSV datasets.

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, StrMethodFormatter

# Locate the source data and chart output folders.
project_dir = Path(__file__).resolve().parent.parent
data_dir = project_dir / "data"
output_dir = project_dir / "visualizations"
output_dir.mkdir(parents=True, exist_ok=True)

# Load the raw datasets.
orders = pd.read_csv(data_dir / "orders.csv")
products = pd.read_csv(data_dir / "products.csv")
customers = pd.read_csv(data_dir / "customers.csv")

# Standardize payment methods.
orders["payment_method"] = (
    orders["payment_method"].str.strip().str.upper()
)

# Remove duplicate transactions while retaining the first occurrence.
natural_key = [
    "customer_id",
    "product_id",
    "order_date",
    "quantity",
    "discount_pct",
    "payment_method",
    "rating",
    "returned",
]

duplicate_mask = orders.duplicated(
    subset=natural_key, keep="first"
)
orders_clean = orders.loc[~duplicate_mask].copy()

# Fill missing discounts and ratings.
orders_clean["discount_pct"] = (
    orders_clean["discount_pct"].fillna(0)
)
orders_clean["rating"] = (
    orders_clean["rating"].fillna(orders_clean["rating"].median())
)

# Merge product and customer details with cleaned orders.
merged = (
    orders_clean
    .merge(products, on="product_id", how="left", validate="many_to_one")
    .merge(customers, on="customer_id", how="left", validate="many_to_one")
)

assert merged["price"].notna().all(), "Some products did not match."
assert merged["name"].notna().all(), "Some customers did not match."

merged["order_value"] = (
    merged["quantity"]
    * merged["price"]
    * (1 - merged["discount_pct"] / 100)
)

# Flag quantity outliers without removing them from the dataset.
q1 = merged["quantity"].quantile(0.25)
q3 = merged["quantity"].quantile(0.75)
iqr = q3 - q1

lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr

merged["is_outlier"] = (
    (merged["quantity"] < lower)
    | (merged["quantity"] > upper)
)

# Chart 1 — Compare return rates across payment methods.
return_rates = (
    merged.groupby("payment_method")["returned"]
    .mean()
    .mul(100)
    .sort_values(ascending=False)
)

#print("Return rates by payment method:")
#print(return_rates.to_string(float_format=lambda x: f"{x:.1f}%"))

fig, ax = plt.subplots(figsize=(8, 5))

bars = ax.bar(
    return_rates.index,
    return_rates.values,
    color=["#C44E52", "#4C72B0", "#55A868"],
    width=0.6,
)

ax.bar_label(
    bars,
    labels=[f"{value:.1f}%" for value in return_rates],
    padding=5,
)

cod_rate = return_rates.loc["COD"]
card_rate = return_rates.loc["CARD"]

ax.set_title(
    f"COD Returns at {cod_rate:.1f}% — "
    f"About {cod_rate / card_rate:.1f}x Card"
)
ax.set_xlabel("Payment method")
ax.set_ylabel("Return rate (%)")
ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))
ax.set_ylim(0, return_rates.max() * 1.2)
ax.grid(axis="y", alpha=0.25)
ax.set_axisbelow(True)

fig.tight_layout()
bar_path = output_dir / "return_rate_by_payment.png"
fig.savefig(bar_path, dpi=200, bbox_inches="tight")
plt.close(fig)

#print(f"Saved: {bar_path}")

# Chart 2 — Show monthly revenue excluding quantity outliers.
merged["order_date"] = pd.to_datetime(merged["order_date"])
merged["year_month"] = merged["order_date"].dt.to_period("M")

monthly_revenue = (
    merged.loc[~merged["is_outlier"]]
    .groupby("year_month")["order_value"]
    .sum()
    .sort_index()
)

#print("\nOutlier-corrected monthly revenue (INR):")
#print(monthly_revenue.to_string(float_format="{:.2f}".format))

peak_month = monthly_revenue.idxmax()
peak_label = peak_month.to_timestamp().strftime("%B %Y")
month_labels = [
    month.to_timestamp().strftime("%b %Y")
    for month in monthly_revenue.index
]

fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(
    month_labels,
    monthly_revenue.values,
    marker="o",
    linewidth=2,
    color="#4C72B0",
)

for month, revenue in zip(month_labels, monthly_revenue.values):
    ax.annotate(
        f"{revenue:,.2f}",
        (month, revenue),
        textcoords="offset points",
        xytext=(0, 10),
        ha="center",
        fontsize=9,
    )

ax.set_title(
    f"{peak_label} Leads Monthly Revenue "
    "After Excluding Quantity Outliers"
)
ax.set_xlabel("Order month")
ax.set_ylabel("Revenue (INR)")
ax.yaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
ax.set_ylim(0, monthly_revenue.max() * 1.2)
ax.grid(alpha=0.25)
ax.set_axisbelow(True)

fig.tight_layout()
line_path = output_dir / "monthly_revenue_trend.png"
fig.savefig(line_path, dpi=200, bbox_inches="tight")
plt.close(fig)

#print(f"Saved: {line_path}")
