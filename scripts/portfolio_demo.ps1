[CmdletBinding()]
param([switch]$SkipBuild)

$ErrorActionPreference = "Stop"
$composeFile = Join-Path $PSScriptRoot "../compose.portfolio.yml"
$composeArgs = @("compose", "--project-name", "bybot-portfolio", "--file", $composeFile)

Write-Host "Starting the local ByBot demo and its PostgreSQL database..."
[string[]]$imageArgs = if ($SkipBuild) { "--no-build", "--pull", "never" } else { "--build" }
& docker @composeArgs up -d @imageArgs --wait --wait-timeout 120
if ($LASTEXITCODE -ne 0) {
    throw "Could not start the portfolio stack. Check Docker Desktop and port 8010."
}

$restartApi = {
    Write-Host "Replacing the API container while PostgreSQL keeps its state..."
    & docker @composeArgs up -d --no-deps --no-build --pull never --force-recreate --wait --wait-timeout 120 api
    if ($LASTEXITCODE -ne 0) {
        throw "The API did not come back after the restart."
    }
}.GetNewClosure()

& (Join-Path $PSScriptRoot "paper_execution_smoke.ps1") -BaseUrl "http://127.0.0.1:8010" -RestartApi $restartApi
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "API explorer: http://127.0.0.1:8010/docs"
Write-Host "Closed trades: http://127.0.0.1:8010/paper/trades"
Write-Host "Paper account: http://127.0.0.1:8010/paper/pnl"
