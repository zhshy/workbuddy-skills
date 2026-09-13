#!/usr/bin/env python3
"""Resolve place identity, then collect a cached top-N image shortlist."""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, html, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

UA = "Mozilla/5.0 travel-guide-image-research/2.0"
GENERIC = re.compile(r"(?:logo|default|share|sns|banner|favicon|sprite|portrait|concert|event|celebrity)", re.I)

def fetch(url: str, as_json: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json" if as_json else "text/html"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.load(response) if as_json else response.read(1_500_000).decode("utf-8", "replace")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            if attempt: raise
            time.sleep(1)

def item(source, page, image, title="", score=0, **extra):
    return {"source": source, "source_page": page, "image_url": html.unescape(image), "title": title,
            "candidate_score": score, "status": "candidate", "subject_verified": False,
            "visually_confirmed": False, **extra}

def words(value):
    return {part for part in re.split(r"[^\w\u3400-\u9fff]+", str(value).casefold()) if len(part) > 1}

def rank_score(row, candidate):
    haystack = " ".join(str(candidate.get(k, "")) for k in ("title", "context", "source_page"))
    query = " ".join(str(row.get(k, "")) for k in ("query", "local_name", "english_name", "city", "country"))
    score = int(candidate.get("candidate_score", 0)) + min(24, len(words(haystack) & words(query)) * 4)
    return score - (40 if GENERIC.search(haystack + " " + str(candidate.get("image_url", ""))) else 0)

def official(row):
    page = row.get("official_url")
    if not page: return []
    body, hits = fetch(page), []
    patterns = (
        ("official_og_image", "high", r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)'),
        ("official_og_image", "high", r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']'),
        ("official_jsonld_image", "normal", r'"image"\s*:\s*"(https?://[^"\\]+)'),
    )
    for source, risk, pattern in patterns:
        hits.extend((source, risk, url) for url in re.findall(pattern, body, re.I))
    unique = {}
    for source, risk, url in hits:
        clean = urllib.parse.urljoin(page, url.replace("\\/", "/"))
        if not GENERIC.search(clean): unique.setdefault(clean, (source, risk))
    return [item(source, page, url, row.get("query", ""), 100 if risk == "normal" else 75, entity_bound=True, review_risk=risk)
            for url, (source, risk) in unique.items()][:2]

def claim_coordinates(claims):
    try:
        value = claims["P625"][0]["mainsnak"]["datavalue"]["value"]
        return float(value["latitude"]), float(value["longitude"])
    except (KeyError, IndexError, TypeError, ValueError): return None

def wikidata(row):
    query = " ".join(str(row.get(k, "")) for k in ("query", "city", "country")).strip()
    entity_query = str(row.get("english_name") or row.get("query") or row.get("local_name") or "").strip()
    ids = [row["wikidata_id"]] if row.get("wikidata_id") else []
    params = urllib.parse.urlencode({"action":"wbsearchentities","search":entity_query,"language":"en","format":"json","limit":3})
    ids.extend(hit["id"] for hit in fetch("https://www.wikidata.org/w/api.php?" + params, True).get("search", []) if hit["id"] not in ids)
    result, coords, chosen = [], None, None
    for entity_id in ids[:3]:
        entity = fetch(f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json", True).get("entities", {}).get(entity_id, {})
        claims, labels, descriptions = entity.get("claims", {}), entity.get("labels", {}), entity.get("descriptions", {})
        label = (labels.get("en") or next(iter(labels.values()), {})).get("value", "")
        context = (descriptions.get("en") or next(iter(descriptions.values()), {})).get("value", "")
        # A supplied ID is a hint, not proof. It must still overlap the requested
        # entity/destination so a mistyped QID cannot poison coordinate search.
        if not (words(label + " " + context) & words(query)): continue
        coords, chosen = claim_coordinates(claims) or coords, entity_id
        for claim in claims.get("P18", [])[:2]:
            filename = claim["mainsnak"]["datavalue"]["value"]
            params = urllib.parse.urlencode({"action":"query","titles":f"File:{filename}","prop":"imageinfo","iiprop":"url|mime|extmetadata","iiurlwidth":1600,"format":"json"})
            page = next(iter(fetch("https://commons.wikimedia.org/w/api.php?" + params, True).get("query", {}).get("pages", {}).values()), {})
            info = (page.get("imageinfo") or [{}])[0]; url = info.get("thumburl") or info.get("url")
            if url: result.append(item("wikidata_p18", f"https://www.wikidata.org/wiki/{entity_id}", url, label, 90, entity_id=entity_id, context=context, coordinates=coords, license_metadata=info.get("extmetadata", {}), identity_check_required=True))
        if result: break
    return result, coords, chosen

def commons_geo(row, coords, entity_id):
    if not coords: return []
    radius = max(50, min(int(row.get("radius_m", 400)), 1000))
    params = urllib.parse.urlencode({"action":"query","generator":"geosearch","ggsprimary":"all","ggsnamespace":6,"ggsradius":radius,"ggscoord":f"{coords[0]}|{coords[1]}","ggslimit":8,"prop":"imageinfo|coordinates","iiprop":"url|mime|extmetadata","iiurlwidth":1600,"format":"json"})
    result = []
    for page in fetch("https://commons.wikimedia.org/w/api.php?" + params, True).get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]; url, title = info.get("thumburl") or info.get("url"), page.get("title", "")
        if not url or GENERIC.search(title): continue
        point = (page.get("coordinates") or [{}])[0]
        result.append(item("commons_geosearch", f"https://commons.wikimedia.org/?curid={page.get('pageid')}", url, title, 60, entity_id=entity_id, coordinates=[point.get("lat"), point.get("lon")], radius_m=radius, license_metadata=info.get("extmetadata", {}), identity_check_required=True))
    return result[:4]

def openverse(row):
    query = " ".join(str(row.get(k, "")) for k in ("query", "city", "country")).strip()
    api = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode({"q":query,"page_size":5,"mature":"false"})
    result = []
    for found in fetch(api, True).get("results", []):
        image = found.get("url") or found.get("thumbnail")
        if image and not GENERIC.search((found.get("title") or "") + " " + image):
            result.append(item("openverse", found.get("foreign_landing_url") or found.get("detail_url") or api, image, found.get("title") or "", 20, license=found.get("license"), creator=found.get("creator"), identity_check_required=True))
    return result[:3]

def collect(row, limit):
    candidates, errors, entity_id = [], [], row.get("wikidata_id")
    coords = (float(row["latitude"]), float(row["longitude"])) if row.get("latitude") is not None and row.get("longitude") is not None else None
    for name, resolver in (("official", lambda: official(row)),):
        try: candidates.extend(resolver())
        except Exception as error: errors.append({"source":name,"error":type(error).__name__})
    commercial = str(row.get("kind") or row.get("type") or "").lower() in {"restaurant", "shop", "hotel", "experience", "souvenir"}
    if commercial and candidates:
        ranked = sorted(candidates, key=lambda candidate: rank_score(row, candidate), reverse=True)
        return {**row, "resolved_identity":{"wikidata_id":entity_id,"coordinates":coords}, "candidates":ranked[:limit], "errors":errors, "search_stopped":"exact official candidates found; open-media ladder skipped"}
    try:
        found, resolved, entity_id = wikidata(row); candidates.extend(found); coords = coords or resolved
    except Exception as error: errors.append({"source":"wikidata","error":type(error).__name__})
    fallback_resolvers = (("openverse", lambda: openverse(row)),) if commercial else (("commons_geosearch", lambda: commons_geo(row, coords, entity_id)), ("openverse", lambda: openverse(row)))
    for name, resolver in fallback_resolvers:
        try: candidates.extend(resolver())
        except Exception as error: errors.append({"source":name,"error":type(error).__name__})
    unique = {}
    for candidate in candidates:
        candidate["candidate_score"] = rank_score(row, candidate); key = candidate["image_url"].split("?")[0]
        if key not in unique or candidate["candidate_score"] > unique[key]["candidate_score"]: unique[key] = candidate
    ranked = sorted(unique.values(), key=lambda x: x["candidate_score"], reverse=True)
    return {**row, "resolved_identity":{"wikidata_id":entity_id,"coordinates":coords}, "candidates":ranked[:limit], "errors":errors}

def cache_key(row, limit):
    return hashlib.sha256(json.dumps({"v":3,"row":row,"limit":limit}, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("requests", type=Path); parser.add_argument("output", type=Path)
    parser.add_argument("--workers", type=int, default=3); parser.add_argument("--per-place", type=int, default=2); parser.add_argument("--refresh", action="store_true"); args = parser.parse_args()
    rows = json.loads(args.requests.read_text(encoding="utf-8-sig")); limit = max(1, min(args.per_place, 6))
    if not isinstance(rows, list): raise SystemExit("requests JSON must be a list")
    cache_path = args.output.parent / ".image-candidate-cache.json"
    try: cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else {}
    except (OSError, json.JSONDecodeError): cache = {}
    results, work = [None] * len(rows), []
    for index, row in enumerate(rows):
        key = cache_key(row, limit)
        if not args.refresh and key in cache: results[index] = cache[key]
        else: work.append((index, key, row))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 3))) as pool:
        futures = {pool.submit(collect, row, limit):(index,key) for index,key,row in work}
        for future in concurrent.futures.as_completed(futures):
            index,key = futures[future]; results[index] = cache[key] = future.result()
    final = [row for row in results if row is not None]; args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8"); cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    empty = [str(row.get("id") or row.get("query")) for row in final if not row["candidates"]]
    print(f"IMAGE CANDIDATES: {sum(len(row['candidates']) for row in final)} for {len(final)} places; cached={len(rows)-len(work)}; empty={len(empty)}")
    if empty: print("EMPTY IDS: " + ", ".join(empty))
    return 0

if __name__ == "__main__": sys.exit(main())
