param([string]$Source='.')
$ErrorActionPreference='Stop'; Set-Location $Source
$env:PYTHONPATH=(Get-Location).Path
python -m pytest tests/test_v343_issue28_regressions.py -q --disable-warnings
exit $LASTEXITCODE
