#!/usr/bin/env python3
"""Inspect a workbench, persist its stage, and print the next required action."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from _build_state import STATE_NAME, evaluate, load_json, print_state, save
from runtime_preflight import ensure_runtime


def main() -> int:
    skill_root = ensure_runtime()
    parser = argparse.ArgumentParser()
    parser.add_argument("workbench", type=Path)
    parser.add_argument("--run-gates", action="store_true")
    parser.add_argument("--run", action="store_true", help="execute the next deterministic stage, then reevaluate")
    args = parser.parse_args()
    root = args.workbench.resolve()
    persisted = load_json(root / STATE_NAME)
    original_skill_root = str(persisted.get("skill_root", "")).strip()
    if original_skill_root and Path(original_skill_root).resolve() != skill_root:
        raise SystemExit(
            "SKILL ROOT CONFLICT: this build was started by a different skill copy. "
            f"Resume it with scripts from {original_skill_root}; do not mix installed and supplied versions."
        )
    state = evaluate(root, run_gates=args.run_gates)
    if args.run and not state.get("handoff_allowed"):
        scripts = Path(__file__).resolve().parent
        stage = state.get("stage")
        commands: list[list[str]] = []
        if stage == "research_required":
            country = str(persisted.get("country", "")).strip()
            if not country:
                print("OPEN RESEARCH INPUT: country is missing; rerun start_build.py with --country or run init_research_workspace.py explicitly")
            else:
                commands = [
                    [sys.executable, str(scripts / "init_research_workspace.py"), str(root), "--destination", str(persisted["destination"]), "--country", country, "--start-date", str(persisted.get("start_date", "pending")), "--days", str(persisted["days"])],
                    [sys.executable, str(scripts / "seed_deterministic_packs.py"), str(root)],
                ]
        elif stage == "profile_required":
            commands = [[sys.executable, str(scripts / "compile_destination_profile.py"), str(root)]]
        elif stage == "workbench_required":
            commands = [[sys.executable, str(scripts / "install_ui_system.py"), str(root)]]
        elif stage == "render_required":
            profile = root / "destination-profile.json"
            commands = [
                [sys.executable, str(scripts / "preflight_text_width.py"), str(profile)],
                [sys.executable, str(scripts / "plan_incremental_validation.py"), str(root)],
                [sys.executable, str(scripts / "install_ui_system.py"), str(root), "--force-template"],
                [sys.executable, str(scripts / "build_render_bindings.py"), str(profile), str(root / "render-bindings.json")],
                [sys.executable, str(scripts / "render_destination.py"), str(profile), str(root)],
            ]
        elif stage in {"research_in_progress", "profile_invalid", "assets_invalid", "visual_review_required", "automated_gates_required", "browser_qa_required"}:
            print("OPEN WORK REMAINS: execute the bounded correction batch in next_required_action; --run will not fabricate researched facts or QA evidence")
        elif stage == "assets_required":
            commands = [
                [sys.executable, str(scripts / "fetch_declared_assets.py"), str(root / "destination-profile.json"), str(root)],
                [sys.executable, str(scripts / "build_asset_manifest.py"), str(root / "destination-profile.json"), str(root / "asset-manifest.json")],
            ]
        for command in commands:
            result = subprocess.run(command)
            if result.returncode:
                return result.returncode
        if commands:
            state = evaluate(root, run_gates=args.run_gates)
    save(args.workbench, state)
    print_state(state)
    return 0 if state["handoff_allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
