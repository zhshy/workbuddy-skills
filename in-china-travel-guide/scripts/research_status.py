#!/usr/bin/env python3
"""Report a small next batch from a travel-guide research plan."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PHASES = (
    ("framing",),
    ("places-core", "places-shopping"),
    ("places-experiences", "places-food"),
    ("itinerary",),
    ("modules-discovery", "modules-practical"),
    ("modules-language-notes",),
)


def select_phase_batch(pending: list[dict], size: int) -> tuple[int, list[dict]]:
    pending_by_id = {str(item.get("id")): item for item in pending}
    for phase_no, phase_ids in enumerate(PHASES, 1):
        selected = [pending_by_id[item_id] for item_id in phase_ids if item_id in pending_by_id]
        if selected:
            return phase_no, selected[:size]
    return len(PHASES), pending[:size]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbench", type=Path)
    parser.add_argument("--batch-size", type=int)
    args = parser.parse_args()
    root = args.workbench.resolve()
    plan_path = root / "research-plan.json"
    if not plan_path.is_file():
        raise SystemExit("research-plan.json missing; run init_research_workspace.py")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    pending = []
    complete = 0
    for pack in plan.get("packs", []):
        path = root / pack["file"]
        valid_json = False
        if path.is_file():
            try:
                checker = Path(__file__).with_name("validate_research_pack.py")
                error_file = root / ".contract-errors" / f"{pack['id']}.json"
                checked = subprocess.run([sys.executable, str(checker), pack["id"], str(path), "--repair-safe", "--errors", str(error_file)], capture_output=True)
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
                valid_json = checked.returncode == 0 and not (isinstance(payload, dict) and payload.get("_draft") is True)
            except (OSError, json.JSONDecodeError):
                valid_json = False
        if valid_json:
            pack["status"] = "complete"
            complete += 1
        else:
            pack["status"] = "pending"
            pending.append(pack)
    plan["status"] = "ready_for_contract_check" if not pending else "in_progress"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    total = len(plan.get("packs", []))
    print(f"RESEARCH FILES {complete}/{total} present")
    if not pending:
        compiler = Path(__file__).with_name("compile_destination_profile.py")
        result = subprocess.run([sys.executable, str(compiler), str(root)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        output = ((result.stdout or "") + (result.stderr or "")).strip()
        if result.returncode:
            plan["status"] = "contract_invalid"
            plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print("RESEARCH CONTRACT INVALID — files exist but required fields are incomplete")
            if output:
                print(output)
            print("CONTINUE: fix the named source packs, then rerun research_status.py")
            return 2
        plan["status"] = "complete"
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"RESEARCH {complete}/{total} contract-complete")
        if output:
            print(output)
        return 0
    size = max(1, args.batch_size or int(plan.get("batch_size", 2)))
    phase_no, batch = select_phase_batch(pending, size)
    print(f"NEXT BATCH — PHASE {phase_no}/{len(PHASES)}")
    for item in batch:
        task_file = root / item.get("task_file", "")
        print(f"- {item['id']}: {item['purpose']} -> {root / item['file']}")
        if task_file.is_file():
            print(f"  task spec: {task_file}")
        checker = Path(__file__).with_name("validate_research_pack.py")
        print(f"  validate immediately: {sys.executable} {checker} {item['id']} {root / item['file']}")
    print("CONTINUE: finish and validate only this bounded batch, persist failures, then rerun research_status.py")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
