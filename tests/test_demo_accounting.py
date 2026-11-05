from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path

import pytest

from app.bybit.demo_accounting import calculate_fill_level_accounting
from app.models import Side, Symbol
