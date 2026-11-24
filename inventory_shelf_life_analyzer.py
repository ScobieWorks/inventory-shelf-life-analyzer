import argparse
import csv
import json
import sys
from datetime import datetime, date
from pathlib import Path
from textwrap import dedent

# ---------- date parsing ----------
DATE_PATTERNS = ["%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y"]

def parse_date(value: str) -> date:
    for fmt in DATE_PATTERNS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unparseable date: {value}")

# ---------- bucket logic ----------
class Bucket:
    EXPIRED = "Expired"
    LESS_30 = "<30 days"
    BETWEEN_30_90 = "30-90 days"
    MORE_90 = ">90 days"


def bucket_and_days_left(expiry: date, reference: date):
    days_left = (expiry - reference).days
    if days_left < 0:
        bucket = Bucket.EXPIRED
    elif days_left < 30:
        bucket = Bucket.LESS_30
    elif days_left <= 90:
        bucket = Bucket.BETWEEN_30_90
    else:
        bucket = Bucket.MORE_90
    return bucket, days_left

# ---------- aggregation ----------

def aggregate(items):
    buckets = {
        Bucket.EXPIRED: [],
        Bucket.LESS_30: [],
        Bucket.BETWEEN_30_90: [],
        Bucket.MORE_90: [],
    }
    for it in items:
        buckets[it["bucket"]].append(it)
    total = len(items)
    report = []
    for name, lst in buckets.items():
        count = len(lst)
        if count:
            avg = sum(i["days_left"] for i in lst) / count
        else:
            avg = 0.0
        percent = (count / total * 100) if total else 0.0
        report.append({
            "name": name,
            "count": count,
            "avg_days_left": round(avg, 1),
            "percent_of_total": round(percent, 1),
            "items": [i["row"] for i in lst],
        })
    return report

# ---------- report writing ----------

def write_report(result_path: str, report):
    with open(result_path, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)

# ---------- table printing ----------

def print_table(report):
    header = f"{'Bucket':<12} {'Count':>5} {'Avg Days Left':>15} {'% of Total':>12}"
    lines = [header, "-" * len(header)]
    for r in report:
        lines.append(f"{r['name']:<12} {r['count']:>5} {r['avg_days_left']:>15.1f} {r['percent_of_total']:>12.1f}")
    sys.stdout.write("\n".join(lines) + "\n")

# ---------- CLI ----------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Inventory shelf‑life analyzer")
    parser.add_argument("csv_path", help="Path to CSV file or - for stdin")
    parser.add_argument("--date-column", default="expiry", help="Column name containing expiry dates")
    parser.add_argument("--today", help="Reference date YYYY-MM-DD (defaults to today)")
    parser.add_argument("--output", help="Write JSON report to this path")
    parser.add_argument("--no-table", action="store_true", help="Suppress console table")
    args = parser.parse_args(argv)

    reference = datetime.strptime(args.today, "%Y-%m-%d").date() if args.today else date.today()

    if args.csv_path == "-":
        reader = csv.DictReader(sys.stdin)
    else:
        path = Path(args.csv_path)
        if not path.is_file():
            sys.stderr.write(f"File not found: {args.csv_path}\n")
            sys.exit(1)
        reader = csv.DictReader(path.open(encoding="utf-8"))

    if args.date_column not in reader.fieldnames:
        sys.stderr.write(f"Missing date column: {args.date_column}\n")
        sys.exit(1)

    items = []
    for row in reader:
        try:
            expiry = parse_date(row[args.date_column])
        except ValueError as e:
            sys.stderr.write(f"{e}\n")
            sys.exit(1)
        bucket, days_left = bucket_and_days_left(expiry, reference)
        items.append({"row": row, "bucket": bucket, "days_left": days_left})

    report = aggregate(items)

    if not args.no_table:
        print_table(report)

    if args.output:
        write_report(args.output, report)

    sys.exit(0)

if __name__ == "__main__":
    main()
