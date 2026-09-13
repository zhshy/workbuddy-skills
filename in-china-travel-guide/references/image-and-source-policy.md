# Image and Source Policy

This document defines where and how to obtain images and source references for venues, attractions, and dining.

---

## Region-Based Sourcing

All research must respect the `region` flag set at the start of the build.

### Domestic (境内)

| Content Type | Preferred Source | Fallback |
|--------------|------------------|----------|
| Attraction photos | Official WeChat article images | Baidu Maps POI image |
| Restaurant/food photos | WeChat Official Account posts | Baidu Maps POI image |
| Map location | Baidu Maps static image or embed link | - |
| Opening hours / tickets | WeChat Official Account or Baidu Maps info | Local travel blogs |

### International (境外)

| Content Type | Preferred Source | Fallback |
|--------------|------------------|----------|
| Attraction photos | Official website gallery | Google Maps images |
| Restaurant/food photos | Official website or Google Maps | TripAdvisor |
| Map location | Google Maps static image or embed link | - |
| Opening hours / tickets | Official website | Google Maps |

---

## Photo Requirements

- Each place card MUST include a photo or location image.
- Photos must be **precise to the venue** — generic city skyline photos are NOT acceptable.
- If no official photo is available, use a map screenshot showing the exact location with a marker.

### Photo Credit
- When possible, note the source: `"Photo: WeChat Official Account of [Venue]"` or `"Photo: Official Website"`.

---

## Image Acquisition Steps (per venue)

1. **Search for official channels**:
   - Domestic: search WeChat for the venue name, look for Official Account posts with photos.
   - International: visit the official website gallery or press/media page.
2. **If no official photo found**, use the map service (Baidu/Google) to capture a street view or POI image.
3. **Last resort**: use a creative-commons licensed photo from a reliable travel site (with attribution).

---

## Map Link Format

- Domestic: `https://api.map.baidu.com/staticimage?center={lat},{lng}&width=...`
  - Or simply provide a link to the Baidu Maps search result: `https://j.map.baidu.com/xxxx`
- International: `https://www.google.com/maps/place/{venue_name}`

---

## Rating Sources

| Region | Primary Rating | Secondary Rating |
|--------|---------------|------------------|
| Domestic | Dianping (大众点评) score | - |
| International | Google Maps rating | TripAdvisor (if more relevant) |

When displaying ratings, always label the source clearly (e.g., "大众点评：4.5/5" or "Google：4.6/5").

---

## Exclusions

- Do NOT use images from Wikipedia unless explicitly allowed.
- Do NOT use generic stock photos.
- Do NOT use images that are clearly of a different venue.
