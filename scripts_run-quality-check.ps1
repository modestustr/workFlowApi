$ErrorActionPreference = "Stop"

# If Python 3.14 is installed use it.
# If not, replace with py -3.13 or py -3.12 or just python.
if (-not (Test-Path ".venv")) {
    py -3.14 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pip install -e .

pre-commit install
pre-commit run --all-files

ruff check .
ruff format --check .
pytest --cov=. --cov-report=term-missing --cov-report=xml