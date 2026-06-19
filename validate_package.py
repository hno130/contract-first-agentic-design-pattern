from __future__ import annotations

from pathlib import Path
import json
import py_compile
import subprocess
import sys
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent
DEMO = ROOT / "contract_first_demo.py"
RUN_DIR = ROOT / "demo_run"
VALIDATION_REPORT = ROOT / "validation_report.json"


REQUIRED_FILES = [
    "README.md",
    "FINAL_BRIEFING.md",
    "PATTERN_SPEC.md",
    "IMPLEMENTATION_GUIDE.md",
    "PROMPT_TEMPLATES.md",
    "IMPROVEMENT_BRIEF.md",
    "contract_schema.json",
    "contract_first_demo.py",
    "validate_package.py",
]


REQUIRED_RUN_FILES = [
    "contract.json",
    "contract.md",
    "generated_monthly_sales_summary.py",
    "verification_trace.json",
    "repair_plan_attempt_1.json",
    "final_report.md",
    "execution_summary.json",
    "manifest.json",
    "cases/valid_sales.csv",
    "cases/missing_column.csv",
    "cases/bad_revenue.csv",
    "cases/missing_month.csv",
    "cases/hidden_order_sales.csv",
]


def main() -> int:
    checks: list[dict[str, object]] = []

    def record(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    for relative in REQUIRED_FILES:
        path = ROOT / relative
        record(f"required file: {relative}", path.is_file(), str(path))

    compile_ok, compile_detail = compile_python([DEMO])
    record("compile package python", compile_ok, compile_detail)

    demo_ok, demo_detail = run_demo()
    record("run demo", demo_ok, demo_detail)

    for relative in REQUIRED_RUN_FILES:
        path = RUN_DIR / relative
        record(f"required demo artifact: {relative}", path.is_file(), str(path))

    contract_ok, contract_detail = validate_contract_shape(RUN_DIR / "contract.json")
    record("validate contract shape", contract_ok, contract_detail)

    trace_ok, trace_detail = validate_trace(RUN_DIR / "verification_trace.json")
    record("validate verification trace", trace_ok, trace_detail)

    summary_ok, summary_detail = validate_summary(RUN_DIR / "execution_summary.json")
    record("validate execution summary", summary_ok, summary_detail)

    generated = RUN_DIR / "generated_monthly_sales_summary.py"
    compile_generated_ok, compile_generated_detail = compile_python([generated])
    record("compile generated script", compile_generated_ok, compile_generated_detail)

    sample_ok, sample_detail = run_generated_sample(generated)
    record("run generated sample", sample_ok, sample_detail)

    report = {
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }
    VALIDATION_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    for check in checks:
        status = "PASS" if check["passed"] else "FAIL"
        print(f"{status} {check['name']}")

    print(f"Validation report: {VALIDATION_REPORT}")
    return 0 if report["passed"] else 1


def compile_python(paths: list[Path]) -> tuple[bool, str]:
    try:
        for path in paths:
            py_compile.compile(str(path), doraise=True)
        return True, "compiled"
    except Exception as exc:  # pragma: no cover - validation utility
        return False, repr(exc)


def run_demo() -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, str(DEMO), "--run-dir", str(RUN_DIR)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    detail = f"exit_code={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    return result.returncode == 0, detail


def validate_contract_shape(path: Path) -> tuple[bool, str]:
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"could not read contract: {exc!r}"

    required = {
        "goal",
        "scope",
        "out_of_scope",
        "assumptions",
        "acceptance_criteria",
        "failure_policy",
        "repair_policy",
        "max_iterations",
    }
    missing = sorted(required - set(contract))
    if missing:
        return False, f"missing fields: {missing}"

    criteria = contract.get("acceptance_criteria", [])
    if len(criteria) < 6:
        return False, f"expected at least 6 criteria, got {len(criteria)}"

    criterion_required = {"id", "priority", "category", "statement", "verification", "evidence"}
    for criterion in criteria:
        missing_criterion_fields = sorted(criterion_required - set(criterion))
        if missing_criterion_fields:
            return False, f"{criterion.get('id', '<unknown>')} missing {missing_criterion_fields}"
        if criterion["priority"] not in {"must", "should", "could"}:
            return False, f"{criterion['id']} has invalid priority {criterion['priority']!r}"

    return True, "contract shape is valid"


def validate_trace(path: Path) -> tuple[bool, str]:
    try:
        trace = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"could not read trace: {exc!r}"

    attempts = trace.get("attempts", [])
    if len(attempts) != 2:
        return False, f"expected 2 attempts, got {len(attempts)}"
    if attempts[0].get("passed") is not False:
        return False, "first attempt should fail to demonstrate repair"
    if attempts[-1].get("passed") is not True:
        return False, "final attempt should pass"

    failed_first = [
        check["criterion_id"]
        for check in attempts[0].get("checks", [])
        if not check.get("passed")
    ]
    expected_failures = {"C2", "C4", "C5", "C6"}
    if not expected_failures.issubset(set(failed_first)):
        return False, f"first attempt failures missing expected set: {failed_first}"

    return True, "trace shows fail -> repair -> pass"


def validate_summary(path: Path) -> tuple[bool, str]:
    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"could not read summary: {exc!r}"

    if summary.get("final_status") != "PASS":
        return False, f"expected PASS, got {summary.get('final_status')!r}"
    if summary.get("attempts") != 2:
        return False, f"expected 2 attempts, got {summary.get('attempts')!r}"
    if summary.get("failed_checks"):
        return False, "expected no failed checks"
    return True, "summary is passing"


def run_generated_sample(generated: Path) -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, str(generated), str(RUN_DIR / "cases" / "valid_sales.csv")],
        capture_output=True,
        text=True,
        timeout=10,
    )
    expected = "month,total_revenue\n2026-01,140.50\n2026-02,20.00\n"
    detail = f"exit_code={result.returncode}\nstdout={result.stdout!r}\nstderr={result.stderr!r}"
    return result.returncode == 0 and result.stdout == expected, detail


if __name__ == "__main__":
    raise SystemExit(main())
