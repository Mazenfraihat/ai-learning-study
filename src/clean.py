"""
Cleaning pipeline for the AI-Assisted Learning survey.
Usage: python src/clean.py data/responses.csv
Outputs: data/clean.csv + printed summary (drops, correlations with GPA).
"""
import sys
import pandas as pd

# --- 1. Load -------------------------------------------------------------
raw = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "data/responses.csv")
raw.columns = [c.strip() for c in raw.columns]
print(f"Loaded {len(raw)} raw responses")

COLUMNS = {
    "GPA (0.0–4.0)": "gpa",
    "Hours studied per week": "study_hours",
    "Study consistency (1–5)": "consistency",
    "What is your primary study method?": "method",
    "How often do you use AI tools (ChatGPT, etc.) for studying?": "ai_freq",
    "How do you primarily use AI? (Select all that apply)": "ai_uses",
    "How confident are you in using AI effectively?": "ai_confidence",
    "How dependent are you on AI for completing assignments?": "ai_dependence",
    "How often do you verify or double-check AI-generated answers?": "ai_verify",
    "What is your major?": "major",
    "What is your current year in school?": "year",
    "To ensure quality responses, please select ‘Often’ for this question": "attention",
    "How difficult are your current courses?": "difficulty",
    "On average, how many hours do you sleep per night? (Number)": "sleep",
    "How easily do you get distracted while studying?": "distraction",
    "How often do you complete assignments without external help (including AI)?": "independence",
}
df = raw.rename(columns=COLUMNS)

# --- 2. Attention check --------------------------------------------------
before = len(df)
df = df[df["attention"].astype(str).str.strip().str.lower() == "often"]
print(f"Attention check: dropped {before - len(df)}")

# --- 3. GPA: coerce to float, keep 0.0-4.0 --------------------------------
df["gpa"] = pd.to_numeric(df["gpa"], errors="coerce")
before = len(df)
df = df[df["gpa"].between(0.0, 4.0)]
print(f"GPA validity: dropped {before - len(df)}")

# --- 4. Range answers -> numeric midpoints --------------------------------
HOURS = {"0-5 Hours": 2.5, "5–10 Hours": 7.5, "10–20 Hours": 15,
         "20–30 Hours": 25, "30+ Hours": 35}
SLEEP = {"<5": 4.5, "5–6": 5.5, "6–7": 6.5, "7–8": 7.5, "8+": 8.5}
df["study_hours_n"] = df["study_hours"].map(HOURS)
df["sleep_n"] = df["sleep"].map(SLEEP)

# --- 5. Numeric coercion for scale questions -------------------------------
for col in ["consistency", "ai_freq", "ai_confidence", "ai_dependence",
            "ai_verify", "difficulty", "distraction", "independence"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# --- 6. Multi-select "How do you use AI" -> one-hot ------------------------
uses = df["ai_uses"].fillna("").str.get_dummies(sep=", ")
uses.columns = ["use_" + c.strip().lower().replace(" ", "_").replace("/", "")[:25]
                for c in uses.columns]
df = pd.concat([df, uses], axis=1)

# --- 7. Save + summary ------------------------------------------------------
df = df.drop(columns=["attention", "Timestamp"], errors="ignore")
df.to_csv("data/clean.csv", index=False)
print(f"\nSaved {len(df)} clean responses -> data/clean.csv")

numeric = df.select_dtypes("number")
print("\n=== Correlations with GPA ===")
print(numeric.corr()["gpa"].drop("gpa")
      .sort_values(key=abs, ascending=False).round(3).to_string())

print("\n=== Mean GPA by AI-verification level ===")
print(df.groupby("ai_verify")["gpa"].agg(["mean", "count"]).round(2))
