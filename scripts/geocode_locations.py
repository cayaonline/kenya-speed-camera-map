#!/usr/bin/env python3
"""
geocode_locations.py
--------------------
Resolves the `landmark_key` on each seed camera to an APPROXIMATE anchor
coordinate from the local landmark registry (scripts/landmarks.py), and
sets `coordinate_precision` accordingly.

Design rules (enforced here):
  * We NEVER invent a camera coordinate. We only attach the coordinate of a
    known landmark, clearly flagged as an anchor, not the camera itself.
  * If a landmark key is unknown, coordinates are left blank and the record
    keeps coordinate_precision = "unknown" (it will be skipped by the GeoJSON
    builder and should already be in the field-verification queue).
  * Optional: if `--online` is passed AND the `geopy` package + network are
    available, unknown landmarks may be looked up via OSM Nominatim. This is
    opt-in and still flagged as "approximate" — disabled by default for
    determinism and because the sandbox has no network for map services.

Input : data/seed_cameras.csv
Output: data/cameras_geocoded.csv
"""
import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from landmarks import resolve  # noqa: E402

ROOT = os.path.dirname(HERE)
IN_CSV = os.path.join(ROOT, "data", "seed_cameras.csv")
OUT_CSV = os.path.join(ROOT, "data", "cameras_geocoded.csv")


def geocode_online(name):
    """Optional OSM Nominatim lookup. Returns (lat, lon) or None. Always 'approximate'."""
    try:
        from geopy.geocoders import Nominatim
    except ImportError:
        print("  ! geopy not installed; skipping online geocoding", file=sys.stderr)
        return None
    try:
        geo = Nominatim(user_agent="kenya-speed-camera-map/0.1")
        loc = geo.geocode(f"{name}, Nairobi, Kenya", timeout=10)
        if loc:
            return round(loc.latitude, 4), round(loc.longitude, 4)
    except Exception as e:  # network / rate-limit / service errors
        print(f"  ! online geocode failed for {name!r}: {e}", file=sys.stderr)
    return None


def main(online=False):
    with open(IN_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    resolved, blank = 0, 0
    for r in rows:
        key = r.get("landmark_key", "").strip()
        hit = resolve(key)
        if hit:
            lat, lon, precision, _name = hit
            r["latitude"] = f"{lat:.4f}"
            r["longitude"] = f"{lon:.4f}"
            r["coordinate_precision"] = precision
            resolved += 1
        elif online and r.get("nearest_landmark"):
            res = geocode_online(r["nearest_landmark"])
            if res:
                r["latitude"], r["longitude"] = f"{res[0]:.4f}", f"{res[1]:.4f}"
                r["coordinate_precision"] = "approximate"
                resolved += 1
            else:
                r["coordinate_precision"] = "unknown"
                blank += 1
        else:
            # leave coordinates blank; cannot place this point honestly
            r["latitude"] = ""
            r["longitude"] = ""
            r["coordinate_precision"] = "unknown"
            blank += 1

    fieldnames = list(rows[0].keys())
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"Geocoded {resolved} camera anchor(s); {blank} left blank (unknown).")
    print(f"  -> {OUT_CSV}")
    print("  NOTE: all coordinates are LANDMARK ANCHORS, not confirmed camera points.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--online", action="store_true",
                    help="attempt OSM Nominatim for unknown landmarks (needs network + geopy)")
    args = ap.parse_args()
    main(online=args.online)
