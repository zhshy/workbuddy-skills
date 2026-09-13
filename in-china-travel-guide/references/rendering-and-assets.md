# Rendering and asset workflow

## Official byte-safe renderer

`build_render_bindings.py` is the destination-neutral canonical component generator. It reads the validated profile and emits all 11 registered fragments plus destination runtime bindings. `render_destination.py` is the byte-safe inserter between those bindings and the compressed canonical product. It does not serialize the document. It locates one registered destination-bearing root, replaces only its inner byte range and leaves the outer canonical element intact.

Command:

```text
python scripts/render_destination.py destination-profile.json workbench
```

The profile's `render_bindings_file` points to a JSON file with:

- `html`: selector plus complete canonical inner fragment generated from profile records;
- `runtime_files`: optional full content for the documented destination-bearing runtimes.

Allowed selectors are `.hero`, `.trip-pulse`, `#contents`, `.flight-band`, `#stay`, `#route`, `#sights`, `#shops`, `#move`, `#food`, `#booking`, `#words`, `#tips`, `.mobile-menu-panel` and the unique page-level `body > footer`. Bind every family needed by the product; partial bindings remain an unfinished workbench. Build fragments by cloning the matching canonical component subtree and rendering target records into it. Do not copy reference prose or venue records. The status strip, contents subtitle, mobile-directory identity and footer are destination-bearing surfaces and must be generated from the same profile rather than inherited from Bali.

The renderer rejects duplicate/unregistered selectors, empty fragments, changed locked files and changed inline styles. It writes `RENDER_REPORT.json` and remains safe to rerun against a clean workbench. When replacing already rendered records, reinstall a clean workbench and rerender from the same profile/bindings rather than stacking transformations.

## Contract-compliant generic adapters

If a fragment-production helper is needed, it must be destination-neutral and reusable. It may read profile records and produce binding fragments, but may not hardcode any destination. It must preserve canonical classes, nesting, controls and interaction hooks. Whole-document DOM serialization is prohibited; registered subtree serialization is allowed only when the original inline styles and locked-file hashes are restored and verified.

## Image evidence pipeline

1. Research the exact venue/product and record image declarations in the profile. Resolve assets per place, not as one destination-wide candidate pool.
2. Download locally using available browser/network tools; do not infer identity from filename.
   - When direct image URLs are already declared, `fetch_declared_assets.py profile asset-root` may batch-download them. It never decides identity.
3. Run `build_asset_manifest.py profile output-manifest`.
4. Run `verify_assets.py profile manifest asset-root --machine-only --write` for file, decode, dimension and place-ID preflight. Rendering may proceed after this passes, producing an explicitly non-final `PREVIEW_READY` build.
5. Run `build_asset_contact_sheet.py manifest asset-root contact-sheet.jpg` and inspect every selected image/source label in one batch. Open only flagged, ambiguous, Open Graph, third-party or watermark-risk files individually at full size; an exact official body photo that is clear in a sufficiently large contact-sheet cell does not require a second redundant opening.
6. Only after inspection set `visually_confirmed: true`, `watermark_checked: true` and `subject_verified: true`.
7. Run strict product audit.

Evidence states are independent:

- `http_accessible`: source/file request succeeded;
- `decoded`: local raster decodes and meets minimum size;
- `source_identity_bound`: source page explicitly names the same place ID;
- `visually_confirmed`: Agent inspected the visible subject;
- `watermark_checked`: Agent inspected the full-size image for corner, center and repeated stock watermarks;
- `subject_verified`: all applicable evidence is complete.

No tool may automatically turn file existence into `subject_verified: true`. If the host's image viewer fails, try the contact sheet in its browser once. If both visual surfaces fail, stop visual retries, retain `PREVIEW_READY`, and leave the relevant flags false; do not treat a sandbox defect as a reason to redo research or downloads.

Use a bounded candidate budget. For each required image slot, inspect at most three candidates from the preferred source tier and at most six candidates total. If none passes, switch source tier or replace the venue rather than scanning dozens of weak results. Reject obvious logos, banners, posters, maps, UI screenshots, social cards and known stock-preview hosts before downloading. Never rank approximately 30 candidates for every slot.

## Pending stays

Pending accommodation renders `.hotel-card.stay-pending` with neutral copy and no property image, address, booking link or map link. Confirmed accommodation uses the normal gallery and requires at least two distinct verified exact-property images; use three when reliable assets are readily available. Changing status from pending to confirmed requires rerendering the complete `#stay` family.
