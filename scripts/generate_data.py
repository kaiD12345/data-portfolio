"""Generate FICTIONAL datasets for portfolio samples. No real data is used."""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
out = Path(__file__).resolve().parent.parent / "data"
out.mkdir(exist_ok=True)

# ---------------- 1. Fictional retail sales (for the dashboard + report) ----------------
branches = ["Kigali Central", "Nyamirambo", "Remera", "Huye", "Musanze"]
categories = {"Groceries": (1500, 0.45), "Beverages": (900, 0.30),
              "Household": (2500, 0.15), "Personal care": (1800, 0.10)}
branch_weight = {"Kigali Central": 1.5, "Nyamirambo": 1.1, "Remera": 1.2, "Huye": 0.8, "Musanze": 0.7}

rows = []
for month in pd.period_range("2025-01", "2025-12", freq="M"):
    seasonal = 1 + 0.15 * np.sin((month.month - 3) / 12 * 2 * np.pi) + (0.2 if month.month == 12 else 0)
    for b in branches:
        for cat, (price, share) in categories.items():
            units = rng.poisson(600 * branch_weight[b] * share * seasonal)
            unit_price = price * rng.normal(1.0, 0.03)
            revenue = units * unit_price
            cost = revenue * rng.normal(0.72, 0.03)
            rows.append([str(month), b, cat, units, round(revenue), round(cost)])

sales = pd.DataFrame(rows, columns=["month", "branch", "category", "units_sold", "revenue_rwf", "cost_rwf"])
sales.to_csv(out / "sales_fictional.csv", index=False)

# ---------------- 2. Fictional messy survey (for the cleaning sample) ----------------
n = 300
districts = ["Gasabo", "Kicukiro", "Nyarugenge", "Huye", "Musanze", "Rubavu"]
dirty_district = {
    "Gasabo": ["Gasabo", "gasabo", "GASABO ", " Gasabo"],
    "Kicukiro": ["Kicukiro", "kicukiro", "Kicukiro ", "KICUKIRO"],
    "Nyarugenge": ["Nyarugenge", "nyarugenge", "Nyarugenge ", "NYARUGENGE"],
    "Huye": ["Huye", "huye", " Huye", "HUYE"],
    "Musanze": ["Musanze", "musanze", "Musanze ", "MUSANZE"],
    "Rubavu": ["Rubavu", "rubavu", "Rubavu ", "RUBAVU"],
}
ids = [f"R{i:04d}" for i in range(1, n + 1)]
true_d = rng.choice(districts, n)
gender_opts = ["Female", "female", "F", "Male", "male", "M", "FEMALE", ""]
gender = rng.choice(gender_opts, n, p=[.3, .15, .1, .15, .1, .08, .07, .05])
age = rng.integers(12, 19, n).astype(object)
for idx in rng.choice(n, 6, replace=False):
    age[idx] = rng.choice([0, 150, 999, -1, "15 years", "sixteen"])
for idx in rng.choice(n, 10, replace=False):
    age[idx] = np.nan
dates = pd.to_datetime("2025-03-01") + pd.to_timedelta(rng.integers(0, 60, n), unit="D")
fmts = ["%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y"]
date_str = [d.strftime(fmts[i]) for d, i in zip(dates, rng.integers(0, 3, n))]
attend = rng.choice(["Yes", "yes", "YES", "No", "no", "Y", "N", ""], n, p=[.35, .15, .1, .15, .08, .07, .05, .05])
score = rng.normal(62, 14, n).round(1).astype(object)
for idx in rng.choice(n, 8, replace=False):
    score[idx] = rng.choice(["N/A", "-", "absent", 540, -20])

survey = pd.DataFrame({
    "respondent_id": ids,
    "district": [rng.choice(dirty_district[d]) for d in true_d],
    "gender": gender,
    "age": age,
    "survey_date": date_str,
    "attends_school": attend,
    "test_score": score,
})
dupes = survey.sample(12, random_state=1)
survey = pd.concat([survey, dupes], ignore_index=True).sample(frac=1, random_state=7).reset_index(drop=True)
survey.to_csv(out / "survey_raw_fictional.csv", index=False)
print("sales rows:", len(sales), "| raw survey rows:", len(survey))
