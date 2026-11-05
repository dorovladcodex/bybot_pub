from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
from uuid import UUID, uuid4

from app.bybit.demo import (
    DemoExecutionService,
    classify_demo_order_ownership,
)
from app.models import (
    DemoExecutionRecord,
    DemoExecutionState,
    ExecutionEnvironment,
    Side,
    Symbol,
)
from tests.test_bybit_demo_execution import (
    FakeDemoClient,
    MemoryRepository,
    demo_settings,
)








def _flat_positions() -> list[dict]:
    return [
        {"symbol": "AVAXUSDT", "size": "0", "positionIdx": 0},
    ]


class AutoCancelClient(FakeDemoClient):
    def __init__(self, orders: list[dict], *, remove_on_cancel: bool = True):
        super().__init__()
        self.open_orders = [dict(item) for item in orders]
        self.positions = _flat_positions()
        self.remove_on_cancel = remove_on_cancel

    def cancel_order(self, symbol, order_id):
        super().cancel_order(symbol, order_id)
        if self.remove_on_cancel:
            self.open_orders = [
                item
                for item in self.open_orders
                if str(item.get("orderId") or "") != order_id
            ]
        return {"retCode": 0}
