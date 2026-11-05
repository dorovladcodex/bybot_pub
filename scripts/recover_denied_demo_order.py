"""Recover one verified, permission-denied Demo submission; dry run by default."""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import socket
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.bybit.demo_diagnostics import DemoDiagnosticsConfig, run_demo_diagnostics
from app.bybit.demo_execution_recovery import diagnose_demo_execution
from app.db.persistence import PersistenceRepository
from app.models import DemoExecutionState


def blockers_for_denied_submission(status, diagnosis, execution_id: str) -> list[str]:
    """Require fresh independent exchange evidence and an exact incident audit."""
    blockers = list(status.failures) + list(diagnosis.blockers)
    record = diagnosis.record
    if not status.kill_switch.get("active"):
        blockers.append("kill switch is not active")
    if status.kill_switch.get("reasons") != ["entry submission outcome is uncertain"]:
        blockers.append("kill-switch reasons do not match this incident")
    if not status.latest_execution or str(status.latest_execution.id) != execution_id:
        blockers.append("execution is not the selected latest incident")
    if not status.newest_execution or str(status.newest_execution.id) != execution_id:
        blockers.append("a newer execution exists")
    if str(record.id) != execution_id or record.state != DemoExecutionState.DEMO_NOT_SUBMITTED:
        blockers.append("execution is not finalized as not submitted")
    if record.order_id or record.accepted_quantity != 0 or record.fills:
        blockers.append("execution contains an exchange order or fill")
    if record.cleanup_result != "remote position flat and bot-owned orders zero":
        blockers.append("flat-state repair audit is missing")
    if diagnosis.proposed_state != DemoExecutionState.DEMO_NOT_SUBMITTED or not diagnosis.repairable:
        blockers.append("fresh exchange verification does not confirm no order")
    if diagnosis.entry_order_history or diagnosis.entry_executions or diagnosis.remote_open_orders:
        blockers.append("order, fill, or open order found")
    if not diagnosis.repeated_remote_flat:
        blockers.append("repeated flat position checks failed")
    if status.unrelated_open_orders or status.bot_owned_open_orders or status.unresolved_executions:
        blockers.append("open orders or unresolved executions exist")
    if any(float(position.get("size") or 0) != 0 for position in status.positions.values()):
        blockers.append("an exchange position is open")
    events = diagnosis.durable_events
    denied = [e for e in events if e.get("event_type") == "CREATE_UNCERTAIN"
              and "permission denied" in str(e.get("last_error") or "").lower()]
    audit = {str(e.get("event_type") or "") for e in events}
    if len(denied) != 1 or not {"READ_ONLY_RECONCILIATION_COMPLETED", "EXECUTION_REPAIR_APPLIED", "FINAL_REMOTE_STATE_FLAT"}.issubset(audit):
        blockers.append("permission denial or completed repair audit is missing")
    activations = [e for e in status.kill_switch.get("events", [])
                   if e.get("event_type") == "KILL_SWITCH_ACTIVATED" and e.get("active")]
    if len(activations) != 1 or not denied:
        blockers.append("incident activation is ambiguous")
    else:
        activation = activations[0]
        if activation.get("execution_id") not in (None, "", execution_id):
            blockers.append("activation belongs to a different execution")
        try:
            def as_time(value):
                return value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            incident_time = as_time(denied[0]["occurred_at"])
            activation_time = as_time(activation["created_at"])
            age = datetime.now(timezone.utc) - incident_time
            if abs((activation_time - incident_time).total_seconds()) > 30 or not timedelta(seconds=30) <= age <= timedelta(hours=24):
                blockers.append("incident timing cannot be verified")
        except (KeyError, TypeError, ValueError):
            blockers.append("incident timing is unavailable")
    return list(dict.fromkeys(blockers))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--confirm-reset", action="store_true")
    args = parser.parse_args()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(1)
            if probe.connect_ex(("127.0.0.1", 8011)) == 0:
                print("RECOVERY REFUSED: stop the Demo server on port 8011 first")
                return 1
        config = DemoDiagnosticsConfig.load()
        repository = PersistenceRepository(config.database_url, create_schema=False)
        def verify():
            return blockers_for_denied_submission(
                run_demo_diagnostics(config, repository=repository),
                diagnose_demo_execution(config, args.execution_id, repository=repository),
                args.execution_id,
            )
        blockers = verify()
        if blockers:
            print("RECOVERY REFUSED")
            for blocker in blockers:
                print(f"- {blocker}")
            return 1
        print("EXACT PERMISSION-DENIED INCIDENT AND FLAT DEMO ACCOUNT: PASS")
        if not args.confirm_reset:
            print("KILL SWITCH RESET: DRY RUN")
            return 0
        if not repository.link_demo_kill_switch_execution(
            args.execution_id, reason="verified denied submission; fresh Demo history and flat account"
        ):
            raise RuntimeError("failed to append incident link")
        blockers = verify()
        if blockers:
            print("RECOVERY REFUSED AFTER RECHECK")
            for blocker in blockers:
                print(f"- {blocker}")
            return 1
        if not repository.reset_demo_kill_switch(
            args.execution_id, reason="verified permission-denied submission; no Demo order or position"
        ):
            raise RuntimeError("failed to reset Demo kill switch")
        print("KILL SWITCH RESET: PASS")
        return 0
    except Exception as exc:
        print(f"RECOVERY FAILED: {type(exc).__name__}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
