Set-Location -Path "C:\Users\fabri\cofluhab\cofluhab"
$out = ".\exports\movmut_progress.txt"
if (-not (Test-Path (Split-Path $out))) { New-Item -ItemType Directory -Path (Split-Path $out) -Force | Out-Null }

while ($true) {
    $ts = Get-Date -Format o
    Add-Content $out "----- $ts -----"
    if (Test-Path .\exports\movmut_import_run.log) {
        Get-Content .\exports\movmut_import_run.log -Tail 20 | ForEach-Object { Add-Content $out $_ }
    } else {
        Add-Content $out "No log yet"
    }
    try {
        & python -c "import os,sys; os.environ.setdefault('DJANGO_SETTINGS_MODULE','cofluhab.settings'); import django; django.setup(); from principal.models import Contrato,ParcelaContrato; print('contratos=',Contrato.objects.count()); print('parcelas=',ParcelaContrato.objects.count())" | ForEach-Object { Add-Content $out $_ }
    } catch {
        Add-Content $out "python-counts-error: $_"
    }
    Start-Sleep -Seconds 30
}
