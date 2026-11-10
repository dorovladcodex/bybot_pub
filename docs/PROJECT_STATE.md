# Project state

## Implemented

- News ingestion, filtering, mock/optional LLM classification, signal and risk
  records; a separate local PAPER workflow with simulated costs and accounting.
- V2 market features, six deterministic strategies (one disabled by default),
  scoring and portfolio reservations. V2 and automatic Demo execution require
  explicit enabling.
- Bybit Demo-only adapter, reservations, event history, reconciliation, protection
  management and fail-closed controls. Live execution is blocked.
- PostgreSQL persistence, Alembic migrations, local Docker paper demonstration,
  automated tests and historical backtesting components.

The single Alembic head verified by `python -m alembic heads` is
`20260811_0015`. This migration adds V4 research tables to the V2 history.

## Experimental and planned

V4/V5 research and shadow-analysis modules are experimental and do not establish
profitability. GCP deployment is documented as a target, not verified. This
sanitized public snapshot omits private historical exchange fixtures and account
data. Test success is not evidence of profitability or production readiness.

## Known engineering limitations

- Large execution and runtime modules merit incremental extraction backed by
  regression tests; a line-count refactor alone would increase risk.
- In-memory market history and a single-process design constrain recovery and
  scaling. Legacy financial tables retain floating-point fields.
- API authentication and production deployment hardening are absent. Some
  test-named endpoints accept requests outside local TEST_MODE; do not expose the
  API to untrusted clients. Compose credentials are local examples only.
- Dependencies use ranges rather than a lock file; audit and pin for deployment.
- PostgreSQL tests need an explicitly configured disposable test database.

Paper equity is starting equity plus cumulative net realized PnL and current
unrealized PnL. Paper sizing does not use Bybit Demo wallet equity. See the
[architecture](ARCHITECTURE.md), [security policy](SECURITY.md) and [runbook](RUNBOOK.md).
