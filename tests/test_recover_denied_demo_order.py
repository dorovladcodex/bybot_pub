from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.models import DemoExecutionState
from scripts.recover_denied_demo_order import blockers_for_denied_submission


def evidence():
    now = datetime.now(timezone.utc)
    incident = now - timedelta(minutes=5)
    record = SimpleNamespace(
        id="execution", state=DemoExecutionState.DEMO_NOT_SUBMITTED,
        order_id=None, accepted_quantity=Decimal("0"), fills=[],
        cleanup_result="remote position flat and bot-owned orders zero",
    )
    events = [
        {"event_type": "CREATE_UNCERTAIN", "occurred_at": incident,
         "last_error": "Bybit Demo request failed: Permission denied"},
        *[{"event_type": name} for name in (
            "READ_ONLY_RECONCILIATION_COMPLETED", "EXECUTION_REPAIR_APPLIED",
            "FINAL_REMOTE_STATE_FLAT")],
    ]
    status = SimpleNamespace(
        failures=[], kill_switch={"active": True,
            "reasons": ["entry submission outcome is uncertain"],
            "events": [{"event_type": "KILL_SWITCH_ACTIVATED", "active": True,
                        "created_at": incident, "execution_id": None}]},
        latest_execution=record, newest_execution=record,
        unrelated_open_orders=[], bot_owned_open_orders=[], unresolved_executions=[],
        positions={"ETHUSDT": {"size": "0"}},
    )
    diagnosis = SimpleNamespace(
        blockers=[], record=record, proposed_state=DemoExecutionState.DEMO_NOT_SUBMITTED,
        repairable=True, entry_order_history=[], entry_executions=[], remote_open_orders=[],
        repeated_remote_flat=True, durable_events=events,
    )
    return status, diagnosis


def test_only_verified_permission_denial_is_recoverable():
    status, diagnosis = evidence()
    assert blockers_for_denied_submission(status, diagnosis, "execution") == []


def test_open_position_or_unresolved_history_refuses_recovery():
    status, diagnosis = evidence()
    status.positions["ETHUSDT"]["size"] = "0.01"
    diagnosis.entry_executions.append({"execId": "fill"})
    assert blockers_for_denied_submission(status, diagnosis, "execution")


def test_wrong_reason_missing_audit_or_newer_execution_refuses_recovery():
    status, diagnosis = evidence()
    status.kill_switch["reasons"] = ["daily loss limit"]
    diagnosis.durable_events.pop()
    status.newest_execution = SimpleNamespace(id="other")
    assert len(blockers_for_denied_submission(status, diagnosis, "execution")) >= 3


def test_ambiguous_activation_and_old_incident_refuse_recovery():
    status, diagnosis = evidence()
    diagnosis.durable_events[0]["occurred_at"] -= timedelta(days=3)
    status.kill_switch["events"].append(dict(status.kill_switch["events"][0]))
    assert blockers_for_denied_submission(status, diagnosis, "execution")
