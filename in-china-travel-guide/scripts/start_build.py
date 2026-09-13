#!/usr/bin/env python3
"""Create a resumable travel-handbook build state."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _build_state import DECISIONS_NAME, STATE_NAME, now, print_state, save
from runtime_preflight import ensure_runtime

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    skill_root = ensure_runtime()
    parser = argparse.ArgumentParser()
    parser.add_argument("workbench", type=Path)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--country", default="")
    parser.add_argument("--start-date", default="pending")
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--budget-level", default="")
    parser.add_argument("--budget-total", default="")
    parser.add_argument("--local-daily-budget", default="", help="local daily budget per traveler")
    parser.add_argument("--force-new-workbench", action="store_true", help="explicitly allow a second active workbench for the same trip")
    args = parser.parse_args()
    root = args.workbench.resolve()
    state_path = root / STATE_NAME
    if state_path.exists():
        raise SystemExit(f"build state already exists: {state_path}; use advance_build.py")
    if not args.force_new_workbench and root.parent.is_dir():
        matches = []
        for candidate in root.parent.glob(f"*/{STATE_NAME}"):
            try:
                prior = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            prior_start = str(prior.get("start_date", "pending") or "pending")
            requested_start = str(args.start_date or "pending")
            requested_compact = requested_start.replace("-", "")
            dates_compatible = prior_start == requested_start or requested_start == "pending"
            if prior_start == "pending" and requested_start != "pending":
                dates_compatible = requested_compact in candidate.parent.name.replace("-", "")
            if (
                prior.get("destination") == args.destination.strip()
                and dates_compatible
                and int(prior.get("days", 0) or 0) == args.days
                and prior.get("handoff_allowed") is not True
            ):
                matches.append(candidate.parent.resolve())
        if matches:
            existing = max(matches, key=lambda item: (item / STATE_NAME).stat().st_mtime)
            raise SystemExit(
                "ACTIVE BUILD EXISTS — resume it instead of creating retry/V2/V3 directories.\n"
                f"ACTIVE_WORKBENCH: {existing}\n"
                f'NEXT_COMMAND: "{sys.executable}" "{Path(__file__).resolve().parent / "advance_build.py"}" "{existing}" --run\n'
                "Use --force-new-workbench only when the user explicitly requested an independent rebuild."
            )
    if args.days < 1:
        raise SystemExit("--days must be positive")
    decisions = {
        "schema_version": 1,
        "flight": {"status": "pending"},
        "stay": {"status": "pending"},
        "budget_plan": {
            "level": args.budget_level,
            "total_trip": args.budget_total,
            "local_per_person_day": args.local_daily_budget,
        },
        "updated_at": now(),
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / DECISIONS_NAME).write_text(json.dumps(decisions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    state = {
        "schema_version": 2,
        "destination": args.destination.strip(),
        "country": args.country.strip(),
        "start_date": args.start_date,
        "days": args.days,
        "status": "in_progress",
        "flight_decision": "pending",
        "stay_decision": "pending",
        "stage": "research_required",
        "next_required_action": f"Run init_research_workspace.py {root} --destination {args.destination!r} --country {args.country or '<country>'} --start-date {args.start_date} --days {args.days}, then follow research_status.py in bounded batches.",
        "handoff_allowed": False,
        "final_response_allowed": False,
        "continuation_required": True,
        "user_input_required": False,
        "active_workbench": str(root),
        "skill_root": str(skill_root),
        "checks": {},
        "evidence": {},
        "created_at": now(),
        "updated_at": now(),
    }
    save(root, state)
    print_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
