#!/usr/bin/env python3
"""
build_geojson.py
----------------
Builds the map-ready outputs from the seed CSVs:

  output/speed_zones.geojson  - LineString per corridor segment (Point if only
                                one anchor is known)
  output/cameras.geojson      - Point per provisional camera anchor
  output/legal_defaults.json  - non-spatial national legal reference
                                (default limits have no single geometry)

Geometry comes from the landmark registry via geom_from_key / geom_to_key
(zones) and the geocoded camera file. Records whose anchors cannot be
resolved are skipped from the spatial layer and reported, so nothing is
placed on the map without a real anchor.

Pure standard library (csv + json) so it runs with no extra dependencies.
GeoJSON coordinate order is [lon, lat] per RFC 7946.
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from landmarks import resolve  # noqa: E402

ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)


def load(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num_or_none(x):
    if x is None or str(x).strip() == "":
        return None
    try:
        v = float(x)
        return int(v) if v.is_integer() else v
    except ValueError:
        return None


def clean(row, drop=()):
    """Copy row -> properties, coercing numeric fields, dropping helper keys."""
    numeric = {"speed_limit_kmh", "speed_limit_min_kmh", "speed_limit_max_kmh",
               "confidence_score", "latitude", "longitude"}
    props = {}
    for k, v in row.items():
        if k in drop:
            continue
        if k in numeric:
            props[k] = num_or_none(v)
        else:
            props[k] = (v.strip() if isinstance(v, str) else v) or None
    return props


def build_zones():
    rows = load("seed_speed_zones.csv")
    feats, skipped = [], []
    for r in rows:
        a = resolve(r.get("geom_from_key", ""))
        b = resolve(r.get("geom_to_key", ""))
        if a and b:
            # LineString anchor->anchor (a rough stand-in for true road geometry)
            geom = {"type": "LineString",
                    "coordinates": [[a[1], a[0]], [b[1], b[0]]]}
            anchor_prec = "two_landmark_anchors"
        elif a:
            geom = {"type": "Point", "coordinates": [a[1], a[0]]}
            anchor_prec = a[2]
        else:
            skipped.append(r["zone_id"])
            continue
        props = clean(r, drop=("geom_from_key", "geom_to_key"))
        props["geometry_anchor"] = anchor_prec
        props["_layer"] = "speed_zone"
        feats.append({"type": "Feature", "geometry": geom, "properties": props})
    fc = {"type": "FeatureCollection",
          "name": "kenya_speed_zones",
          "metadata": {
              "note": "Segment geometry is approximated from landmark anchors, "
                      "NOT traced road centrelines. Phase 2 replaces these with "
                      "OSM/KeNHA geometry.",
              "count": len(feats)},
          "features": feats}
    write("speed_zones.geojson", fc)
    if skipped:
        print(f"  zones skipped (no anchor): {skipped}")
    return len(feats)


def build_cameras():
    cam_file = "cameras_geocoded.csv" if os.path.exists(
        os.path.join(DATA, "cameras_geocoded.csv")) else "seed_cameras.csv"
    rows = load(cam_file)
    feats, skipped = [], []
    for r in rows:
        lat, lon = r.get("latitude", ""), r.get("longitude", "")
        if not (str(lat).strip() and str(lon).strip()):
            skipped.append(r["camera_id"])
            continue
        geom = {"type": "Point", "coordinates": [float(lon), float(lat)]}
        props = clean(r, drop=("landmark_key",))
        props["_layer"] = "camera"
        feats.append({"type": "Feature", "geometry": geom, "properties": props})
    fc = {"type": "FeatureCollection",
          "name": "kenya_speed_cameras",
          "metadata": {
              "note": "Every point is a LANDMARK ANCHOR pending field verification, "
                      "NOT a confirmed camera coordinate. NTSA has not published "
                      "exact camera locations.",
              "source_file": cam_file,
              "count": len(feats)},
          "features": feats}
    write("cameras.geojson", fc)
    if skipped:
        print(f"  cameras skipped (no coords): {skipped}")
    return len(feats)


def build_legal():
    rows = load("seed_legal_defaults.csv")
    payload = {
        "name": "kenya_legal_default_speed_limits",
        "note": "National statutory/agency defaults. These have no single map "
                "geometry; apply as fallback where no posted/segment limit exists.",
        "rules": [clean(r) for r in rows],
    }
    write("legal_defaults.json", payload)
    return len(rows)


def write(name, obj):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"  wrote {os.path.relpath(path, ROOT)}")


def embed_for_app():
    """Write app/data.js with layers as globals so index.html works via file://."""
    app = os.path.join(ROOT, "app")
    os.makedirs(app, exist_ok=True)
    def rd(n):
        return json.load(open(os.path.join(OUT, n), encoding="utf-8"))
    payload = (
        "// AUTO-GENERATED by scripts/build_geojson.py - do not edit by hand.\n"
        "window.SPEED_ZONES = " + json.dumps(rd("speed_zones.geojson")) + ";\n"
        "window.CAMERAS = " + json.dumps(rd("cameras.geojson")) + ";\n"
        "window.LEGAL_DEFAULTS = " + json.dumps(rd("legal_defaults.json")) + ";\n"
    )
    with open(os.path.join(app, "data.js"), "w", encoding="utf-8") as f:
        f.write(payload)
    print("  wrote app/data.js (embedded layers for offline map)")


def main():
    print("Building GeoJSON outputs...")
    nz = build_zones()
    nc = build_cameras()
    nl = build_legal()
    embed_for_app()
    print(f"\nDone: {nz} zone features, {nc} camera features, {nl} legal rules.")


if __name__ == "__main__":
    main()
