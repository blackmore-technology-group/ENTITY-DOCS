param([string]$Source='.',[string]$Python='python',[Parameter(Mandatory=$true)][string]$AdamRoot,[string]$QualificationSite='')
$ErrorActionPreference='Stop'; Set-Location $Source
$head=(git rev-parse HEAD).Trim(); $tag=(git describe --tags --exact-match HEAD).Trim()
if($head -ne '528b70aabd05b1e930b77e4933f157731e47274f'){throw "Unexpected commit: $head"}
if($tag -ne 'v3.4.3'){throw "Unexpected tag: $tag"}
$env:ENTITY_ADAM_V1_ROOT=$AdamRoot; $env:PYTHONPATH=(Get-Location).Path
if($QualificationSite){$env:PYTHONPATH="$QualificationSite;$env:PYTHONPATH"}
& $Python -m pytest tests -q --disable-warnings
exit $LASTEXITCODE
