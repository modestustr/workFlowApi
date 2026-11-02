from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from repo_auditor.scanner import ScanResult, scan_repository


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-auditor",
        description="Run read-only Ruff static analysis on a local Python repository.",
    )
    parser.add_argument("repository", type=Path, help="Path to the local repository to inspect")
    parser.add_argument(
        "--target-version",
        default="py310",
        choices=[f"py3{minor}" for minor in range(10, 15)],
        help="Minimum Python version the target repository supports (default: py310)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report format (default: text)",
    )
    return parser


def _print_text(result: ScanResult) -> None:
    print(f"Repository: {result.repository}")
    print(f"Python files scanned: {result.files_scanned}")
    print(f"Findings: {len(result.findings)}")
    for finding in result.findings:
        print(f"{finding.file}:{finding.line}:{finding.column}: {finding.code} {finding.message}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = scan_repository(args.repository, target_version=args.target_version)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"repo-auditor: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        _print_text(result)

    return 1 if result.findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
