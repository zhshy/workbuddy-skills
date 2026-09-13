#!/usr/bin/env python3
"""Build a provenance manifest from destination-profile image declarations."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.profile.read_text(encoding="utf-8"))
    assets = []
    cover = data.get("cover", {})
    cover_file = cover.get("image")
    if cover_file:
        derived = None
        derived_from = str(cover.get("derived_from", "")).strip()
        if derived_from:
            derived = next((image for place in data.get("places", []) for image in place.get("images", []) if isinstance(image, dict) and image.get("file") == derived_from), None)
        provenance = cover if cover.get("source_page") else (derived or cover)
        assets.append({
            "file": cover_file,
            "place_id": "__cover__",
            "venue": data.get("display_name"),
            "module": "cover",
            "role": "hero",
            "source_type": provenance.get("source_type"),
            "media_class": provenance.get("media_class"),
            "original_media_class": provenance.get("original_media_class", provenance.get("media_class")),
            "visual_subject_type": provenance.get("visual_subject_type", "landscape"),
            "source_page": provenance.get("source_page"),
            "download_url": provenance.get("download_url"),
            "transcoded_from": provenance.get("transcoded_from"),
            "verification_evidence": provenance.get("verification_evidence"),
            "retrieved_at": provenance.get("retrieved_at", date.today().isoformat()),
            "http_accessible": bool(provenance.get("http_accessible", False)),
            "decoded": False,
            "source_identity_bound": bool(provenance.get("source_identity_bound", False)),
            "visually_confirmed": bool(provenance.get("visually_confirmed", False)),
            "watermark_checked": bool(provenance.get("watermark_checked", False)),
            "visual_confirmation_note": provenance.get("visual_confirmation_note"),
            "subject_verified": bool(provenance.get("subject_verified", False)),
        })
    for place in data.get("places", []):
        for image in place.get("images", []):
            if not isinstance(image, dict):
                continue
            assets.append({
                "file": image.get("file"),
                "place_id": place.get("id"),
                "venue": place.get("display_name"),
                "module": image.get("module", place.get("type")),
                "role": image.get("role", "gallery"),
                "source_type": image.get("source_type"),
                "media_class": image.get("media_class"),
                "original_media_class": image.get("original_media_class", image.get("media_class")),
                "visual_subject_type": image.get("visual_subject_type"),
                "source_page": image.get("source_page"),
                "download_url": image.get("download_url"),
                "transcoded_from": image.get("transcoded_from"),
                "verification_evidence": image.get("verification_evidence"),
                "retrieved_at": image.get("retrieved_at", date.today().isoformat()),
                "http_accessible": bool(image.get("http_accessible", False)),
                "decoded": False,
                "source_identity_bound": bool(image.get("source_identity_bound", False)),
                "visually_confirmed": bool(image.get("visually_confirmed", False)),
                "watermark_checked": bool(image.get("watermark_checked", False)),
                "visual_confirmation_note": image.get("visual_confirmation_note"),
                "subject_verified": bool(image.get("subject_verified", False)),
            })
    manifest = {
        "destination": data.get("destination"),
        "retrieved_at": date.today().isoformat(),
        "assets": assets,
    }
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS wrote {len(assets)} asset records; visual confirmation remains a separate required step")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
