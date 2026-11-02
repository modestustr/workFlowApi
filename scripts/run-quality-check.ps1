$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot

try {
    $VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
    $VenvScripts = Join-Path $ProjectRoot '.venv\Scripts'

    if (-not (Test-Path -LiteralPath $VenvPython)) {
        & py -3.14 -m venv .venv
        if ($LASTEXITCODE -ne 0) {
            throw 'Failed to create .venv with Python 3.14.'
        }
    }

    $VenvSitePackages = Join-Path $ProjectRoot '.venv\Lib\site-packages'
    $SiteCustomization = @'
import os
import sys

base_prefix = os.path.normcase(os.path.abspath(sys.base_prefix))
sys.path[:] = [
    path
    for path in sys.path
    if os.path.normcase(os.path.abspath(path or os.curdir)) != base_prefix
]
'@
    Set-Content -LiteralPath (Join-Path $VenvSitePackages 'sitecustomize.py') -Value $SiteCustomization -Encoding ASCII

    $OriginalPath = $env:PATH
    $env:PATH = "$VenvScripts;$OriginalPath"
    try {
        & $VenvPython -m ensurepip --upgrade
        if ($LASTEXITCODE -ne 0) {
            throw 'Failed to bootstrap pip inside .venv.'
        }

        & $VenvPython -m pip --isolated install --ignore-installed -r requirements.txt -r requirements-dev.txt
        if ($LASTEXITCODE -ne 0) {
            throw 'Failed to install dependencies into .venv.'
        }

        & $VenvPython -m pip --isolated install --no-deps -e .
        if ($LASTEXITCODE -ne 0) {
            throw 'Failed to install the local CLI package into .venv.'
        }

        & $VenvPython -m pre_commit install
        if ($LASTEXITCODE -ne 0) {
            throw 'Failed to install the pre-commit hook.'
        }

        & $VenvPython -m pre_commit run --all-files
        if ($LASTEXITCODE -ne 0) {
            throw 'Pre-commit checks failed.'
        }

        & $VenvPython -m ruff check .
        if ($LASTEXITCODE -ne 0) {
            throw 'Ruff lint checks failed.'
        }

        & $VenvPython -m ruff format --check .
        if ($LASTEXITCODE -ne 0) {
            throw 'Ruff format check failed.'
        }

        & $VenvPython -m pytest --cov=. --cov-report=term-missing --cov-report=xml
        if ($LASTEXITCODE -ne 0) {
            throw 'Pytest failed.'
        }
    }
    finally {
        $env:PATH = $OriginalPath
    }
}
finally {
    Pop-Location
}
