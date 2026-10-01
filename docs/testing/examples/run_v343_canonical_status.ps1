param([string]$Source='.',[string]$Python='python')
$ErrorActionPreference='Stop'; Set-Location $Source
$env:PYTHONPATH=(Get-Location).Path
& $Python -m pytest tests/test_v342_canonical_status.py -q --disable-warnings
exit $LASTEXITCODE
