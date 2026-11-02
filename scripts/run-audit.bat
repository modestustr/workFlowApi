@echo off
setlocal

for %%I in ("%~dp0..") do set "PROJECT_ROOT=%%~fI"
set "REPO_AUDITOR_EXE=%PROJECT_ROOT%\.venv\Scripts\repo-auditor.exe"

if not exist "%REPO_AUDITOR_EXE%" (
    echo Repo Auditor is not installed in this project's .venv.
    echo First run: .\scripts\run-quality-check.ps1
    set "AUDIT_EXIT_CODE=2"
    goto :finish
)

powershell.exe -NoProfile -Command "$repository = Read-Host 'Denetlenecek Python repo klasorunun yolunu girin'; if ([string]::IsNullOrWhiteSpace($repository)) { [Console]::Error.WriteLine('Klasor yolu bos olamaz.'); exit 2 }; if (-not (Test-Path -LiteralPath $repository -PathType Container)) { [Console]::Error.WriteLine('Belirtilen klasor bulunamadi.'); exit 2 }; $repository = [System.IO.Path]::GetFullPath($repository); Write-Host 'Python surumu: 1) 3.10  2) 3.11  3) 3.12  4) 3.13  5) 3.14'; $versionChoice = Read-Host 'Hedef surumu secin [1-5]'; $targetVersion = switch ($versionChoice) { '1' { 'py310' } '2' { 'py311' } '3' { 'py312' } '4' { 'py313' } '5' { 'py314' } default { $null } }; if ($null -eq $targetVersion) { [Console]::Error.WriteLine('Gecersiz Python surumu secimi.'); exit 2 }; Write-Host 'Rapor formati: 1) Metin  2) JSON'; $formatChoice = Read-Host 'Rapor formatini secin [1-2]'; $reportFormat = switch ($formatChoice) { '1' { 'text' } '2' { 'json' } default { $null } }; if ($null -eq $reportFormat) { [Console]::Error.WriteLine('Gecersiz rapor formati secimi.'); exit 2 }; & $env:REPO_AUDITOR_EXE $repository --target-version $targetVersion --format $reportFormat; exit $LASTEXITCODE"
set "AUDIT_EXIT_CODE=%ERRORLEVEL%"

:finish
echo.
echo Tarama bitti. Sonucu incelemek icin pencereyi kapatmayin.
pause
exit /b %AUDIT_EXIT_CODE%
