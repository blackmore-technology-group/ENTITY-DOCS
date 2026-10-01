param([string]$Source='.')
$ErrorActionPreference='Stop'; Set-Location $Source
$env:PYTHONPATH=(Get-Location).Path
$files=@('tests/test_v3_crypto_assurance.py','tests/test_repository_safety.py','tests/test_portable_export_scope.py','tests/test_v3_hardening_exchange.py','tests/test_v3_market_recovery.py')
python -m pytest $files -q --disable-warnings
exit $LASTEXITCODE
