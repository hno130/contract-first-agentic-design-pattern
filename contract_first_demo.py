from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timezone


PATTERN_VERSION = "1.0.0"
DEFAULT_REQUEST = "CSV 파일을 읽어서 월별 매출 요약을 만드는 Python 스크립트를 만들어줘."


@dataclass(frozen=True)
class AcceptanceCriterion:
    id: str
    priority: str
    category: str
    statement: str
    verification: str
    evidence: str


@dataclass(frozen=True)
class Contract:
    goal: str
    scope: list[str]
    out_of_scope: list[str]
    assumptions: list[str]
    acceptance_criteria: list[AcceptanceCriterion]
    failure_policy: str
    repair_policy: str
    max_iterations: int = 2

    def criteria_by_id(self) -> dict[str, AcceptanceCriterion]:
        return {criterion.id: criterion for criterion in self.acceptance_criteria}

    def to_markdown(self) -> str:
        lines = [
            "# Generated Contract",
            "",
            f"- Pattern version: {PATTERN_VERSION}",
            f"- Max iterations: {self.max_iterations}",
            "",
            "## Goal",
            "",
            self.goal,
            "",
            "## Scope",
            "",
        ]
        lines.extend(f"- {item}" for item in self.scope)
        lines.extend(["", "## Out Of Scope", ""])
        lines.extend(f"- {item}" for item in self.out_of_scope)
        lines.extend(["", "## Assumptions", ""])
        lines.extend(f"- {item}" for item in self.assumptions)
        lines.extend(["", "## Acceptance Criteria", ""])
        for criterion in self.acceptance_criteria:
            lines.append(
                f"- **{criterion.id}** [{criterion.priority}/{criterion.category}] "
                f"{criterion.statement}"
            )
            lines.append(f"  - Verification: {criterion.verification}")
            lines.append(f"  - Evidence: {criterion.evidence}")
        lines.extend(
            [
                "",
                "## Policies",
                "",
                f"- Failure policy: {self.failure_policy}",
                f"- Repair policy: {self.repair_policy}",
                "",
            ]
        )
        return "\n".join(lines)


@dataclass(frozen=True)
class CheckResult:
    criterion_id: str
    priority: str
    name: str
    passed: bool
    evidence: str
    detail: str


@dataclass
class AttemptResult:
    attempt: int
    passed: bool
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def failed_checks(self) -> list[CheckResult]:
        return [check for check in self.checks if not check.passed]


@dataclass(frozen=True)
class RepairAction:
    criterion_id: str
    diagnosis: str
    action: str
    reverification: str


@dataclass(frozen=True)
class RepairPlan:
    after_attempt: int
    actions: list[RepairAction]


@dataclass(frozen=True)
class RunArtifacts:
    contract_json: Path
    contract_md: Path
    generated_script: Path
    verification_trace: Path
    final_report: Path
    execution_summary: Path
    manifest: Path
    repair_plan_paths: list[Path]


class ContractGenerator:
    def generate(self, request: str, max_iterations: int = 2) -> Contract:
        return Contract(
            goal="Build a CLI script that reads a CSV file and prints monthly revenue totals.",
            scope=[
                "Accept one CSV file path from the command line.",
                "Validate the required month and revenue columns.",
                "Print monthly revenue totals sorted by month.",
                "Fail loudly for invalid inputs instead of emitting partial results.",
            ],
            out_of_scope=[
                "Inferring non-normalized date formats.",
                "Currency conversion.",
                "Graphical user interface.",
                "Writing output files.",
            ],
            assumptions=[
                "The CSV input uses UTF-8 encoding.",
                "The required columns are month and revenue.",
                "The month value is already normalized, for example 2026-01.",
                "The revenue value must be numeric.",
                f"Original request: {request}",
            ],
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="C1",
                    priority="must",
                    category="interface",
                    statement="The script accepts the input CSV path as a command-line argument.",
                    verification="Running the script without an argument must fail with a usage message.",
                    evidence="process exit code and stderr",
                ),
                AcceptanceCriterion(
                    id="C2",
                    priority="must",
                    category="input-validation",
                    statement="The script validates that month and revenue columns exist.",
                    verification="A CSV missing revenue must fail with a clear missing-column error.",
                    evidence="process exit code and stderr",
                ),
                AcceptanceCriterion(
                    id="C3",
                    priority="must",
                    category="correctness",
                    statement="The script prints sorted monthly totals in CSV format.",
                    verification="A sample CSV must produce the expected month,total_revenue output.",
                    evidence="stdout exact match",
                ),
                AcceptanceCriterion(
                    id="C4",
                    priority="must",
                    category="input-validation",
                    statement="The script rejects non-numeric revenue values.",
                    verification="A CSV containing a non-numeric revenue value must fail with a clear error.",
                    evidence="process exit code and stderr",
                ),
                AcceptanceCriterion(
                    id="C5",
                    priority="must",
                    category="input-validation",
                    statement="The script rejects rows with an empty month value.",
                    verification="A CSV containing an empty month must fail with a clear row-level error.",
                    evidence="process exit code and stderr",
                ),
                AcceptanceCriterion(
                    id="C6",
                    priority="must",
                    category="resilience",
                    statement="The script handles a missing input file without a Python traceback.",
                    verification="A non-existent file path must fail with a clear file-not-found error.",
                    evidence="process exit code and stderr",
                ),
            ],
            failure_policy="All must criteria must pass before the task is considered complete.",
            repair_policy="Repair only the criteria that failed in the latest verification run.",
            max_iterations=max_iterations,
        )


class Executor:
    def render_script(
        self,
        target: Path,
        attempt: int,
        repair_plan: RepairPlan | None = None,
    ) -> None:
        source = self._first_attempt_source() if attempt == 1 else self._repaired_source(repair_plan)
        target.write_text(source, encoding="utf-8")

    def _first_attempt_source(self) -> str:
        return textwrap.dedent(
            """
            from collections import defaultdict
            import csv
            import sys


            def main(argv):
                if len(argv) != 2:
                    print("Usage: python generated_monthly_sales_summary.py <input.csv>", file=sys.stderr)
                    return 2

                totals = defaultdict(float)
                with open(argv[1], newline="", encoding="utf-8") as handle:
                    reader = csv.DictReader(handle)
                    for row in reader:
                        totals[row["month"]] += float(row["revenue"])

                print("month,total_revenue")
                for month in sorted(totals):
                    print(f"{month},{totals[month]:.2f}")
                return 0


            if __name__ == "__main__":
                raise SystemExit(main(sys.argv))
            """
        ).lstrip()

    def _repaired_source(self, repair_plan: RepairPlan | None) -> str:
        repair_note = "Contract repair applied."
        if repair_plan is not None:
            repaired_ids = ", ".join(action.criterion_id for action in repair_plan.actions)
            repair_note = f"Contract repair applied for: {repaired_ids}."

        return textwrap.dedent(
            f'''
            from collections import defaultdict
            import csv
            import sys


            REQUIRED_COLUMNS = {{"month", "revenue"}}
            REPAIR_NOTE = {repair_note!r}


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
                            print(f"ERROR: Missing required columns: {{', '.join(missing)}}", file=sys.stderr)
                            return 3

                        for row_number, row in enumerate(reader, start=2):
                            month = (row.get("month") or "").strip()
                            raw_revenue = (row.get("revenue") or "").strip()
                            if not month:
                                print(f"ERROR: Missing month at row {{row_number}}", file=sys.stderr)
                                return 4
                            try:
                                revenue = float(raw_revenue)
                            except ValueError:
                                print(
                                    f"ERROR: Invalid revenue at row {{row_number}}: {{raw_revenue!r}}",
                                    file=sys.stderr,
                                )
                                return 5
                            totals[month] += revenue
                except FileNotFoundError:
                    print(f"ERROR: File not found: {{argv[1]}}", file=sys.stderr)
                    return 6

                print("month,total_revenue")
                for month in sorted(totals):
                    print(f"{{month}},{{totals[month]:.2f}}")
                return 0


            if __name__ == "__main__":
                raise SystemExit(main(sys.argv))
            '''
        ).lstrip()


class Verifier:
    def __init__(self, workspace: Path, contract: Contract) -> None:
        self.workspace = workspace
        self.criteria = contract.criteria_by_id()
        self.case_dir = workspace / "cases"
        self.case_dir.mkdir(parents=True, exist_ok=True)
        self.valid_csv = self.case_dir / "valid_sales.csv"
        self.missing_column_csv = self.case_dir / "missing_column.csv"
        self.bad_revenue_csv = self.case_dir / "bad_revenue.csv"
        self.missing_month_csv = self.case_dir / "missing_month.csv"
        self.hidden_order_csv = self.case_dir / "hidden_order_sales.csv"
        self.missing_file = self.case_dir / "does_not_exist.csv"
        self._write_cases()

    def verify(self, script_path: Path, attempt: int) -> AttemptResult:
        checks = [
            self._check_usage(script_path),
            self._check_missing_column(script_path),
            self._check_valid_summary(script_path),
            self._check_bad_revenue(script_path),
            self._check_missing_month(script_path),
            self._check_missing_file(script_path),
            self._check_hidden_sorting(script_path),
        ]
        must_checks = [check for check in checks if check.priority == "must"]
        return AttemptResult(
            attempt=attempt,
            passed=all(check.passed for check in must_checks),
            checks=checks,
        )

    def _write_cases(self) -> None:
        self._write_csv(
            self.valid_csv,
            ["month", "revenue"],
            [
                ["2026-01", "100"],
                ["2026-01", "40.5"],
                ["2026-02", "20"],
            ],
        )
        self._write_csv(
            self.hidden_order_csv,
            ["month", "revenue"],
            [
                ["2026-03", "1"],
                ["2026-01", "2"],
                ["2026-02", "3"],
            ],
        )
        self._write_csv(
            self.missing_column_csv,
            ["month", "amount"],
            [["2026-01", "100"]],
        )
        self._write_csv(
            self.bad_revenue_csv,
            ["month", "revenue"],
            [["2026-01", "not-a-number"]],
        )
        self._write_csv(
            self.missing_month_csv,
            ["month", "revenue"],
            [["", "10"]],
        )

    def _write_csv(self, path: Path, header: list[str], rows: list[list[str]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)

    def _run(self, script_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script_path), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )

    def _check_usage(self, script_path: Path) -> CheckResult:
        result = self._run(script_path)
        passed = result.returncode != 0 and "Usage:" in result.stderr
        return self._check_result(
            "C1",
            "usage message",
            passed,
            result,
            "Expected non-zero exit and Usage message.",
        )

    def _check_missing_column(self, script_path: Path) -> CheckResult:
        result = self._run(script_path, str(self.missing_column_csv))
        passed = result.returncode != 0 and "Missing required columns" in result.stderr
        return self._check_result(
            "C2",
            "missing required column",
            passed,
            result,
            "Expected clear missing-column error.",
        )

    def _check_valid_summary(self, script_path: Path) -> CheckResult:
        result = self._run(script_path, str(self.valid_csv))
        expected = "month,total_revenue\n2026-01,140.50\n2026-02,20.00\n"
        passed = result.returncode == 0 and result.stdout == expected
        return self._check_result(
            "C3",
            "valid monthly summary",
            passed,
            result,
            f"Expected stdout exactly:\n{expected}",
        )

    def _check_bad_revenue(self, script_path: Path) -> CheckResult:
        result = self._run(script_path, str(self.bad_revenue_csv))
        passed = result.returncode != 0 and "Invalid revenue" in result.stderr
        return self._check_result(
            "C4",
            "reject bad revenue",
            passed,
            result,
            "Expected clear invalid-revenue error.",
        )

    def _check_missing_month(self, script_path: Path) -> CheckResult:
        result = self._run(script_path, str(self.missing_month_csv))
        passed = result.returncode != 0 and "Missing month" in result.stderr
        return self._check_result(
            "C5",
            "reject missing month",
            passed,
            result,
            "Expected clear missing-month error.",
        )

    def _check_missing_file(self, script_path: Path) -> CheckResult:
        result = self._run(script_path, str(self.missing_file))
        passed = result.returncode != 0 and "File not found" in result.stderr
        return self._check_result(
            "C6",
            "handle missing file",
            passed,
            result,
            "Expected clear file-not-found error without traceback.",
        )

    def _check_hidden_sorting(self, script_path: Path) -> CheckResult:
        result = self._run(script_path, str(self.hidden_order_csv))
        expected = "month,total_revenue\n2026-01,2.00\n2026-02,3.00\n2026-03,1.00\n"
        passed = result.returncode == 0 and result.stdout == expected
        return self._check_result(
            "C3",
            "hidden sorting sample",
            passed,
            result,
            f"Expected sorted stdout exactly:\n{expected}",
        )

    def _check_result(
        self,
        criterion_id: str,
        name: str,
        passed: bool,
        result: subprocess.CompletedProcess[str],
        expectation: str,
    ) -> CheckResult:
        criterion = self.criteria[criterion_id]
        return CheckResult(
            criterion_id=criterion.id,
            priority=criterion.priority,
            name=name,
            passed=passed,
            evidence=criterion.evidence,
            detail=self._detail(result, expectation),
        )

    def _detail(self, result: subprocess.CompletedProcess[str], expectation: str) -> str:
        return (
            f"{expectation}\n"
            f"exit_code={result.returncode}\n"
            f"stdout={result.stdout!r}\n"
            f"stderr={result.stderr!r}"
        )


class RepairPlanner:
    def plan(self, attempt: int, failed_checks: list[CheckResult]) -> RepairPlan:
        unique_failed_checks = self._dedupe_by_criterion(failed_checks)
        actions = [self._action_for(check) for check in unique_failed_checks]
        return RepairPlan(after_attempt=attempt, actions=actions)

    def _dedupe_by_criterion(self, failed_checks: list[CheckResult]) -> list[CheckResult]:
        seen: set[str] = set()
        unique: list[CheckResult] = []
        for check in failed_checks:
            if check.criterion_id in seen:
                continue
            seen.add(check.criterion_id)
            unique.append(check)
        return unique

    def _action_for(self, check: CheckResult) -> RepairAction:
        known_actions = {
            "C2": RepairAction(
                criterion_id="C2",
                diagnosis="The implementation reads row values before validating CSV headers.",
                action="Validate required columns immediately after DictReader initialization.",
                reverification="Run the missing-column CSV case and expect a clear error.",
            ),
            "C4": RepairAction(
                criterion_id="C4",
                diagnosis="The implementation lets ValueError escape as a Python traceback.",
                action="Catch numeric conversion errors and return a clear row-level message.",
                reverification="Run the bad-revenue CSV case and expect an Invalid revenue error.",
            ),
            "C5": RepairAction(
                criterion_id="C5",
                diagnosis="The implementation accepts an empty month and aggregates it as a blank key.",
                action="Strip and validate month before adding revenue to totals.",
                reverification="Run the missing-month CSV case and expect a Missing month error.",
            ),
            "C6": RepairAction(
                criterion_id="C6",
                diagnosis="The implementation lets FileNotFoundError escape as a Python traceback.",
                action="Catch FileNotFoundError and return a clear file-not-found message.",
                reverification="Run the missing-file case and expect a File not found error.",
            ),
        }
        return known_actions.get(
            check.criterion_id,
            RepairAction(
                criterion_id=check.criterion_id,
                diagnosis=f"The check '{check.name}' failed verification.",
                action="Inspect the failed evidence and adjust the implementation for this criterion.",
                reverification="Re-run the failed criterion check.",
            ),
        )


class FinalReporter:
    def render(
        self,
        contract: Contract,
        final_result: AttemptResult,
        script_path: Path,
        trace_path: Path,
        repair_plan_paths: list[Path],
    ) -> str:
        passed_checks = [check for check in final_result.checks if check.passed]
        failed_checks = final_result.failed_checks
        unique_criteria = sorted({check.criterion_id for check in final_result.checks})
        unique_passed_criteria = sorted(
            {
                check.criterion_id
                for check in final_result.checks
                if all(
                    sibling.passed
                    for sibling in final_result.checks
                    if sibling.criterion_id == check.criterion_id
                )
            }
        )
        lines = [
            "# Final Report",
            "",
            f"- Pattern version: {PATTERN_VERSION}",
            f"- Goal: {contract.goal}",
            f"- Final status: {'PASS' if final_result.passed else 'FAIL'}",
            f"- Attempts: {final_result.attempt}",
            f"- Checks passed: {len(passed_checks)}/{len(final_result.checks)}",
            f"- Criteria passed: {len(unique_passed_criteria)}/{len(unique_criteria)}",
            f"- Generated script: `{script_path.name}`",
            f"- Verification trace: `{trace_path.name}`",
            "",
            "## Verification Checks",
            "",
        ]

        for check in final_result.checks:
            status = "PASS" if check.passed else "FAIL"
            lines.append(f"- {status} {check.criterion_id} [{check.priority}] {check.name}")

        lines.extend(["", "## Repair Plans", ""])
        if repair_plan_paths:
            lines.extend(f"- `{path.name}`" for path in repair_plan_paths)
        else:
            lines.append("- No repair plan was needed.")

        lines.extend(["", "## Residual Risk", ""])
        if failed_checks:
            lines.extend(f"- {check.criterion_id}: {check.name}" for check in failed_checks)
        else:
            lines.append("- No failed must criteria remain in this demo verification suite.")

        lines.append("")
        return "\n".join(lines)


class ManifestWriter:
    def write(self, run_dir: Path, target: Path) -> None:
        files = []
        for path in sorted(item for item in run_dir.rglob("*") if item.is_file()):
            if path == target:
                continue
            files.append(
                {
                    "path": path.relative_to(run_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "sha256": self._sha256(path),
                }
            )
        payload = {
            "pattern_version": PATTERN_VERSION,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "files": files,
        }
        write_json(target, payload)

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


class ContractFirstAgent:
    def __init__(self, run_dir: Path, max_iterations: int = 2) -> None:
        self.run_dir = run_dir
        self.max_iterations = max_iterations
        self.generator = ContractGenerator()
        self.executor = Executor()
        self.repair_planner = RepairPlanner()
        self.reporter = FinalReporter()
        self.manifest_writer = ManifestWriter()

    def run(self, request: str, clean: bool = True) -> tuple[bool, RunArtifacts]:
        if clean and self.run_dir.exists():
            shutil.rmtree(self.run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)

        contract = self.generator.generate(request, max_iterations=self.max_iterations)
        artifacts = RunArtifacts(
            contract_json=self.run_dir / "contract.json",
            contract_md=self.run_dir / "contract.md",
            generated_script=self.run_dir / "generated_monthly_sales_summary.py",
            verification_trace=self.run_dir / "verification_trace.json",
            final_report=self.run_dir / "final_report.md",
            execution_summary=self.run_dir / "execution_summary.json",
            manifest=self.run_dir / "manifest.json",
            repair_plan_paths=[],
        )

        write_json(artifacts.contract_json, asdict(contract))
        artifacts.contract_md.write_text(contract.to_markdown(), encoding="utf-8")

        verifier = Verifier(self.run_dir, contract)
        attempts: list[dict[str, object]] = []
        repair_plans: list[dict[str, object]] = []
        repair_plan: RepairPlan | None = None

        print("=== Contract-First Agent Demo ===")
        print(f"Pattern version: {PATTERN_VERSION}")
        print(f"Contract generated: {artifacts.contract_json}")
        print(f"Goal: {contract.goal}")
        print(f"Acceptance criteria: {len(contract.acceptance_criteria)}")
        print("Verification checks: 7")
        print()

        final_result: AttemptResult | None = None
        for attempt in range(1, contract.max_iterations + 1):
            print(f"Attempt {attempt}: execute -> verify")
            self.executor.render_script(artifacts.generated_script, attempt, repair_plan)
            result = verifier.verify(artifacts.generated_script, attempt)
            final_result = result
            attempts.append(asdict(result))

            if result.passed:
                print("All must acceptance criteria passed.")
                break

            repair_plan = self.repair_planner.plan(attempt, result.failed_checks)
            repair_plan_path = self.run_dir / f"repair_plan_attempt_{attempt}.json"
            write_json(repair_plan_path, asdict(repair_plan))
            artifacts.repair_plan_paths.append(repair_plan_path)
            repair_plans.append(asdict(repair_plan))

            print("Failed criteria:")
            for check in result.failed_checks:
                print(f"- {check.criterion_id}: {check.name}")
            print(f"Repair plan written: {repair_plan_path}")
            print()

        assert final_result is not None
        trace_payload = {
            "pattern_version": PATTERN_VERSION,
            "contract_goal": contract.goal,
            "attempts": attempts,
            "repair_plans": repair_plans,
        }
        write_json(artifacts.verification_trace, trace_payload)
        artifacts.final_report.write_text(
            self.reporter.render(
                contract=contract,
                final_result=final_result,
                script_path=artifacts.generated_script,
                trace_path=artifacts.verification_trace,
                repair_plan_paths=artifacts.repair_plan_paths,
            ),
            encoding="utf-8",
        )

        summary_payload = {
            "pattern_version": PATTERN_VERSION,
            "request": request,
            "final_status": "PASS" if final_result.passed else "FAIL",
            "attempts": final_result.attempt,
            "checks_total": len(final_result.checks),
            "checks_passed": len([check for check in final_result.checks if check.passed]),
            "failed_checks": [asdict(check) for check in final_result.failed_checks],
            "artifacts": {
                "contract_json": artifacts.contract_json.name,
                "contract_md": artifacts.contract_md.name,
                "generated_script": artifacts.generated_script.name,
                "verification_trace": artifacts.verification_trace.name,
                "final_report": artifacts.final_report.name,
                "repair_plans": [path.name for path in artifacts.repair_plan_paths],
            },
        }
        write_json(artifacts.execution_summary, summary_payload)
        self.manifest_writer.write(self.run_dir, artifacts.manifest)

        print()
        print("=== Final Report ===")
        for check in final_result.checks:
            status = "PASS" if check.passed else "FAIL"
            print(f"{status} {check.criterion_id}: {check.name}")
        print()
        print(f"Generated script: {artifacts.generated_script}")
        print(f"Verification trace: {artifacts.verification_trace}")
        print(f"Final report: {artifacts.final_report}")
        print(f"Manifest: {artifacts.manifest}")
        return final_result.passed, artifacts


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Contract-First agent pattern demo.")
    parser.add_argument("--request", default=DEFAULT_REQUEST, help="User request to convert into a contract.")
    parser.add_argument(
        "--run-dir",
        default=str(Path(__file__).resolve().parent / "demo_run"),
        help="Directory where demo artifacts will be written.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
        help="Maximum execute/verify/repair attempts.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not remove an existing run directory before execution.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.max_iterations < 1:
        raise SystemExit("--max-iterations must be at least 1")

    run_dir = Path(args.run_dir).resolve()
    success, _ = ContractFirstAgent(run_dir, max_iterations=args.max_iterations).run(
        request=args.request,
        clean=not args.no_clean,
    )
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
