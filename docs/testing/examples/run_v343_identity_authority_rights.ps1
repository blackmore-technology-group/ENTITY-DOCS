param([string]$Source='.')
Set-Location $Source; $env:PYTHONPATH=(Get-Location).Path
$files=@('tests/test_public_contract.py','tests/test_v3_universal_fabric.py','tests/test_v3_global_passports.py','tests/test_v3_profiles.py','tests/test_v3_data_economic_sovereignty.py')
python -m pytest $files -q --disable-warnings
exit $LASTEXITCODE
