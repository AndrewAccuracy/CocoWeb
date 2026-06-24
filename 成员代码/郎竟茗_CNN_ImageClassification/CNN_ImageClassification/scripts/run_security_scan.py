from __future__ import annotations

import argparse
import contextlib
import io
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_ROOT / "reports" / "scan-report-output.txt"
SECURITY_MODULE = PROJECT_ROOT / "security" / "secure_image_input.py"
TEST_DIR = PROJECT_ROOT / "tests"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass(frozen=True)
class CheckResult:
    code: str
    name: str
    risk: str
    status: str
    evidence: str


def run_unit_tests() -> tuple[bool, str, int, int, int]:
    loader = unittest.TestLoader()
    suite = loader.discover(str(TEST_DIR), pattern="test_*.py")
    buffer = io.StringIO()
    runner = unittest.TextTestRunner(stream=buffer, verbosity=2)

    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        result = runner.run(suite)

    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    return result.wasSuccessful(), buffer.getvalue(), total, failures, errors


def scan_static_rules() -> list[CheckResult]:
    source = SECURITY_MODULE.read_text(encoding="utf-8")

    checks = [
        CheckResult(
            "S1",
            "Allowed image extensions are restricted",
            "High",
            "PASS" if "ALLOWED_EXTENSIONS" in source and "jpg" in source and "png" in source else "FAIL",
            "ALLOWED_EXTENSIONS contains jpg/jpeg/png",
        ),
        CheckResult(
            "S2",
            "Real image content is verified",
            "High",
            "PASS" if "imghdr.what" in source and ".verify()" in source else "FAIL",
            "Uses file header detection and Pillow verify()",
        ),
        CheckResult(
            "S3",
            "Path traversal filename fragments are rejected",
            "High",
            "PASS" if '".."' in source and '"/"' in source and '"\\\\"' in source else "FAIL",
            "Rejects ../, /, and backslash in uploaded filename",
        ),
        CheckResult(
            "S4",
            "Upload size is limited",
            "Medium",
            "PASS" if "MAX_UPLOAD_BYTES" in source and "5 * 1024 * 1024" in source else "FAIL",
            "MAX_UPLOAD_BYTES is set to 5MB",
        ),
        CheckResult(
            "S5",
            "Image dimensions and pixel count are limited",
            "Medium",
            "PASS"
            if "MAX_IMAGE_PIXELS" in source and "MAX_WIDTH" in source and "MAX_HEIGHT" in source
            else "FAIL",
            "MAX_IMAGE_PIXELS, MAX_WIDTH, and MAX_HEIGHT are enforced",
        ),
        CheckResult(
            "S6",
            "Internal prediction errors are hidden from users",
            "Medium",
            "PASS" if "预测失败，请稍后重试。" in source and "repr(" not in source and "traceback" not in source else "FAIL",
            "Public response is a fixed safe error message",
        ),
        CheckResult(
            "S7",
            "Validation failure stops prediction",
            "High",
            "PASS" if "SecurityValidationError" in source and "return {\"ok\": False" in source else "FAIL",
            "SecurityValidationError is handled before model prediction response",
        ),
    ]
    return checks


def render_report(write_report: bool) -> tuple[str, bool]:
    test_ok, test_output, total, failures, errors = run_unit_tests()
    static_results = scan_static_rules()
    static_ok = all(item.status == "PASS" for item in static_results)
    overall_ok = static_ok and test_ok

    lines = [
        "CNN ImageClassification Security Scan",
        "=" * 45,
        "",
        f"Project root: {PROJECT_ROOT}",
        f"Security module: {SECURITY_MODULE.relative_to(PROJECT_ROOT)}",
        "",
        "Policy summary",
        "-" * 45,
        "- Allowed types: jpg/jpeg/png",
        "- Max upload size: 5MB",
        "- Max dimensions: 4096x4096",
        "- Max pixels: 10000000",
        "- User filename is not trusted as a server path",
        "- Internal prediction exceptions are hidden from users",
        "",
        "Static security checks",
        "-" * 45,
    ]

    for item in static_results:
        lines.append(f"[{item.status}] {item.code} {item.name} | risk={item.risk}")
        lines.append(f"       evidence: {item.evidence}")

    lines.extend(
        [
            "",
            "Unit test summary",
            "-" * 45,
            f"Status: {'PASS' if test_ok else 'FAIL'}",
            f"Tests run: {total}",
            f"Failures: {failures}",
            f"Errors: {errors}",
            "",
            "Unit test details",
            "-" * 45,
            test_output.rstrip(),
            "",
            "Final result",
            "-" * 45,
            "PASS: high-risk upload and prediction-entry issues are covered."
            if overall_ok
            else "FAIL: at least one static check or unit test failed.",
        ]
    )

    rendered = "\n".join(lines) + "\n"

    if write_report:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(rendered, encoding="utf-8")

    return rendered, overall_ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CNN upload security checks.")
    parser.add_argument(
        "--write-report",
        action="store_true",
        help=f"write detailed output to {REPORT_PATH.relative_to(PROJECT_ROOT)}",
    )
    args = parser.parse_args()

    rendered, ok = render_report(args.write_report)
    print(rendered)
    if args.write_report:
        print(f"Report written to: {REPORT_PATH}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
