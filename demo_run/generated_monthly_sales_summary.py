from collections import defaultdict
import csv
import sys


REQUIRED_COLUMNS = {"month", "revenue"}
REPAIR_NOTE = 'Contract repair applied for: C2, C4, C5, C6.'


def main(argv):
    if len(argv) != 2:
        print("Usage: python generated_monthly_sales_summary.py <input.csv>", file=sys.stderr)
        return 2

    totals = defaultdict(float)
    try:
        with open(argv[1], newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fieldnames = set(reader.fieldnames or [])
            missing = sorted(REQUIRED_COLUMNS - fieldnames)
            if missing:
                print(f"ERROR: Missing required columns: {', '.join(missing)}", file=sys.stderr)
                return 3

            for row_number, row in enumerate(reader, start=2):
                month = (row.get("month") or "").strip()
                raw_revenue = (row.get("revenue") or "").strip()
                if not month:
                    print(f"ERROR: Missing month at row {row_number}", file=sys.stderr)
                    return 4
                try:
                    revenue = float(raw_revenue)
                except ValueError:
                    print(
                        f"ERROR: Invalid revenue at row {row_number}: {raw_revenue!r}",
                        file=sys.stderr,
                    )
                    return 5
                totals[month] += revenue
    except FileNotFoundError:
        print(f"ERROR: File not found: {argv[1]}", file=sys.stderr)
        return 6

    print("month,total_revenue")
    for month in sorted(totals):
        print(f"{month},{totals[month]:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
