markdown
---
name: in-china-travel-guide
description: |
  This skill generates a personalized, comprehensive HTML travel guide for any destination.
  It automatically detects whether the destination is inside China (domestic) or outside (international),
  and switches data sources accordingly: Baidu Maps + WeChat Official Accounts + Dianping for domestic,
  Google Maps + Official Websites + Google Ratings for international.
  The final output is a beautifully designed single-page HTML with 6 core modules.
---

# Personalized Travel Guide Skill

## Overview

This skill produces a complete travel guide HTML for a given destination, duration, and traveler profile.
It uses a multi-stage research process to collect and synthesize information.

## Core Modules (Final Output)

The final HTML guide contains exactly these **6 sections**:

1. **Itinerary** (行程) — Day-by-day plan with time slots and activities
2. **Attractions** (景点) — Must-see landmarks and hidden gems
3. **Shopping** (购物) — Best shopping areas and souvenirs
4. **Experiences** (体验) — Cultural and unique local experiences
5. **Dining** (餐饮) — Limited to two sub-categories only:
   - Local Snacks / Street Food (当地小吃推荐)
   - Signature Restaurants Worth a Detour (值得专程去)
6. **Local Tips** (当地贴士) — Practical local advice

### Removed Modules (不再包含)
- ~~Language Tips~~ (语言锦囊) — removed
- ~~Preparation~~ (出发前准备) — removed

---

## 0. Destination Region Detection (Auto)

Before starting any research, determine whether the destination is within China (mainland) or outside.

- **Inside China (境内)**: if the destination is a city in China (e.g., Beijing, Shanghai, Chengdu, Xi'an) or the country is explicitly "China".
- **Outside China (境外)**: all other destinations (Tokyo, Paris, New York, etc.).

Store this decision as `region = "domestic"` or `"international"` and use it to select data sources throughout the build.

---

## Data Collection & Research

For every venue or recommendation you research, always check `region` first:

| Data Type | Domestic (境内) | International (境外) |
|-----------|-----------------|----------------------|
| **Location Map** | Baidu Maps link/embed | Google Maps link/embed |
| **Official Info** | WeChat Official Account name | Official website URL |
| **Restaurant Rating** | Dianping (大众点评) score | Google Maps rating |
| **Photos** | Official WeChat articles or Baidu Maps POI | Official website or Google Maps |

### Research Priorities

- **Attractions**: Must include location, opening hours, ticket price (if any), and a brief description.
- **Dining**: ONLY collect local snacks/street food and restaurants worth a detour. Skip fine dining, cafes, bars, and chains.
- **Shopping**: Highlight unique local products and best shopping districts.
- **Experiences**: Cultural activities, classes, workshops, or unique local events.

---

## Build Workflow

1. **Collect user input** — from questionnaire or natural language
2. **Detect region** — set `region = "domestic"` or `"international"`
3. **Research all modules** using appropriate data sources per region
4. **Generate HTML** with 6 modules using the output format template
5. **Present to user** — deliver the final HTML guide

### Region flows through to the rendered page

`region` is not only a research hint. The render pipeline derives it from the profile
(`country`, or the optional `region` field) and stamps it on the page body as
`data-handbook-region="domestic" | "international"`. From there:

- Every static venue card (stays / sights / shops / experiences / food) gets its
  **location link** from `map_url()` in `build_render_bindings.py`, which returns a
  **Baidu Maps** link for domestic and **Google Maps** for international (a place may
  override with its own explicit non-foreign link).
- Trip Mode (`trip-mode.js`) reads the same attribute to pick its default map provider:
  domestic defaults to **百度地图** with **谷歌地图** as the alternate; international
  defaults to **Google** with **Apple Maps** as the alternate. Users can still switch
  within that pair and the choice is remembered per destination.

## Color Scheme

The guide uses a **fixed default color scheme** (blue/teal theme). No user color selection is required.

---

## Important Constraints

- All place cards MUST include a precise location link (Baidu Maps or Google Maps depending on region)
- Restaurant ratings MUST show the correct source label (Dianping for domestic, Google for international)
- For domestic destinations, always attempt to find WeChat Official Accounts for venues
- For international destinations, always attempt to find official websites
- Do NOT include Language Tips or Preparation modules
- Do NOT ask users to select color schemes
