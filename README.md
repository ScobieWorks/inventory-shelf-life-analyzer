# Inventory Shelf‑Life Analyzer

## Overview

`inventory-shelf-life-analyzer` is a lightweight, pure‑Python command‑line tool that helps small retailers, hobby food producers, and home kitchens keep track of perishable inventory.  It reads a CSV file containing an expiry date column, calculates how many days remain until each item expires, buckets items into logical categories, and prints a concise table.  Optionally, it can write a JSON report that includes the raw rows per bucket for further processing.

The tool is intentionally dependency‑free – it uses only the Python standard library – and is designed to run offline on any machine with Python 3.11+.

## Features

* **CSV input** – Accepts a file path or `-` for stdin.
* **Custom date column** – Specify the column that holds expiry dates.
* **Reference date** – Override the current date with `--today` for reproducible reports.
* **Bucketing** – Items are classified into:
  * **Expired** – already past the reference date.
  * **<30 days** – expiring within the next 30 days.
  * **30‑90 days** – expiring between 30 and 90 days.
  * **>90 days** – expiring more than 90 days away.
* **Console table** – Human‑readable summary of counts, average days left, and percentage of total.
* **JSON report** – Optional `--output` flag writes a structured JSON file containing the same summary plus the raw rows per bucket.
* **No external dependencies** – Built entirely with the standard library.

## Installation

The project is a single Python file, so you can copy `inventory_shelf_life_analyzer.py` into your project or run it directly:

```bash
python inventory_shelf_life_analyzer.py path/to/inventory.csv
```

If you prefer a convenient command, you can create a small wrapper script or add the file to your `PATH`.

## Usage

```bash
$ inventory-shelf-life-analyzer inventory.csv \
    --date-column expiry \
    --today 2023-01-01 \
    --output report.json
```

### Positional arguments

* `csv_path` – Path to the CSV file. Use `-` to read from standard input.

### Optional flags

| Flag | Description |
|------|-------------|
| `--date-column <name>` | Column name containing expiry dates (default: `expiry`). |
| `--today <YYYY‑MM‑DD>` | Reference date for calculations (default: today). |
| `--output <path>` | Write a JSON report to the specified file. |
| `--no-table` | Suppress the console table output. |

### Example CSV

```csv
id,expiry,description
1,2023-01-15,Fresh apples
2,2023-02-20,Cheese
3,2022-12-31,Expired yogurt
4,2023-05-10,Milk
```

### Example Output

```
Bucket       Count   Avg Days Left   % of Total
-------------------------------------------
Expired          1            -1.0        25.0
<30 days         1             14.0        25.0
30-90 days       1             49.0        25.0
>90 days         1            119.0        25.0
```

The JSON report (`report.json`) will contain the same data plus the raw rows for each bucket.

## Testing

The test suite uses the standard `unittest` framework and does not require any external packages.  Run the tests with:

```bash
python -m unittest discover -s tests -v
```

The tests cover:

* Date parsing for supported formats.
* Bucket assignment logic.
* CLI table output and JSON report generation.
* Error handling for missing columns and invalid dates.

## License

This project is released under the MIT License.

---

*End of README*

## Installation

```bash
pip install git+https://github.com/ScobieWorks/inventory-shelf-life-analyzer.git
```


## Command-line usage

```bash
inventory-shelf-life-analyzer --help
```

## Limitations
<!-- generated-limitations:fda25afb14a2941f6f3760fc37035d88554e4a45566ffea8b0625fae3aca823f -->
- The text reader in `inventory_shelf_life_analyzer.py` uses UTF-8; supply UTF-8 text for that reading path.
<!-- /generated-limitations -->
