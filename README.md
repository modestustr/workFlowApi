# Repo Auditor

Repo Auditor is a local command-line tool for read-only static checks of Python repositories. It reports Ruff findings for `E`, `F`, `I`, `B`, and `UP` rules in `.py` and `.pyi` files.

The scanner does not run code, tests, build steps, package install hooks, or commands defined by the repository being inspected. It uses the Ruff executable installed with Repo Auditor, ignores the target repository's Ruff configuration, and does not write Ruff caches or modify scanned files. Python files in common environment, cache, build, and dependency directories are skipped.

## Install

From the Repo Auditor checkout, use PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

## Scan a local repository

Interactive Windows menu:

```powershell
.\scripts\run-audit.bat
```

The menu asks for the repository folder, Python target version, and report format. Enter the folder path without surrounding quotes; paths containing spaces are supported.

Direct command:

```powershell
.\.venv\Scripts\repo-auditor.exe "D:\path\to\python-repository"
.\.venv\Scripts\repo-auditor.exe "D:\path\to\python-repository" --target-version py313 --format json
```

The default target version is `py310`. The supported values are `py310` through `py314`.

Each finding includes the rule code, file and line location, a short explanation, a suggested next step, and a link to the rule documentation when Ruff provides one. For example, an `E501` finding reports the actual line length, configured limit, and number of excess characters. The scanner reports findings only; it does not automatically fix the target repository.

Exit codes:

- `0`: scan completed with no findings
- `1`: scan completed and findings were reported
- `2`: invalid input or scanner failure

This first version is intentionally a local CLI rather than an API: it avoids exposing a service that accepts and scans arbitrary repositories. A future API should use isolated workers and explicit resource limits before it accepts remote or uploaded code.
