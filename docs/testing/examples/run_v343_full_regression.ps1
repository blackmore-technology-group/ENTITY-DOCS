param([string]$Source='.')
$ErrorActionPreference='Stop'
Set-Location $Source
$head=(git rev-parse HEAD).Trim(); $tag=(git describe --tags --exact-match HEAD).Trim()
if($head -ne '528b70aabd05b1e930b77e4933f157731e47274f'){throw "Unexpected commit: $head"}
if($tag -ne 'v3.4.3'){throw "Unexpected tag: $tag"}
$env:PYTHONPATH=(Get-Location).Path
python -m pytest tests -q --disable-warnings
exit $LASTEXITCODE
