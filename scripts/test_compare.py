import sys
import os

# Ensure project root is on sys.path when running from `scripts/`
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from comparison_engine import compare_cv_data, generate_report

# Minimal synthetic structured data matching project keys
cv_a = {
    "DENEYİM": [{"Raw_Entry": "Senior Backend Developer at Acme (2019-2024)"}],
    "EĞİTİM": [{"Raw_Entry": "BSc Computer Science, University X (2014-2018)"}],
    "YETENEKLER": ["python", "django", "sql"],
    "ÖZET": "Experienced backend developer with strong Python and system design skills."
}

cv_b = {
    "DENEYİM": [{"Raw_Entry": "Backend Engineer at Beta (2020-2024)"}],
    "EĞİTİM": [{"Raw_Entry": "BSc Computer Science, University Y (2013-2017)"}],
    "YETENEKLER": ["python", "flask", "nosql"],
    "ÖZET": "Backend engineer focusing on scalable Python services and APIs."
}

if __name__ == "__main__":
    total_score, section_scores = compare_cv_data(cv_a, cv_b)
    report = generate_report(cv_a, cv_b, total_score, section_scores)

    print(f"Total score: {total_score} (x100 = {total_score*100:.1f}%)")
    print("Section scores:")
    for k, v in section_scores.items():
        print(f"  {k}: {v}")

    print("\nReport:")
    for line in report:
        print(line)
