param([string]$Source='.',[string]$Python='python',[string]$QualificationSite='')
$ErrorActionPreference='Stop'; Set-Location $Source; $env:PYTHONPATH=(Get-Location).Path
if($QualificationSite){$env:PYTHONPATH="$QualificationSite;$env:PYTHONPATH"}
& $Python -m pytest tests/test_portable_export_scope.py -q --disable-warnings
exit $LASTEXITCODE
