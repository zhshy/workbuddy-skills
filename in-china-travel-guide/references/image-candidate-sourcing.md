# Image candidate sourcing

Use this reference when collecting new exact-place images. Discovery and visual verification are separate stages.

## Source ladder

For public landmarks, resolve an exact entity and coordinates first. Prefer destination-government or official open-data media, then an exact official detail page, Wikidata P18, Wikimedia Commons geosearch within 300–500 metres, Openverse exact match, and finally a manual exact-place source. A city or national tourism API is preferred when it supplies stable media URLs and usable terms; it is destination-specific, not a universal dependency.

For restaurants, shops, hotels and other commercial venues, prefer an exact official detail page with `image` JSON-LD or `og:image`, then the venue's official social/property page, then a reputable exact-property listing or an available credentialed place service resolved by stable place ID. Category-labelled venue photos such as food, storefront, exterior or interior are preferable to untyped keyword results. Use coordinate-aware Commons/Openverse only when the entity and city still match; Commons is not the default commercial-place source. Exact Google Maps photography or exact-pin Street View is the final manual fallback. Label Street View as a location reference. Google restaurant ratings remain the only Standard-mode rating source; do not query extra rating platforms merely because images are missing.

Google Places photo resource names may expire and its terms constrain persistent caching, so do not make it the default local static-asset source. Foursquare or Mapillary may be used when credentials and usage terms permit; absence of credentials is a normal fallback condition. Unsplash is suitable for a destination cover or generic editorial mood, never as proof of a named venue.

## Cheap rejection before visual review

- Official sources must be exact detail pages. Reject search, list and home pages and URLs or filenames containing `logo`, `default`, `share`, `sns`, `banner`, `favicon` or equivalent generic markers.
- Wikidata requires the intended entity, destination/country context and a plausible entity type before accepting its P18 image as a candidate.
- Openverse titles, creator metadata and source pages must retain meaningful venue-name or destination overlap. Reject portraits, celebrity appearances and event coverage for a building or shop unless the requested subject is that event.
- Reject tiny files, non-image responses, implausible aspect ratios, watermarked previews and byte-identical duplicates before contact-sheet review.
- Reject candidates outside the resolved country or beyond the configured radius unless the source is the exact official entity page.
- Reject category conflicts before download: portraits/events/logos/menus cannot satisfy a venue exterior slot; generic city panoramas cannot satisfy a named restaurant; a nearby building cannot satisfy the requested branch.

These checks reduce noise but do not prove identity. Every automatic row remains `status: candidate`, `subject_verified: false`, and `visually_confirmed: false`.

## Bounded batch workflow

1. Write one compact request per place with stable ID, exact local/English name, city, country, place kind, known official URL and, when known, Wikidata ID plus latitude/longitude. Resolve the entity once; do not repeat it in every source query.
2. Run `scripts/research_image_candidates.py`. It caches results by normalized request, uses one host-aware bounded retry and stores full metadata without printing it.
3. Rank by exact entity, official binding, coordinate distance, destination/name overlap and category compatibility. Keep two candidates per image slot by default; request a wider shortlist only for failed slots.
4. Download only the shortlist and create one contact sheet for the batch. Save full metadata to JSON; print only counts and failing IDs to the terminal.
5. Promote a candidate only after the contact-sheet row or focused full-size view confirms the exact subject. Record the canonical entity/place ID, coordinates where available, source page, direct image URL, licence/attribution, byte hash and visible identity evidence.

Treat official-page JSON-LD images as normal-risk candidates and every `og:image` as high-risk because it may be a logo, poster or sharing card. An OG candidate may support feasibility but never bypasses later visual review; prefer a clear official body/JSON-LD photo when both exist.

Inspect at most three source families for one commercial venue. If none yields an identity-bound usable image, mark that candidate `replace` in `.research-state/candidate-ledger.json` and choose one replacement from the existing shortlist. Do not use a generic category image and do not begin a fresh broad venue search loop.

Do not insert fixed per-image sleeps. Use the helper's small retry only after an actual transient failure, stop a throttled host, and reuse its cache. When an exact commercial official candidate is found, stop the open-media ladder for that venue; do not continue through Wikimedia merely to collect alternatives.

Use API-provided Wikimedia thumbnail URLs (normally 1200–1600 px), not handcrafted original-file redirects. This reduces large transfers and Wikimedia rate-limit retries. An embedding model may rank an already bounded shortlist, but similarity is never identity proof.

Persistent commercial-photo caching is allowed only when that provider's current terms permit the intended local/static export. A credential or a successful response does not grant redistribution rights.

When the bounded shortlist fails, change tier or replace the recommendation. Do not expand into an unbounded search and do not reuse an unrelated image.
