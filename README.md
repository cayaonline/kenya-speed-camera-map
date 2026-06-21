# Kenya Speed Limit &amp; Camera Enforcement Map

**Public-source aggregation with confidence scoring.**
A civic-data and road-safety intelligence platform that builds a structured,
GIS-ready, source-attributed map of speed limits and automated traffic
enforcement zones in Kenya, focused on Nairobi.

🔗 **Live map:** https://cayaonline.github.io/kenya-speed-camera-map/

> ⚠️ **Not an official NTSA map.** Speed limits and camera locations must be
> verified against posted road signs and official NTSA / KeNHA notices. Camera
> points in this project are **landmark anchors**, not confirmed camera
> coordinates. For research and civic-data purposes only.

---

## Project overview

The platform aggregates information from official legislation, government
agencies, public notices, infrastructure authorities, and credible media to
build a machine-readable database of road speed limits, camera-enforced
corridors, fixed and mobile camera locations, school/safety zones, road
classifications, enforcement-confidence levels, and source attribution.

It addresses a real data gap: there is currently no publicly accessible,
machine-readable national dataset of Kenya's speed-limit zones and speed-camera
enforcement areas. With the rollout of automated enforcement and Intelligent
Transport Management Systems (ITMS), accurate speed-limit information matters
more than ever — yet it stays fragmented across traffic law, NTSA notices,
KeNHA projects, media reports, road signage, and driver-community reports.

### Objectives

1. Create a national inventory of speed-limit zones.
2. Map known and reported speed-camera enforcement areas.
3. Attach every data point to a source and a confidence score.
4. Distinguish official, reported, inferred, and field-verified information.
5. Build an extensible GIS database that supports continuous updates.
6. Keep a transparent methodology that prioritises accuracy over completeness.

### Core principles

- **Accuracy first** — nothing is presented as confirmed without verifiable evidence.
- **Source transparency** — every record carries source, date, verification status, confidence.
- **Confidence-based mapping** — users can see the reliability of every feature.
- **Continuous verification** — the dataset is built to be ground-truthed and corrected over time.

### Intended use cases

Road-safety research; fleet &amp; logistics operations; navigation / driver-assistance
data foundations; insurance &amp; risk analytics; and public transparency around
speed regulation and automated enforcement.

---

## What this MVP actually does

1. Encodes Kenya's **statutory default speed limits** from primary law.
2. Encodes **reported camera-enforcement corridors** (NTSA's 2026 ITMS rollout)
   from credible media — clearly flagged as *reported*, not *confirmed*.
3. Surfaces **uncertainty as data**: every record has a source, confidence
   score, verification status, and notes; conflicts are preserved, not hidden.

It does **not** claim exact camera GPS positions. NTSA has not published a
camera-location dataset, so no point here is presented as an exact camera point.

---

## Quick start (local)

No dependencies required for the core pipeline — Python 3.8+ standard library only.

```bash
# 1. rebuild geojson + app/data.js from the CSVs, with validation
./run.sh
#    (or: python3 scripts/geocode_locations.py && python3 scripts/validate_sources.py && python3 scripts/build_geojson.py)

# 2. open the map
#    a) double-click app/index.html        (offline; reads app/data.js)
#    b) or serve it like the live site:
python3 -m http.server -d app 8000          # -> http://localhost:8000
```

Edit loop: **change `data/*.csv` → `./run.sh` → refresh browser.**

---

## Deploy &amp; share (GitHub Pages)

The site is static (`app/` = `index.html` + generated `data.js`). GitHub rebuilds
the data on every push via `.github/workflows/deploy.yml`, so collaborators always
get a fresh map. You never commit generated files; CI regenerates them.

```bash
# one-time: authenticate (opens a browser)
gh auth login                       # GitHub.com -> HTTPS -> login with browser

# from the project root
git init
git add -A
git commit -m "Kenya speed limit & camera enforcement map — full prototype"
git branch -M main

# creates the repo, wires origin, and pushes in one step
gh repo create kenya-speed-camera-map --public --source=. --remote=origin --push
```

Then in the repo: **Settings → Pages → Source → "GitHub Actions"**. Watch the
**Actions** tab; when it goes green the live link is
`https://cayaonline.github.io/kenya-speed-camera-map/`.

Update loop after that: `git add -A && git commit -m "…" && git push` → auto-rebuild + redeploy.

> The live map loads Leaflet and CARTO basemap tiles from CDNs, so testers need
> internet for the basemap to render.

---

## Project structure

```
kenya-speed-camera-map/
├── README.md
├── requirements.txt          # stdlib-only core; optional libs for phase 2
├── run.sh                    # one-command pipeline
├── .github/workflows/deploy.yml   # CI: build data + publish app/ to Pages
├── .gitignore                # ignores generated artifacts (CI rebuilds them)
├── data/
│   ├── seed_legal_defaults.csv     # national statutory defaults (non-spatial)
│   ├── seed_speed_zones.csv        # corridor segments (spatial)
│   ├── seed_cameras.csv            # provisional camera points (coords blank)
│   ├── cameras_geocoded.csv        # ← generated: anchors filled from registry
│   ├── sources.csv                 # bibliography + reliability ratings
│   └── field_verification_queue.csv# prioritised real-world checks
├── scripts/
│   ├── landmarks.py          # approximate, precision-flagged landmark anchors
│   ├── geocode_locations.py  # resolves landmark_key -> anchor coords
│   ├── validate_sources.py   # data-integrity checks (fails build on error)
│   └── build_geojson.py      # emits GeoJSON + app/data.js
├── output/                   # ← generated
│   ├── speed_zones.geojson
│   ├── cameras.geojson
│   └── legal_defaults.json
└── app/
    ├── index.html            # Leaflet map (filters, search, popups)
    └── data.js               # ← generated: layers embedded for offline use
```

---

## Methodology

**Separate the kinds of truth.** Every record carries a `source_type` that fixes
how much it can be trusted:

| source_type | meaning | example |
|---|---|---|
| `law` | statute / gazetted rule | Traffic (Speed Limits) Rules 1975 |
| `official_agency` | NTSA / KeNHA statement | NTSA ITMS announcement |
| `media` | credible news report | Daily Nation corridor list |
| `field_observation` | ground-truth | *(none yet)* |
| `osm` | OpenStreetMap geometry | road centrelines (geometry only) |
| `inferred` | deduced from road class | "80 because it's a bypass" |

**Never invent coordinates.** Camera seed records ship with **blank**
lat/lon. The geocoder only attaches the coordinate of a *named landmark*
(e.g. Safari Park Hotel), tagged `coordinate_precision = geocoded_landmark` or
`approximate`. A landmark anchor is explicitly **not** the camera.

**Preserve conflicts.** Where sources disagree, the disagreement is encoded.
Example: Thika Road's Jomoko / Allsops / Pangani sections are listed at
**80 km/h** in the seed brief but **up to 110 km/h** in NTSA-attributed media.
Those records store an 80–110 range, carry `needs_field_check`, and appear in the
verification queue (`VQ-001`).

**Geometry is approximate in the MVP.** Speed-zone segments are straight lines
between landmark anchors — a stand-in for true road centrelines. Phase 2 replaces
them with traced OSM / KeNHA geometry.

---

## Confidence scoring

`confidence_score` (0–100) → `confidence_level`:

| Score | Basis | Level |
|---|---|---|
| 95–100 | Official law/agency, exact location + limit | high |
| 85–94 | Official agency, approximate location | high |
| 75–84 | Multiple credible media agree, specific | high |
| 60–74 | One credible media, specific location | medium |
| 50–59 | Media, vague location / no exact limit | medium |
| 20–39 | OSM / inferred from road type only | low |
| 0–19 | Rumour / social — **not displayed as confirmed** | low |

Buckets: **high ≥ 75**, **medium 50–74**, **low < 50**.
`validate_sources.py` fails the build if score and level ever disagree.

---

## Source hierarchy

Authoritative first, media strictly secondary:

1. **Kenya Law** — Traffic Act (Cap 403); Traffic (Speed Limits) Rules 1975 (rev. 2022).
2. **NTSA** — notices, FAQs, ITMS announcements.
3. **KeNHA / Ministry of Roads &amp; Transport** — corridor and project notices.
4. **Road operators** — e.g. Moja Expressway for the Nairobi Expressway.
5. **Credible media** — Nation, Star, Business Daily, Standard, Citizen, NTV, etc. (reported, never official).
6. **OpenStreetMap** — road geometry only; never legal proof of a limit.

Enforced rule: a record with `source_type = media` can never be `verification_status = official`.

---

## Data integrity checks (`validate_sources.py`)

Runs on every build (locally and in CI) and exits non-zero on any error:

- no record without a source; no camera without a confidence level;
- no `exact` coordinate unless `field_verified` / `official`;
- `speed_limit_kmh` numeric or blank; `min ≤ max` for ranges;
- `confidence_score` matches `confidence_level` and sits in 0–100;
- `media` ⇒ not `official`; `inferred` zone ⇒ not `camera_present = true`;
- coordinates (if present) fall inside a Kenya bounding box.

Current status: **15 zones, 15 cameras, 6 legal rules, 11 sources — 0 errors.**

---

## How to update the data

1. **Edit the CSVs in `data/`.** Always fill `source_name`, `source_url`,
   `source_type`, `source_date`, `confidence_score`, `confidence_level`,
   `verification_status`, `notes`.
2. **Register the source** in `sources.csv` (`reliability_rating` 1–5).
3. **Add a landmark** to `scripts/landmarks.py` if you reference a new place —
   with an honest `precision` flag. Never type a coordinate you can't justify.
4. **Re-run** `./run.sh` (validator blocks inconsistent rows; outputs regenerate).
5. **Commit &amp; push** — CI redeploys the live map.

### How to add field verification

1. Take an item from `data/field_verification_queue.csv` (start `priority = high`).
2. Verify on the ground (street view / dashcam / site visit / official request).
3. In the row, set real `latitude`/`longitude` + `coordinate_precision = exact`,
   `verification_status = field_verified`, `last_verified = <YYYY-MM-DD>`, bump the
   score, and add a `field_observation` source.
4. Resolve the queue item and re-run `./run.sh`.

Only `field_verified` / `official` records may use `coordinate_precision = exact`.

---

## Next data-collection plan

- **Phase 1 — official requests (highest leverage).** File an NTSA / KeNHA request
  for the ITMS camera register and gazetted section limits. One release lifts many
  records from `media / needs_field_check` to `official`. Resolves `VQ-001/012/013`.
- **Phase 2 — real road geometry.** Replace landmark-anchor lines with traced OSM /
  KeNHA centrelines (`osmnx` / Overpass); buffer camera zones instead of dropping points.
- **Phase 3 — field truthing.** Dashcam + GPS passes on Thika Rd, Mombasa Rd,
  Southern Bypass and the Expressway; photograph posted signs to settle the 80-vs-110 conflict.
- **Phase 4 — crowdsourcing.** Lightweight report form → moderation queue; community
  reports enter at low confidence until corroborated.
- **Phase 5 — schema growth.** Optional PostGIS backend; per-vehicle-class limits;
  time-of-day / school-hours zones; change-history for auditable limit revisions.

---

## Tech stack

- **Pipeline:** Python 3 standard library (`csv`, `json`) — zero install.
- **Map:** Leaflet 1.9 + CARTO dark basemap (CDN), single static HTML file.
- **CI/CD:** GitHub Actions → GitHub Pages.
- **Optional:** `geopy` (online geocoding); `geopandas`/`shapely`/`osmnx`/`folium` for Phase 2.

## Licensing &amp; attribution

Road geometry derived from OpenStreetMap is © OpenStreetMap contributors (ODbL) —
attribute accordingly. Legal text is Kenyan law via Kenya Law. Media claims remain
the property of their publishers and are used as cited, attributed references.

## Disclaimer

Independent public-data aggregation initiative, **not** affiliated with or endorsed
by NTSA, KeNHA, or any government agency. Always defer to posted road signage and
official notices. Intended for research, analysis, and civic-data purposes; not the
sole source of legal or regulatory guidance.
