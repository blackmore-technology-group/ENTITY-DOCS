param([string]$Source='.',[string]$Python='python',[string]$QualificationSite='')
$ErrorActionPreference='Stop'; Set-Location $Source; $env:PYTHONPATH=(Get-Location).Path
if($QualificationSite){$env:PYTHONPATH="$QualificationSite;$env:PYTHONPATH"}
$files=@('tests/test_v3_adoption_layer.py','tests/test_v3_global_conformance.py','tests/test_v3_protocol_origin_lineage.py')
& $Python -m pytest $files -q --disable-warnings
exit $LASTEXITCODE
