param([string]$Source='.',[Parameter(Mandatory=$true)][string]$AdamRoot)
Set-Location $Source; $env:PYTHONPATH=(Get-Location).Path; $env:ENTITY_ADAM_V1_ROOT=$AdamRoot
$files=@('tests/test_v342_ecosystem_runtime.py','tests/test_v3_btdu.py','tests/test_adam_v2_integration_contract.py')
python -m pytest $files -q -rs --disable-warnings
exit $LASTEXITCODE
