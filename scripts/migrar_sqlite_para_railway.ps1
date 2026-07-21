param(
    [Parameter(Mandatory = $true)]
    [string]$DatabaseUrl,

    [string]$ProjectRoot = "c:\Users\fabri\cofluhab\cofluhab",

    [string]$FixturePath = "c:\Users\fabri\cofluhab\cofluhab\exports\railway-bootstrap.json.gz"
)

$ErrorActionPreference = "Stop"

Set-Location $ProjectRoot

if (Test-Path ".venv\Scripts\python.exe") {
    $pythonExe = ".\.venv\Scripts\python.exe"
} elseif (Test-Path "venv\Scripts\python.exe") {
    $pythonExe = ".\venv\Scripts\python.exe"
} else {
    $pythonExe = "python"
}

Write-Host "[1/4] Exportando dados do SQLite para fixture compactada..."
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
$dumpArgs = @(
    "manage.py"
    "dumpdata"
    "--exclude"
    "auth.permission"
    "--exclude"
    "contenttypes"
    "--exclude"
    "sessions"
    "--natural-foreign"
    "--natural-primary"
    "--output"
    $FixturePath
)
& $pythonExe @dumpArgs

Write-Host "[2/4] Validando fixture gerada..."
if (-not (Test-Path $FixturePath)) {
    throw "Fixture não foi criada em $FixturePath"
}

Write-Host "[3/4] Aplicando migrações no PostgreSQL do Railway..."
$Env:DATABASE_URL = $DatabaseUrl
& $pythonExe manage.py migrate --noinput

Write-Host "[4/4] Carregando dados no PostgreSQL do Railway..."
& $pythonExe manage.py loaddata $FixturePath

Write-Host "Migração concluída. O arquivo de dados ficou em: $FixturePath"