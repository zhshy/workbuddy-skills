#!/usr/bin/env python3
"""Create a resumable, bounded research workspace for a destination guide."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workbench", type=Path)
    parser.add_argument("--destination")
    parser.add_argument("--display-name")
    parser.add_argument("--country")
    parser.add_argument("--start-date")
    parser.add_argument("--days", type=int)
    parser.add_argument("--travelers", default="2")
    parser.add_argument("--rhythm", default="relaxed")
    args = parser.parse_args()
    root = args.workbench.resolve()
    state_path = root / ".travel-build-state.json"
    state = load_json(state_path) if state_path.is_file() else {}
    destination = args.destination or state.get("destination")
    country = args.country if args.country is not None else state.get("country")
    start_date = args.start_date or state.get("start_date") or "pending"
    days = args.days if args.days is not None else state.get("days")
    if not destination or not country or not isinstance(days, int):
        raise SystemExit("destination, country and days are required either in build state or CLI arguments")
    if args.destination and state.get("destination") and args.destination != state["destination"]:
        raise SystemExit("--destination conflicts with existing build state")
    if args.start_date and state.get("start_date") not in (None, "pending", args.start_date):
        raise SystemExit("--start-date conflicts with existing build state")
    if days < 1:
        raise SystemExit("--days must be positive")
    end_date = "pending"
    if start_date != "pending":
        try:
            end_date = (date.fromisoformat(start_date) + timedelta(days=days - 1)).isoformat()
        except ValueError as exc:
            raise SystemExit(f"start date must be YYYY-MM-DD or pending: {exc}")
    research = root / "research"
    plan_path = root / "research-plan.json"
    if plan_path.exists():
        raise SystemExit(f"research workspace already exists: {plan_path}")

    n = max(4, days)
    sight_floor = max(8, days)
    souvenir_floor = 1
    brief = {
        "destination": destination,
        "display_name": args.display_name or destination,
        "country": country,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "travelers": args.travelers,
        "rhythm": args.rhythm,
        "defaults_authorized": True,
    }
    write_json(root / "travel-brief.json", brief)

    packs: list[dict] = [
        {"id": "framing", "file": "research/framing.json", "purpose": "封面、交通、住宿与行程分段"},
        {"id": "places-core", "file": "research/places/core.json", "purpose": f"{sight_floor}+ 景点及机场、车站、酒店等支持节点"},
        {"id": "places-shopping", "file": "research/places/shopping.json", "purpose": f"店铺与伴手礼；默认只为最终视觉短名单配置图片"},
        {"id": "places-experiences", "file": "research/places/experiences.json", "purpose": "优先 6 个主流体验（3 类×2）；仅在一整类无法通过限次的真实性、坐标和图片校验时降为 2 类×2"},
        {"id": "places-food", "file": "research/places/restaurants.json", "purpose": "专程餐厅与本地稳定连锁兜底；每家保留一张可核对门店图"},
        {"id": "itinerary", "file": "research/itinerary.json", "purpose": f"从已冻结的合格地点中编排全部 {days} 天时段、停留、路线与 Trip Mode 建议"},
        {"id": "modules-discovery", "file": "research/modules/discovery.json", "purpose": "购物与体验分组和行程关联"},
        {"id": "modules-practical", "file": "research/modules/practical.json", "purpose": "餐饮菜单与出发前准备"},
        {"id": "modules-language-notes", "file": "research/modules/language-notes.json", "purpose": "当地语言、英语备用及天气/礼仪/交通/安全/支付贴士"},
    ]
    plan = {
        "schema_version": 1,
        "destination": destination,
        "days": days,
        "batch_size": 2,
        "status": "in_progress",
        "packs": [{**item, "status": "pending"} for item in packs],
        "rules": [
            "每个地点必须来自目标目的地研究，不得复制参考目的地记录。",
            "每张地点图片必须声明本地文件、来源页、来源类型和检索日期。",
            "只完成当前最多两个相互独立的 pack，每个立即校验；单包重复失败时改用 --batch-size 1。",
        ],
    }
    write_json(plan_path, plan)
    write_json(root / ".research-state" / "candidate-ledger.json", {
        "schema_version": 1,
        "destination": destination,
        "current_pack": "framing",
        "candidates": {},
        "source_incidents": [],
        "note": "Keep only compact keep/replace/pending decisions, attempted source families and rate-limit incidents. Do not store prose research here.",
    })
    research.mkdir(parents=True, exist_ok=True)
    source_map = {
        "framing": ["user-supplied booking evidence", "official source for a supplied transport or property identity"],
        "itinerary": ["official tourism board", "Google Maps routing", "operator timetable"],
        "places": ["official venue page", "Google Maps for identity and directions", "official social account"],
        "module": ["verified place records from this research workspace", "official destination guidance"],
    }
    contract_path = Path(__file__).resolve().parent.parent / "assets" / "research-pack-contract.json"
    contract = load_json(contract_path)
    for item in plan["packs"]:
        family = "itinerary" if item["id"] == "itinerary" else "places" if item["id"].startswith("places-") else "module" if item["id"].startswith("modules-") else "framing"
        required = {
            "framing": contract["packs"]["framing"]["required_paths"],
            "itinerary": contract["packs"]["itinerary"]["item_required_paths"],
            "places": ["stable id", "type", "display_name", "map_query", "source_url", "description/why worth visiting", "type-specific fields exactly as listed by this task", "image declarations only at the count stated by this task; every declaration names file, direct download_url unless an existing local file decodes, source_page, media_class/original_media_class, verification_evidence path and identity-specific visual_confirmation_note; visual flags begin false and watermark_checked becomes true only after full-size inspection"],
            "module": ["canonical group objects", "wrapped {place_id: stable-id} references or complete practical entries", "destination-specific copy", "use references/research-data-shapes.md"],
        }[family]
        exact_requirements = {
            "framing": contract["packs"]["framing"]["required_paths"],
            "places-core": [f"object with sights ({sight_floor}+) and support arrays", "sights need id/type/display_name/map_query/source_url, useful description and hours/closures/duration; when Google is accessible, look up every sight once for score and review count, retaining a verified score even when count is absent", "ordinary sights declare exactly 1 image; only gallery_featured sights declare 2", "support contains itinerary-only transport nodes and a user-supplied stay when available"],
            "places-shopping": [f"object with shops and souvenirs arrays", "records need stable IDs, destination-specific buying value and source", "only the final traveler-facing visual shortlist declares one exact image per item; do not create galleries"],
            "places-shops": ["destination-scaled shop records", "id/type/display_name/map_query/source_url", "description/hours/closed_days", "category/buying_tip/brand_highlights/scheduled_label", "1+ exact-place image declaration; no souvenir-only fields"],
            "places-souvenirs": ["destination-scaled unique souvenir records", "id/type/display_name/map_query/source_url", "concise specific description", "why_buy/best_for/where_to_buy/buying_tip", "1+ exact product image declaration; no shop category/brand fields"],
            "places-experiences": ["Standard target: exactly 6 experience records across 3 controlled experience_type categories, 2 records per category", "Constrained fallback: exactly 4 records across 2 categories, 2 per category, only after the third category fails its bounded identity/coordinate/image ladder; record the failure in .research-state/candidate-ledger.json", "id/type/display_name/map_query/source_url", "description >=60 chars", "hours/closed_days/experience_type/category/scheduled_label", "hazardous boolean; risk_assessment >=45 chars only when true", "1+ exact-place image declaration"],
            "places-food": ["dedicated restaurant and dependable local-chain fallback inventory; delivery and hotel-proximity groups are omitted", "id/type/local_name/english_name/display_name/map_query/source_url", "description >=45 chars explaining why worth visiting", "hours/closed_days/cuisine/signature_dishes as researched display copy naming 2+ specific dishes/price_per_person", "when Google is accessible, look up every restaurant once and attempt both score and review count; retain a verified score when count is absent", "only two different venue access failures may establish that Google is unavailable for the run; never use stop-loss to sample only part of an accessible inventory", "do not retry one venue with alternate languages, keyword variants, mirrors or network workarounds", "a batch with zero ratings is complete only when Google is unavailable or no queried venue exposes a reliable score", "each final restaurant declares one exact-venue image from the bounded entity/coordinates/official/listing ladder; replace a venue when no usable image is available", "use references/research-data-shapes.md for exact containers"],
            "places-support": ["all itinerary-only airport/station/transport nodes with stable id/type/display_name/map_query/source_url; transport nodes do not require images", "confirmed hotel records require hours/closed_days and 2 image declarations; do not invent a hotel or hotel images when stay status is pending"],
            "modules-discovery": ["object with shopping and experiences module payloads", "all items use wrapped {place_id: stable-id} references", "use experience_mode=standard for 3 groups×2; use experience_mode=constrained for 2 groups×2 only when the candidate ledger records why a third qualified type was unavailable"],
            "modules-practical": ["object with food and preparation payloads", "food has a destination-authored menu_primer, exactly 4 local_snacks, 6+ dedicated_trip restaurants across 4+ cuisine/scene labels, and 2-4 reliable_chains that are established local chains suitable as low-effort fallbacks; delivery and near_stay are omitted", "for trips of 3+ days, at least 3 dedicated_trip restaurant place_ids must also appear in itinerary stops; choose branches compatible with that day's route and opening hours", f"preparation essentials and confirm_ahead total {max(24, days * 3)}+ practical items"],
            "modules-language-notes": ["object with language and travel_notes payloads", "local language and reusable English fallback each retain five keyword and five phrase groups", "all group titles are Chinese; English/destination-language text appears inside cards with Chinese meanings", "travel_notes contains exactly five default categories: climate, etiquette/culture, transport, safety, payment; each has four titled practical topics"],
        }
        if item["id"] == "itinerary":
            required = [f"JSON array with exactly {days} day objects", *contract["packs"]["itinerary"]["item_required_paths"], "2+ stops (3+ on non-arrival/departure days)", "each stop has place_id/arrival_time/dwell_minutes/transport_mode/transfer_minutes/distance_km/estimated_cost"]
        else:
            required = exact_requirements.get(item["id"], required)
        query_topics = {
            "framing": ["official travel guide", "airport transport", "where to stay"],
            "places-core": ["top attractions official", "attractions Google Maps", "airport station official"],
            "places-shopping": ["best shopping streets markets", "local souvenirs what to buy", "shopping Google Maps"],
            "places-experiences": ["signature local experiences", "cultural activities official", "experiences Google Maps"],
            "places-food": ["best restaurants Google Maps", "destination cuisine types", "dependable local restaurant chains exact branches"],
            "places-support": ["airport station official", "public transport official", "visitor information"],
            "modules-discovery": ["shopping guide itinerary areas", "local experience categories"],
            "modules-practical": ["menu terms dining etiquette", "entry requirements packing payment transport"],
            "modules-language-notes": ["travel phrases pronunciation", "travel safety etiquette local rules"],
        }
        topics = query_topics.get(item["id"], ["daily itinerary route"] if family == "itinerary" else [item["purpose"]])
        task = {
            "task_id": item["id"],
            "target_file": item["file"],
            "purpose": item["purpose"],
            "required_fields": required,
            "suggested_sources": source_map[family],
            "search_queries": [f"{destination} {topic}" for topic in topics],
            "contract_schema": "assets/research-pack-contract.json",
            "neutral_json_example": contract["packs"][item["id"]].get("example") if item["id"] == "framing" else contract["packs"]["itinerary"].get("example_item") if item["id"] == "itinerary" else None,
            "completion_rule": "Save researched JSON to target_file. Completion means this exact required_fields list is satisfied; file existence alone is not completion. Before closing an image-bearing pack, each declaration must either point to a local file that already decodes or pass direct URL, image MIME and minimum-dimension probing; source-page or guessed filename alone is incomplete. Image file may omit download_url only when that local file already exists and decodes.",
            "execution_rule": "Work only within the current bounded batch. For named venues, perform cheap identity, coordinate and image URL/MIME/dimension feasibility before freezing the place. Do not download final assets yet. Write and validate this pack before expanding scope. Generated requirements and named JSON-pointer errors are sufficient; do not read validator source unless an error remains unexplained.",
        }
        if item["id"] == "framing":
            task["writing_rules"] = ["Cover title/title_lines are short editorial phrases and never repeat city, dates, duration or traveler count."]
        elif item["id"] == "itinerary":
            task["writing_rules"] = [
                "Apply references/itinerary-selection-logic.md over the existing candidate pool before writing prose.",
                "Explicit preferences outrank defaults; roughly two thirds of discretionary scheduled stops should match selected interests.",
                "Use one geographic area and one primary anchor per full day, then compatible secondary places, meal/rest time and at most one optional evening extension.",
                "Run one final coherence check for repetition, backtracking, hours, meals/rest and late-to-early transitions; do not launch a new broad search for this check.",
            ]
        elif item["id"] in {"places-experiences", "modules-discovery"}:
            task["writing_rules"] = [
                "At least four of six Standard-mode experiences directly match selected interests.",
                "Every selected experience must explain both why it is distinctive here and why it fits this traveler; reject generic filler.",
                "Do not pad a failed category. After bounded failure, use constrained mode with four strong options and preserve the failure reason in the candidate ledger.",
            ]
        task_path = research / "tasks" / f"{item['id']}.json"
        write_json(task_path, task)
        item["task_file"] = str(task_path.relative_to(root)).replace("\\", "/")
    write_json(plan_path, plan)
    print(f"PASS research workspace created: {plan_path}")
    print(f"CONTINUE: python research_status.py {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
