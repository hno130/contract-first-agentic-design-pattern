# Generated Contract

- Pattern version: 1.0.0
- Max iterations: 2

## Goal

Build a CLI script that reads a CSV file and prints monthly revenue totals.

## Scope

- Accept one CSV file path from the command line.
- Validate the required month and revenue columns.
- Print monthly revenue totals sorted by month.
- Fail loudly for invalid inputs instead of emitting partial results.

## Out Of Scope

- Inferring non-normalized date formats.
- Currency conversion.
- Graphical user interface.
- Writing output files.

## Assumptions

- The CSV input uses UTF-8 encoding.
- The required columns are month and revenue.
- The month value is already normalized, for example 2026-01.
- The revenue value must be numeric.
- Original request: CSV 파일을 읽어서 월별 매출 요약을 만드는 Python 스크립트를 만들어줘.

## Acceptance Criteria

- **C1** [must/interface] The script accepts the input CSV path as a command-line argument.
  - Verification: Running the script without an argument must fail with a usage message.
  - Evidence: process exit code and stderr
- **C2** [must/input-validation] The script validates that month and revenue columns exist.
  - Verification: A CSV missing revenue must fail with a clear missing-column error.
  - Evidence: process exit code and stderr
- **C3** [must/correctness] The script prints sorted monthly totals in CSV format.
  - Verification: A sample CSV must produce the expected month,total_revenue output.
  - Evidence: stdout exact match
- **C4** [must/input-validation] The script rejects non-numeric revenue values.
  - Verification: A CSV containing a non-numeric revenue value must fail with a clear error.
  - Evidence: process exit code and stderr
- **C5** [must/input-validation] The script rejects rows with an empty month value.
  - Verification: A CSV containing an empty month must fail with a clear row-level error.
  - Evidence: process exit code and stderr
- **C6** [must/resilience] The script handles a missing input file without a Python traceback.
  - Verification: A non-existent file path must fail with a clear file-not-found error.
  - Evidence: process exit code and stderr

## Policies

- Failure policy: All must criteria must pass before the task is considered complete.
- Repair policy: Repair only the criteria that failed in the latest verification run.
