[CmdletBinding()]
param(
    [switch]$AllowDemoOrders,
    [ValidateSet("BTCUSDT", "ETHUSDT")][string]$Symbol = "BTCUSDT",
    [Parameter(Mandatory)][ValidateRange(1, 1000)][decimal]$MaxNotionalUSDT,
    [ValidateRange(0.001, 1)][decimal]$MinTrendChangePct = 0.01,
    [ValidateRange(0.1, 100)][decimal]$MinExpectedEdgeBps = 3,
    [ValidateRange(0.1, 2)][decimal]$StopLossPct = 0.5,
    [ValidateRange(0.1, 4)][decimal]$TakeProfitPct = 1
)

$ErrorActionPreference = "Stop"
if (-not $AllowDemoOrders) { throw "Explicit -AllowDemoOrders is required." }
if (-not $env:BYBIT_API_KEY -or -not $env:BYBIT_API_SECRET) {
    throw "Set BYBIT_API_KEY and BYBIT_API_SECRET using your Bybit Demo credentials."
}

Set-Location (Split-Path -Parent $PSScriptRoot)
$python = Join-Path (Get-Location) ".venv\Scripts\python.exe"
$databaseName = if ($Symbol -eq "ETHUSDT") { "bybot_news_demo_eth" } else { "bybot_news_demo" }
$env:DATABASE_URL = "postgresql+psycopg://bybot:bybot@127.0.0.1:5432/$databaseName"
$env:APP_ENV = "demo"
$env:BOT_MODE = "BYBIT_DEMO"
$env:EXECUTION_MODE = "BYBIT_DEMO"
$env:TEST_MODE = "false"
$env:BYBIT_ENV = "demo"
$env:BYBIT_ENABLE_TRADING = "false"
$env:BYBIT_LIVE_TRADING_ENABLED = "false"
$env:BYBIT_DEMO_TRADING_ENABLED = "true"
$env:DEMO_ORDER_EXECUTION_AUTHORIZED = "true"
$env:BYBIT_PRIVATE_DEMO_BASE_URL = "https://api-demo.bybit.com"
$env:BYBIT_PRIVATE_DEMO_WS_URL = "wss://stream-demo.bybit.com"
$env:V2_ENABLED = "false"
$env:V2_AUTO_DEMO_EXECUTION = "false"
$env:AUTO_PAPER_EXECUTION = "false"
$env:DEMO_CANARY_ENABLED = "false"
$env:DEMO_LEVERAGE = "1"
$env:NEWS_ENABLE_RSS = "false"
$env:NEWS_CLASSIFIER_MODE = "mock"
$env:NEWS_POLL_INTERVAL_SECONDS = "10"
$env:MARKET_DATA_PROVIDER = "BYBIT_REST"
$env:ACTIVE_SYMBOLS = "[`"$Symbol`"]"
$env:ALLOWED_SYMBOLS = $env:ACTIVE_SYMBOLS
$culture = [Globalization.CultureInfo]::InvariantCulture
$env:MAX_POSITION_NOTIONAL_USDT = $MaxNotionalUSDT.ToString($culture)
$env:SIGNAL_MIN_TREND_CHANGE_PCT = $MinTrendChangePct.ToString($culture)
$env:SIGNAL_MIN_EXPECTED_EDGE_BPS = $MinExpectedEdgeBps.ToString($culture)
$env:MIN_EXPECTED_EDGE_BPS = $MinExpectedEdgeBps.ToString($culture)
$env:SIGNAL_DEFAULT_STOP_LOSS_PCT = $StopLossPct.ToString($culture)
$env:SIGNAL_DEFAULT_TAKE_PROFIT_PCT = $TakeProfitPct.ToString($culture)

& $python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8011
exit $LASTEXITCODE
