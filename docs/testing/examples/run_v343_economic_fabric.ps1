param([string]$Source='.')
Set-Location $Source; $env:PYTHONPATH=(Get-Location).Path
$files=@('tests/test_v3_economic_participation.py','tests/test_v3_eep_conformance.py','tests/test_v3_exchange_convergence.py','tests/test_v3_verifiable_reality.py')
python -m pytest $files -q --disable-warnings
exit $LASTEXITCODE
