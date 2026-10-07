"""Clean the fictional raw survey and log every change made."""
import json
from pathlib import Path
import numpy as np
import pandas as pd

base = Path(__file__).resolve().parent.parent
raw = pd.read_csv(base / "data" / "survey_raw_fictional.csv", dtype=str, keep_default_na=False)
log = {"rows_in": len(raw)}
df = raw.copy()

# 1. Remove exact duplicate records
before = len(df)
df = df.drop_duplicates(subset="respondent_id", keep="first")
log["duplicates_removed"] = before - len(df)

# 2. Standardise text (trim whitespace, consistent case)
df["district"] = df["district"].str.strip().str.title()

gender_map = {"female": "Female", "f": "Female", "male": "Male", "m": "Male"}
g = df["gender"].str.strip().str.lower().map(gender_map)
log["gender_missing"] = int(g.isna().sum())
df["gender"] = g

yn_map = {"yes": "Yes", "y": "Yes", "no": "No", "n": "No"}
a = df["attends_school"].str.strip().str.lower().map(yn_map)
log["attends_school_missing"] = int(a.isna().sum())
df["attends_school"] = a

# 3. Dates: three mixed formats -> ISO
def parse_date(s):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%b-%Y"):
        try:
            return pd.to_datetime(s, format=fmt)
        except ValueError:
            continue
    return pd.NaT
df["survey_date"] = df["survey_date"].map(parse_date)
log["dates_unparsed"] = int(df["survey_date"].isna().sum())

# 4. Age: numeric only, plausible range for this programme (10-19), else missing
age = pd.to_numeric(df["age"].str.extract(r"(\d+)")[0], errors="coerce")
bad_age = age.notna() & ~age.between(10, 19)
non_numeric = df["age"].str.strip().ne("") & pd.to_numeric(df["age"], errors="coerce").isna()
log["age_out_of_range_set_missing"] = int(bad_age.sum())
log["age_text_values_repaired_or_missing"] = int(non_numeric.sum())
age[bad_age] = np.nan
df["age"] = age.astype("Int64")

# 5. Test score: numeric, valid range 0-100, else missing
score = pd.to_numeric(df["test_score"], errors="coerce")
bad_score = score.notna() & ~score.between(0, 100)
log["score_non_numeric_set_missing"] = int(score.isna().sum() - (df["test_score"].str.strip() == "").sum())
log["score_out_of_range_set_missing"] = int(bad_score.sum())
score[bad_score] = np.nan
df["test_score"] = score

df = df.sort_values("respondent_id").reset_index(drop=True)
log["rows_out"] = len(df)
log["missing_after_cleaning"] = {c: int(df[c].isna().sum()) for c in df.columns}

df.to_csv(base / "data" / "survey_clean.csv", index=False, date_format="%Y-%m-%d")
(base / "data" / "cleaning_log.json").write_text(json.dumps(log, indent=2))
print(json.dumps(log, indent=2))
