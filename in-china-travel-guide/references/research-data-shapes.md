markdown
# Research Data Shapes

This document defines the exact data structures that the research phase must produce for each module. All research output must conform to these shapes before proceeding to the rendering phase.

---

## Global Context

Every research session includes a global context object:

```json
{
  "destination": "Chengdu",
  "days": 4,
  "travelers": 2,
  "styles": ["culture", "food"],
  "region": "domestic" | "international",
  "preferences": "optional user notes"
}
Region Determination
region = "domestic": Destination is within mainland China.

Maps: Baidu Maps

Official Info: WeChat Official Accounts

Restaurant Ratings: Dianping (大众点评)

Photos: Baidu Maps POI or WeChat articles

region = "international": Destination is outside mainland China.

Maps: Google Maps

Official Info: Official websites

Restaurant Ratings: Google Maps ratings

Photos: Official websites or Google Maps

Module 1: Itinerary (行程)
json
{
  "module": "itinerary",
  "data": {
    "overview": "string — brief summary of the trip",
    "days": [
      {
        "day": 1,
        "date": "optional date string",
        "theme": "string — e.g., 'Historical Sites'",
        "activities": [
          {
            "time": "09:00",
            "activity": "string",
            "location": "string",
            "notes": "optional string"
          }
        ],
        "meals": {
          "breakfast": "string — recommendation or 'included'",
          "lunch": "string — recommendation",
          "dinner": "string — recommendation"
        }
      }
    ],
    "pace_notes": "string — e.g., 'Moderate pace with afternoon breaks'"
  }
}
Module 2: Attractions (景点)
json
{
  "module": "attractions",
  "data": {
    "must_see": [
      {
        "name": "string — attraction name",
        "name_local": "string — local language name",
        "description": "string — brief description",
        "location": {
          "address": "string",
          "map_link": "string — Baidu Maps (domestic) or Google Maps (international) link",
          "coordinates": "optional {lat, lng}"
        },
        "official_info": {
          "type": "wechat" | "website",
          "value": "string — WeChat Official Account name (domestic) or website URL (international)"
        },
        "opening_hours": "string",
        "ticket_price": "string — e.g., '¥60' or 'Free'",
        "best_time_to_visit": "string — e.g., 'Morning'",
        "photo_url": "string — optional",
        "photo_source": "string — e.g., 'Baidu Maps POI' or 'Official Website'"
      }
    ],
    "hidden_gems": [
      {
        "name": "string",
        "description": "string",
        "location": { "address": "string", "map_link": "string" },
        "why_visit": "string — why it's worth visiting"
      }
    ]
  }
}
Module 3: Shopping (购物)
json
{
  "module": "shopping",
  "data": {
    "districts": [
      {
        "name": "string — shopping district name",
        "location": { "address": "string", "map_link": "string" },
        "vibe": "string — e.g., 'Luxury malls', 'Local markets'",
        "best_for": ["string — e.g., 'Clothing', 'Souvenirs'"]
      }
    ],
    "souvenirs": [
      {
        "item": "string — souvenir name",
        "where_to_buy": "string",
        "price_range": "string",
        "cultural_note": "string — optional"
      }
    ]
  }
}
Module 4: Experiences (体验)
json
{
  "module": "experiences",
  "data": {
    "activities": [
      {
        "name": "string — experience name",
        "type": "string — e.g., 'Cooking class', 'Tea ceremony', 'Workshop'",
        "description": "string",
        "location": { "address": "string", "map_link": "string" },
        "duration": "string — e.g., '2 hours'",
        "price": "string — e.g., '¥200/person'",
        "booking_info": "string — how to book",
        "why_unique": "string — what makes this special"
      }
    ]
  }
}
Module 5: Dining (餐饮)
IMPORTANT: This module is strictly limited to TWO sub-categories only. No fine dining, cafes, bars, or chains.

5a. Local Snacks / Street Food (当地小吃推荐)
json
{
  "module": "dining",
  "subsection": "local_snacks",
  "data": [
    {
      "snack_name": "string — e.g., 'Mapo Tofu'",
      "snack_name_local": "string — local language name",
      "recommended_shop": "string — stall or shop name",
      "location": {
        "address": "string",
        "map_link": "string — Baidu Maps (domestic) or Google Maps (international)",
        "nearby_landmark": "string"
      },
      "price": "string — e.g., '¥15'",
      "rating": {
        "source": "dianping" | "google" | "none",
        "score": "number — optional, e.g., 4.5",
        "display": "string — e.g., '大众点评：4.5/5' or 'Google：4.6/5'"
      },
      "description": "string — what makes it special, how to eat it"
    }
  ]
}
5b. Signature Restaurants Worth a Detour (值得专程去)
json
{
  "module": "dining",
  "subsection": "worth_a_detour",
  "data": [
    {
      "restaurant_name": "string",
      "restaurant_name_local": "string — local language name",
      "signature_dishes": ["string — e.g., 'Kung Pao Chicken'"],
      "location": {
        "address": "string",
        "map_link": "string — Baidu Maps (domestic) or Google Maps (international)"
      },
      "price_range": "string — e.g., '¥80-150/person'",
      "rating": {
        "source": "dianping" | "google" | "none",
        "score": "number — optional",
        "display": "string — e.g., '大众点评：4.7/5'"
      },
      "why_worth_detour": "string — the story, reputation, or unique factor",
      "reservation_needed": "boolean",
      "reservation_info": "string — optional"
    }
  ]
}
Module 6: Local Tips (当地贴士)
json
{
  "module": "local_tips",
  "data": {
    "transportation": {
      "getting_around": "string — overview",
      "tips": ["string — specific transport tips"]
    },
    "cultural_etiquette": {
      "overview": "string",
      "dos_and_donts": ["string — do's", "string — don'ts"]
    },
    "weather": {
      "best_season": "string",
      "current_season_notes": "string",
      "what_to_wear": "string"
    },
    "money": {
      "currency": "string",
      "payment_methods": ["string — e.g., 'WeChat Pay', 'Credit Card'"],
      "tipping_culture": "string"
    },
    "safety": {
      "general_safety": "string",
      "emergency_numbers": "string — e.g., '110 for police'"
    },
    "other": ["string — any additional practical advice"]
  }
}
