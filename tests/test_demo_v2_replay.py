from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from app.bybit.demo_replay import DemoReplayFixture, DemoV2ReplayHarness
from app.models import (
    DemoExecutionRecord, DemoExecutionState, DemoFill, Side, Symbol,
)
from app.v2.analytics import V2ReportGenerator








def _older_profitable_near(*, run_id: str) -> DemoExecutionRecord:
    opened = datetime(2026, 7, 20, 15, 27, tzinfo=timezone.utc)
    closed = opened + timedelta(minutes=5)
    return DemoExecutionRecord(
        id=UUID("4d929c18-acbd-4e06-9502-bc3422d25df3"),
        candidate_id=uuid4(), run_id=run_id,
        order_link_id="bybot-older-near-entry",
        order_id="older-near-entry-order",
        close_order_id="older-near-take-profit-order",
        state=DemoExecutionState.DEMO_CLOSED,
        symbol=Symbol.NEARUSDT, side=Side.BUY,
        strategy_name="OIFundingSqueezeStrategy",
        strategy_version="2.1.0",
        requested_quantity=Decimal("25"),
        accepted_quantity=Decimal("25"),
        average_fill_price=Decimal("1.86"),
        average_close_price=Decimal("1.868"),
        fills=[DemoFill(
            execution_id="older-near-entry-exec",
            order_id="older-near-entry-order", quantity=Decimal("25"),
            price=Decimal("1.86"), fee=Decimal("0.027"),
            fee_currency="USDT", executed_at=opened,
        )],
        close_fills=[DemoFill(
            execution_id="older-near-close-exec",
            order_id="older-near-take-profit-order", quantity=Decimal("25"),
            price=Decimal("1.868"), fee=Decimal("0.02884303"),
            fee_currency="USDT", executed_at=closed,
        )],
        exchange_fees=Decimal("0.05584303"),
        gross_realized_pnl=Decimal("0.2"),
        realized_exchange_pnl=Decimal("0.14415697"),
        paper_shadow_pnl=Decimal("0.14415697"),
        close_reason="take_profit", exit_attribution="take_profit",
        closed_at=closed, created_at=opened, updated_at=closed,
    )
