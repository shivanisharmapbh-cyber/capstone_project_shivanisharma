# capstone_project_shivanisharma

# Mamaearth Sales and Returns Analysis

This project uses SQL, pandas, Matplotlib, and Gemini to analyze sales,
identify return-risk segments, and generate a business narrative.

## Prerequisites

- MySQL Server and MySQL Workbench
- Python 3 with pip
- The complete repository downloaded to my computer

Open a terminal in the repository's main folder—the folder containing
`sql`, `data`, `analysis`, and `narrator`.

Install the analysis dependencies:

```bash
python -m pip install pandas matplotlib
```

For optional Gemini API generation, also install:

```bash
python -m pip install google-genai
```

The offline narrator does not require the Gemini library.

## 1. Load the SQL Data and Run Reports

connect to MYSQL using MYSQL Workbench.

Create and select the project database:

```sql
CREATE DATABASE IF NOT EXISTS mamaearth_db;
USE mamaearth_db;
```

Open and execute these files in order, using `mamaearth_db` as the
selected database:

1. `sql/schema.sql` — create the three tables.
2. `sql/seed_data.sql` — load the original records.
3. `sql/reports.sql` — run the required reports.

Verify the loaded record counts:

```sql
SELECT COUNT(*) FROM customers; -- 45
SELECT COUNT(*) FROM products;  -- 16
SELECT COUNT(*) FROM orders;    -- 180
```

The raw order report should show:

- Total orders: 180
- Total revenue: INR 99,860.20
- Average order value: INR 554.78

The rating-count report should show 180 orders, with 165 ratings,
and 15 missing ratings. the results are written as comments above each
query in sql/reports.sql.

for the first setup, run schema.sql in a new database.
if the loyalty_tier column is already added, do not
run the alter table statement again.

## 2. Run the Python Analysis and Visualizations

The Python analysis reads the original CSV files directly:

- `data/orders.csv`
- `data/customers.csv`
- `data/products.csv`

It does not require a SQL connection. Keep the CSV headers and preserve
the original source values.

Run:

```bash
python analysis/clean_and_eda.py
python analysis/visualize.py
```

The analysis prints the intermediate results required for verification,
including:

- Original orders shape: (180, 9)
- Standardized payment counts: CARD 70, UPI 55, COD 55
- Duplicate orders removed: O0176–O0180
- Deduplicated orders shape: (175, 9)
- Missing discounts filled: 12
- Missing ratings filled: 15, using a median of 3.0
- Cleaned revenue: INR 97,358.30
- Duplicate revenue reconciliation difference: INR 2,501.90
- Quantity outliers: O0011 and O0098, retained and flagged
- Return rates: COD 44.4%, CARD 14.7%, UPI 18.9%
- Highest-risk segment: COD in Tier-2 cities, at 54.5%
- Six pairwise correlations classified as negligible
- Corrected peak month: March 2026, at INR 20,318.90

Part 2 Task 5 checks the revenue totals. the analysis/
clean_and_eda.py script automatically saves these results,
along with segment and monthly revenue findings, in narrator/
findings.json.

The visualization script regenerates:

- `visualizations/return_rate_by_payment.png`
- `visualizations/monthly_revenue_trend.png`

The monthly chart excludes the two flagged quantity outliers.
Running both scripts again with unchanged CSVs reproduces the same
analysis results and charts.

## 3. Turn findings into a business story

The narrator reads `narrator/findings.json` and tell the story in three parts:
Situation, Complication, and Resolution.

### Offline Mode

No API key, network access, or API spend is required.

Ensure neither `GEMINI_API_KEY` nor `GOOGLE_API_KEY` is set.

In Windows PowerShell:

```powershell
Remove-Item Env:GEMINI_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:GOOGLE_API_KEY -ErrorAction SilentlyContinue
```

In macOS or Linux:

```bash
unset GEMINI_API_KEY GOOGLE_API_KEY
```

Run:

```bash
python narrator/generate_narrative.py
```

The output identifies the source as `offline`, reports zero API tokens,
and saves `narrator/sample_output_offline.txt`.

### Gemini Mode

Google AI Studio provides a free Gemini API key with a free usage tier
for supported models. Use a Free Tier project rather than enabling
paid billing for this project. The offline fallback keeps the pipeline
gradable with zero API spend or network access.

Create a key at https://aistudio.google.com/apikey.

Set it as an environment variable for the current terminal session.

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY = "YOUR_API_KEY"
```

macOS or Linux:

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

Replace the placeholder locally. Never commit an actual key to GitHub.

Run:

```bash
python narrator/generate_narrative.py
```

The default model is `gemini-3.5-flash-lite`. The request uses a separate
system instruction, temperature 0.0, a maximum of 2,048 output tokens,
and a 60-second timeout.

A successful Gemini run saves its actual narrative to
`narrator/sample_output.txt`. If the API request fails, the script
reports the reason and generates the offline narrative instead.

Temperature 0.0 reduces randomness but does not guarantee identical
Gemini wording across requests. The saved online sample is included
for grading without a live API request.

## 4. Verify the Saved Narrative

The narrator prints a PASS or FAIL result for each required check:

- Cleaned revenue: INR 97,358.30
- COD return rate: 44.4%
- Highest-risk segment return rate: 54.5%
- Duplicate reconciliation difference: INR 2,501.90
- March peak revenue: INR 20,318.90

To validate the submitted Gemini sample without calling the API, run:

```bash
python -c "import json; from pathlib import Path; from narrator.generate_narrative import check_numeric_accuracy; p = Path('narrator'); f = json.loads((p / 'findings.json').read_text(encoding='utf-8')); check_numeric_accuracy((p / 'sample_output.txt').read_text(encoding='utf-8'), f)"
```

All five checks should print PASS. These checks verify the required
numeric values; business interpretations still require review.
