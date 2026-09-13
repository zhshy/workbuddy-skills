#!/usr/bin/env python3
"""Probe/download declared images concurrently; identity still requires visual QA."""
from __future__ import annotations
import argparse, json, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from PIL import Image

MIN_WIDTH = 480
MIN_HEIGHT = 320
MIN_PAD_SOURCE_EDGE = 320


def contain_on_white(payload, target):
    """Keep usable small images at native size and center them on a white canvas."""
    with Image.open(BytesIO(payload)) as source:
        source.load()
        source_width, source_height = source.size
        if source_width >= MIN_WIDTH and source_height >= MIN_HEIGHT:
            return payload, source_width, source_height, None
        if min(source_width, source_height) < MIN_PAD_SOURCE_EDGE:
            raise ValueError(f"image too small: {source_width}x{source_height}")
        canvas_width = max(MIN_WIDTH, source_width)
        canvas_height = max(MIN_HEIGHT, source_height)
        canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
        prepared = source.convert("RGBA")
        canvas.paste(prepared, ((canvas_width - source_width) // 2, (canvas_height - source_height) // 2), prepared)
        output = BytesIO()
        suffix = target.suffix.lower()
        if suffix == ".png":
            canvas.save(output, format="PNG", optimize=True)
        elif suffix == ".webp":
            canvas.save(output, format="WEBP", quality=82, method=6)
        else:
            canvas.save(output, format="JPEG", quality=82, optimize=True, progressive=True)
        return output.getvalue(), canvas_width, canvas_height, (source_width, source_height)

def fetch(task, retries, overwrite):
    place_id, image, target = task
    url, name = str(image.get("download_url", "")).strip(), str(image.get("file", "")).strip()
    if target.exists() and not overwrite:
        try:
            with Image.open(target) as existing: width, height = existing.size; existing.verify()
            if width >= MIN_WIDTH and height >= MIN_HEIGHT:
                row = {"place_id": place_id, "file": name, "status": "cached", "width": width, "height": height}
                if image.get("padding_mode") == "contain_white_no_upscale":
                    row.update({
                        "padded": True,
                        "padding_mode": "contain_white_no_upscale",
                        "source_width": image.get("source_width"),
                        "source_height": image.get("source_height"),
                    })
                return row, None, False
        except Exception: pass
    if not url:
        msg = f"{place_id} {name}: local file is missing/invalid and no download_url was supplied"
        return {"place_id": place_id, "file": name, "status": "failed", "error": msg}, msg, False
    error = None
    for attempt in range(max(0, retries) + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 travel-handbook-asset-fetcher/3.0"})
            with urllib.request.urlopen(request, timeout=18) as response:
                mime = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
                # Some image CDNs serve valid JPEG/PNG bytes as the generic
                # application/octet-stream type.  Let Pillow be the authority
                # for those generic responses, while still rejecting explicit
                # HTML/JSON/text payloads before they reach disk.
                if not (mime.startswith("image/") or mime in {"", "application/octet-stream"}):
                    raise ValueError(f"not an image response: {mime}")
                payload = response.read(25 * 1024 * 1024 + 1)
            if len(payload) > 25 * 1024 * 1024: raise ValueError("image exceeds 25 MiB limit")
            with Image.open(BytesIO(payload)) as decoded: decoded.verify()
            payload, width, height, padded_source = contain_on_white(payload, target)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(target.suffix + ".part"); temporary.write_bytes(payload); temporary.replace(target)
            update = {"http_accessible": True, "url_checked_at": datetime.now(timezone.utc).isoformat(), "mime_type": mime, "width": width, "height": height}
            row = {"place_id": place_id, "file": name, "status": "ok", "mime_type": mime, "width": width, "height": height}
            if padded_source:
                source_width, source_height = padded_source
                padding = {"padded": True, "padding_mode": "contain_white_no_upscale", "source_width": source_width, "source_height": source_height}
                update.update(padding); row.update(padding)
            image.update(update)
            return row, None, True
        except Exception as exc:
            error = exc
            transient_http = isinstance(exc, urllib.error.HTTPError) and exc.code in {429, 500, 502, 503, 504}
            transient_network = isinstance(exc, (urllib.error.URLError, TimeoutError, ConnectionError, OSError))
            if (transient_http or transient_network) and attempt < retries:
                time.sleep(min(4, 2 ** attempt)); continue
            break
    msg = f"{place_id} {url}: {error}"
    return {"place_id": place_id, "file": name, "status": "failed", "error": str(error)}, msg, False

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("profile", type=Path); parser.add_argument("asset_root", type=Path)
    parser.add_argument("--overwrite", action="store_true"); parser.add_argument("--place-id", action="append", default=[])
    parser.add_argument("--retries", type=int, default=2); parser.add_argument("--workers", type=int, default=6); args = parser.parse_args()
    data = json.loads(args.profile.read_text(encoding="utf-8")); selected = set(args.place_id); failures, report, tasks = [], [], []
    for place in data.get("places", []):
        place_id = str(place.get("id", ""))
        if selected and place_id not in selected: continue
        for image in place.get("images", []):
            if not isinstance(image, dict): continue
            name = str(image.get("file", "")).strip()
            if not name: failures.append(f"{place_id}: image declaration needs file"); continue
            tasks.append((place_id, image, args.asset_root / name))
    downloaded = 0
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 12))) as pool:
        for future in as_completed([pool.submit(fetch, task, args.retries, args.overwrite) for task in tasks]):
            row, failure, did_download = future.result(); report.append(row); downloaded += int(did_download)
            if failure: failures.append(failure)
    args.profile.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"); args.asset_root.mkdir(parents=True, exist_ok=True)
    provenance_path = args.asset_root / "RESEARCH_PROVENANCE.json"
    if provenance_path.is_file():
        import hashlib
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        provenance["profile_sha256"] = hashlib.sha256(args.profile.read_bytes()).hexdigest()
        provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # A targeted repair must not erase successful records for every other
    # asset. Merge by file so --place-id behaves like an incremental update.
    report_path = args.asset_root / "asset-fetch-report.json"
    if selected and report_path.is_file():
        try:
            previous = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = []
        merged = {
            str(row.get("file")): row
            for row in previous
            if isinstance(row, dict) and row.get("file")
        }
        merged.update({str(row.get("file")): row for row in report if row.get("file")})
        report = list(merged.values())
    report.sort(key=lambda row: (row.get("place_id", ""), row.get("file", "")))
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"downloaded={downloaded}; workers={max(1, min(args.workers, 12))}; report=asset-fetch-report.json; identity is NOT verified by download success")
    for failure in failures: print("FAIL " + failure)
    return 2 if failures else 0

if __name__ == "__main__": raise SystemExit(main())
