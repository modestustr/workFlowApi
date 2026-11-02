from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

EXCLUDED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".tox",
    ".nox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    "node_modules",
}
BATCH_SIZE = 50


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    file: str
    line: int
    column: int
    explanation: str
    suggestion: str
    rule_url: str | None


@dataclass(frozen=True)
class ScanResult:
    repository: str
    files_scanned: int
    findings: list[Finding]

    def to_dict(self) -> dict[str, object]:
        return {
            "repository": self.repository,
            "files_scanned": self.files_scanned,
            "finding_count": len(self.findings),
            "findings": [asdict(finding) for finding in self.findings],
        }


def _raise_walk_error(error: OSError) -> None:
    raise error


def _python_files(root: Path) -> list[Path]:
    python_files: list[Path] = []
    for current_dir, directories, filenames in os.walk(
        root,
        followlinks=False,
        onerror=_raise_walk_error,
    ):
        directories[:] = [
            name
            for name in directories
            if name not in EXCLUDED_DIRECTORIES and not (Path(current_dir) / name).is_symlink()
        ]
        python_files.extend(
            Path(current_dir) / name
            for name in filenames
            if Path(name).suffix in {".py", ".pyi"} and not (Path(current_dir) / name).is_symlink()
        )
    return python_files


def _relative_file(filename: str, root: Path) -> str:
    path = Path(filename)
    if not path.is_absolute():
        path = root / path
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.name


def _run_ruff(files: list[Path], root: Path, target_version: str) -> list[object]:
    ruff_executable = Path(sys.executable).with_name("ruff.exe" if os.name == "nt" else "ruff")
    if not ruff_executable.is_file():
        raise RuntimeError(f"Ruff executable not found beside the active Python: {ruff_executable}")

    command = [
        str(ruff_executable),
        "check",
        "--isolated",
        "--no-cache",
        "--output-format",
        "json",
        "--select",
        "E,F,I,B,UP",
        "--target-version",
        target_version,
        "--line-length",
        "120",
        *[str(path) for path in files],
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Ruff static analysis timed out after 120 seconds.") from error
    except OSError as error:
        raise RuntimeError(f"Could not start Ruff static analysis: {error}") from error

    if completed.returncode not in (0, 1):
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(f"Ruff static analysis failed: {detail}")

    try:
        raw_findings = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("Ruff returned invalid JSON output.") from error
    if not isinstance(raw_findings, list):
        raise RuntimeError("Ruff returned an unexpected JSON result.")
    return raw_findings


def _parse_finding(item: object, root: Path) -> Finding:
    if not isinstance(item, dict):
        raise RuntimeError("Ruff returned a malformed finding.")
    location = item.get("location")
    if (
        not isinstance(item.get("code"), str)
        or not isinstance(item.get("message"), str)
        or not isinstance(item.get("filename"), str)
        or not isinstance(location, dict)
        or not isinstance(location.get("row"), int)
        or not isinstance(location.get("column"), int)
    ):
        raise RuntimeError("Ruff returned a malformed finding.")
    code = item["code"]
    message = item["message"]
    explanation, suggestion = _finding_guidance(code, message)
    rule_url = item.get("url")
    return Finding(
        code=code,
        message=message,
        file=_relative_file(item["filename"], root),
        line=location["row"],
        column=location["column"],
        explanation=explanation,
        suggestion=suggestion,
        rule_url=rule_url if isinstance(rule_url, str) else None,
    )


def _finding_guidance(code: str, message: str) -> tuple[str, str]:
    if code == "E501":
        details = message.removeprefix("Line too long (").removesuffix(")")
        try:
            length, limit = (int(value.strip()) for value in details.split(">", maxsplit=1))
        except ValueError:
            return (
                "Satır, projede belirlenen maksimum satır uzunluğunu aşıyor.",
                "Uzun ifadeyi okunabilir, parantezli çok satırlı bir yapıya bölün.",
            )
        return (
            f"Satır {length} karakter; izin verilen {limit} karakter sınırını {length - limit} karakter aşıyor.",
            "Uzun ifadeyi parantezli çok satırlı bir yapıya bölün. String ifadelerinde içeriği değiştirmeden "
            "bölünebildiğini kontrol edin.",
        )
    if code == "F401":
        return (
            "İçe aktarılan modül veya isim dosyada kullanılmıyor.",
            "İçe aktarım gereksizse kaldırın; yalnızca yan etkisi için kullanılıyorsa bu tercihi açıkça belgeleyin.",
        )
    return (
        f"{code} kuralı: {message}",
        "İlgili Ruff kuralı ve önerilen düzeltme için rapordaki kural bağlantısını açın.",
    )


def scan_repository(repository: Path, target_version: str = "py310") -> ScanResult:
    expanded_path = repository.expanduser()
    if not expanded_path.exists():
        raise ValueError(f"Repository path does not exist: {repository}")
    root = expanded_path.resolve()
    if not root.is_dir():
        raise ValueError(f"Repository path is not a directory: {root}")

    python_files = _python_files(root)
    findings = [
        _parse_finding(item, root)
        for index in range(0, len(python_files), BATCH_SIZE)
        for item in _run_ruff(python_files[index : index + BATCH_SIZE], root, target_version)
    ]
    return ScanResult(repository=str(root), files_scanned=len(python_files), findings=findings)
