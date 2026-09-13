#!/usr/bin/env python3
"""Run a fast product/runtime smoke test in a clean temporary export."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    source = args.root.resolve()
    if not (source / "index.html").exists():
        print("FAIL missing index.html")
        return 2
    with tempfile.TemporaryDirectory(prefix="travel-handbook-forward-") as tmp:
        install_target = Path(tmp) / "fresh-destination"
        installer = Path(__file__).resolve().parent / "install_ui_system.py"
        installed = subprocess.run(
            [sys.executable, str(installer), str(install_target), "--force-template"],
            capture_output=True,
            text=True,
        )
        if installed.returncode:
            print("FAIL destination-neutral installer failed")
            print((installed.stdout + installed.stderr).strip())
            return 2
        raster_suffixes = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
        copied_rasters = [path for path in install_target.rglob("*") if path.is_file() and path.suffix.lower() in raster_suffixes]
        if copied_rasters:
            print("FAIL destination-neutral installer copied Bali raster media")
            return 2
        if not (install_target / "ADAPTATION_REQUIRED.json").exists():
            print("FAIL installer did not mark the raw canonical copy as unfinished")
            return 2

        # Regression fixture: imitate the exact failure this Skill used to let
        # through—rename only the first cover label while leaving Bali content,
        # routes and broken image references behind. The strict audit must reject it.
        dirty = Path(tmp) / "dirty-example-city"
        shutil.copytree(install_target, dirty)
        html = (dirty / "index.html").read_text(encoding="utf-8")
        adapted = html.replace("BALI", "EXAMPLE CITY", 1).replace("巴厘岛旅行手册", "示例城旅行手册", 1)
        (dirty / "index.html").write_text(adapted, encoding="utf-8")
        profile = {
            "destination": "Example City, Testland",
            "display_name": "示例城",
            "navigation_brand": "EXAMPLE CITY · 2026",
            "year": "2026",
            "aliases": ["Example City", "示例城"],
            "country": "Japan",
            "forbidden_reference_terms": ["Ubud", "Seminyak", "Bali"],
            "places": [{
                "id": "example-central-station",
                "type": "sight",
                "display_name": "博多站",
                "map_query": "Example Central Station",
                "source_url": "https://www.jrkyushu.co.jp/",
            }],
        }
        (dirty / "destination-profile.json").write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
        audit = Path(__file__).resolve().parent / "audit_product.py"
        rejected = subprocess.run(
            [sys.executable, str(audit), str(dirty), "--strict"],
            capture_output=True,
            text=True,
        )
        if rejected.returncode == 0:
            print("FAIL strict audit accepted a partial destination rename with Bali contamination and broken media")
            return 2

        candidate = Path(tmp) / "candidate"
        shutil.copytree(source, candidate)
        adapted = (candidate / "index.html").read_text(encoding="utf-8")
        invariants = (
            'id="contents"', 'id="route"', 'id="sights"', 'id="shops"',
            'id="move"', 'id="food"', 'id="booking"', 'id="words"', 'id="tips"',
            "trip-mode.js", "itinerary-customizer.js", "theme-switcher.js",
            "checklist-memory.js", "movement-section",
            "hotel-chapter-fold",
        )
        product_source = adapted + "\n" + "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in candidate.glob("*.js")
        )
        missing = [token for token in invariants if token not in product_source]
        if missing:
            print("FAIL product invariants lost: " + ", ".join(missing))
            return 2
        import re
        source_inline_styles = [re.sub(r"\r\n?", "\n", block).strip() for block in re.findall(r'<style\b[^>]*>(.*?)</style>', (source / "index.html").read_text(encoding="utf-8"), re.I | re.S)]
        candidate_inline_styles = [re.sub(r"\r\n?", "\n", block).strip() for block in re.findall(r'<style\b[^>]*>(.*?)</style>', adapted, re.I | re.S)]
        if candidate_inline_styles != source_inline_styles:
            print("FAIL canonical inline layout CSS was modified")
            return 2
        def loaded_assets(source_text: str, tag: str, attribute: str) -> list[str]:
            pattern = rf'<{tag}\b[^>]*\b{attribute}=["\']([^"\']+)["\']'
            return [Path(value.split("?", 1)[0]).name for value in re.findall(pattern, source_text, re.I)]

        canonical_text = (source / "index.html").read_text(encoding="utf-8")
        if loaded_assets(adapted, "link", "href") != loaded_assets(canonical_text, "link", "href"):
            print("FAIL canonical stylesheet list/order was modified")
            return 2
        if loaded_assets(adapted, "script", "src") != loaded_assets(canonical_text, "script", "src"):
            print("FAIL canonical script list/order was modified")
            return 2
        node = shutil.which("node")
        if node:
            for filename in ("trip-mode.js", "itinerary-customizer.js", "theme-switcher.js"):
                result = subprocess.run([node, "--check", str(candidate / filename)], capture_output=True, text=True)
                if result.returncode:
                    print(f"FAIL JavaScript syntax {filename}: {result.stderr.strip()}")
                    return 2
        rail = (candidate / "desktop-rail.js").read_text(encoding="utf-8", errors="ignore")
        order = "['route','行程'],['sights','景点指南'],['shops','购物'],['move','当地特色体验'],['food','餐饮指南'],['booking','出发前准备'],['words','语言随行锦囊'],['tips','旅游贴士']"
        if order not in rail:
            print("FAIL canonical chapter order was not retained")
            return 2
        if any(token in rail for token in ("panel.innerHTML", "BALI SOUVENIRS", "Threads of Life", "Bali Pulina")):
            print("FAIL shared navigation runtime still injects destination-specific content")
            return 2
        if "handbookDestination" not in rail:
            print("FAIL desktop navigation brand is not destination-driven")
            return 2
        trip_runtime = (candidate / "trip-mode.js").read_text(encoding="utf-8", errors="ignore")
        if "isHotel(" not in trip_runtime:
            print("FAIL Trip Mode does not suppress lodging-only Xiaohongshu actions")
            return 2
        if "name+' 出片'" in trip_runtime or 'name+" 出片"' in trip_runtime:
            print("FAIL place-card Xiaohongshu queries still append 出片 instead of using the exact place name")
            return 2
        css_source = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in candidate.glob("*.css")
        )
        compact_css = "".join(css_source.split())
        rail_invariants = (
            "--desktop-rail-width:188px",
            "grid-template-columns:30pxminmax(0,1fr)!important",
            "min-height:55px!important",
            "font-size:13px!important",
        )
        missing_rail = [token for token in rail_invariants if token not in compact_css]
        if missing_rail:
            print("FAIL canonical readable desktop-rail geometry was not retained: " + ", ".join(missing_rail))
            return 2
        cover_invariants = (
            "jungle-cover-image", "jungle-cover-shade", "jungle-cover-copy",
            "jungle-cover-kicker", 'class="lede"', "jungle-cover-bottom",
        )
        cover_start = adapted.find('class="hero jungle-cover')
        cover_end = adapted.find("</header>", cover_start) if cover_start >= 0 else -1
        cover_source = adapted[cover_start:cover_end] if cover_end > cover_start >= 0 else ""
        missing_cover = [token for token in cover_invariants if token not in cover_source]
        if missing_cover:
            print("FAIL cover copy and media are not one canonical full-viewport composition: " + ", ".join(missing_cover))
            return 2
        if "adventure-card" in adapted + css_source and "adventure-grid{grid-template-columns:repeat(3" in css_source.replace(" ", ""):
            print("FAIL adventure cards use a three-column parent grid that can collapse copy into vertical text")
            return 2
        print("PASS canonical product invariants retained; raw and partially renamed destination workbenches are correctly blocked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
