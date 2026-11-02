import json
from pathlib import Path

from repo_auditor.cli import main
from repo_auditor.scanner import scan_repository


def test_scan_reports_ruff_findings(tmp_path: Path) -> None:
    (tmp_path / "module.py").write_text("import os\n", encoding="utf-8")

    result = scan_repository(tmp_path)

    assert result.findings
    assert result.findings[0].code == "F401"
    assert result.findings[0].file == "module.py"


def test_scan_does_not_execute_target_code(tmp_path: Path) -> None:
    marker = tmp_path / "executed.txt"
    (tmp_path / "module.py").write_text(
        "from pathlib import Path\nPath('executed.txt').write_text('yes')\n",
        encoding="utf-8",
    )

    scan_repository(tmp_path)

    assert not marker.exists()


def test_cli_emits_json_and_nonzero_exit_for_findings(tmp_path: Path, capsys) -> None:
    (tmp_path / "module.py").write_text("import os\n", encoding="utf-8")

    exit_code = main([str(tmp_path), "--format", "json"])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["finding_count"] == 1
    assert output["findings"][0]["code"] == "F401"


def test_cli_reports_invalid_repository(tmp_path: Path, capsys) -> None:
    missing_path = tmp_path / "missing"

    exit_code = main([str(missing_path)])

    assert exit_code == 2
    assert "does not exist" in capsys.readouterr().err
