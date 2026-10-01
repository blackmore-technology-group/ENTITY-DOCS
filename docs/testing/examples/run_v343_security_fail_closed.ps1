param([string]$Source='.',[string]$Python='python',[Parameter(Mandatory=$true)][string]$AdamRoot,[string]$QualificationSite='')
$ErrorActionPreference='Stop'; Set-Location $Source; $env:ENTITY_ADAM_V1_ROOT=$AdamRoot; $env:PYTHONPATH=(Get-Location).Path
if($QualificationSite){$env:PYTHONPATH="$QualificationSite;$env:PYTHONPATH"}
$files=@('tests/test_repository_safety.py','tests/test_v3_crypto_assurance.py','tests/test_v3_btdu.py','tests/test_v3_hardening_exchange.py','tests/test_v3_market_recovery.py','tests/test_v3_global_infrastructure.py','tests/test_v3_global_passports.py','tests/test_v3_data_economic_sovereignty.py','tests/test_v343_issue28_regressions.py','tests/test_v3_exchange_convergence.py')
& $Python -m pytest $files -q --disable-warnings
exit $LASTEXITCODE
