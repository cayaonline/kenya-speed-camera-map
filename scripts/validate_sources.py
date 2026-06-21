#!/usr/bin/env python3
"""
validate_sources.py
-------------------
Automated data-integrity checks (Build spec, Section F).

Rules enforced:
  1. No record without a source.
  2. No camera record without a confidence level.
  3. No "exact" coordinate unless source/field verification supports it.
  4. speed_limit_kmh must be numeric or blank.
  5. speed_limit_min/max used (and ordered) for ranges.
  6. confidence_score must match confidence_level bucket (high>=75, med 50-74, low<50).
  7. source_type = media  =>  verification_status != official.
  8. inferred zones must not be camera_present = true.
  9. every camera with coordinates must be inside a sane Kenya bounding box.
 10. confidence_score within 0-100.

Exit code is non-zero if any ERROR-level issue is found (warnings don't fail).
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# Kenya rough bounding box (lat, lon)
KE_BBOX = dict(lat_min=-5.0, lat_max=5.5, lon_min=33.5, lon_max=42.0)

errors, warnings = [], []


def err(where, msg):
    errors.append(f"[ERROR] {where}: {msg}")


def warn(where, msg):
    warnings.append(f"[WARN ] {where}: {msg}")


def is_number(x):
    if x is None or str(x).strip() == "":
        return True  # blank allowed
    try:
        float(x)
        return True
    except ValueError:
        return False


def bucket_ok(score, level):
    if str(score).strip() == "" or str(level).strip() == "":
        return False
    s = float(score)
    level = level.strip().lower()
    if level == "high":
        return s >= 75
    if level == "medium":
        return 50 <= s <= 74
    if level == "low":
        return s < 50
    return False


def load(name):
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def check_score_range(where, row):
    sc = row.get("confidence_score", "")
    if sc.strip() and (not is_number(sc) or not (0 <= float(sc) <= 100)):
        err(where, f"confidence_score {sc!r} out of 0-100")


def validate_zones():
    rows = load("seed_speed_zones.csv")
    for r in rows:
        zid = r["zone_id"]
        where = f"zones/{zid}"
        if not r.get("source_name", "").strip():
            err(where, "missing source_name")
        if not is_number(r.get("speed_limit_kmh")):
            err(where, f"speed_limit_kmh not numeric: {r.get('speed_limit_kmh')!r}")
        # range ordering
        lo, hi = r.get("speed_limit_min_kmh", ""), r.get("speed_limit_max_kmh", "")
        if lo.strip() and hi.strip() and is_number(lo) and is_number(hi):
            if float(lo) > float(hi):
                err(where, f"speed_min {lo} > speed_max {hi}")
        if not bucket_ok(r.get("confidence_score"), r.get("confidence_level")):
            err(where, f"score {r.get('confidence_score')} != level {r.get('confidence_level')}")
        if r.get("source_type") == "media" and r.get("verification_status") == "official":
            err(where, "media source cannot be verification_status=official")
        if r.get("zone_type") == "inferred" and str(r.get("camera_present")).lower() == "true":
            err(where, "inferred zone must not have camera_present=true")
        check_score_range(where, r)
    return len(rows)


def validate_cameras(fname="seed_cameras.csv"):
    rows = load(fname)
    for r in rows:
        cid = r["camera_id"]
        where = f"cameras/{cid}"
        if not r.get("source_name", "").strip():
            err(where, "missing source_name")
        if not r.get("confidence_level", "").strip():
            err(where, "camera missing confidence_level")
        if not is_number(r.get("speed_limit_kmh")):
            err(where, f"speed_limit_kmh not numeric: {r.get('speed_limit_kmh')!r}")
        if not bucket_ok(r.get("confidence_score"), r.get("confidence_level")):
            err(where, f"score {r.get('confidence_score')} != level {r.get('confidence_level')}")
        if r.get("source_type") == "media" and r.get("verification_status") == "official":
            err(where, "media source cannot be verification_status=official")
        prec = r.get("coordinate_precision", "")
        if prec == "exact" and r.get("verification_status") not in ("field_verified", "official"):
            err(where, "coordinate_precision=exact requires field_verified/official status")
        lat, lon = r.get("latitude", ""), r.get("longitude", "")
        if lat.strip() and lon.strip():
            if not (is_number(lat) and is_number(lon)):
                err(where, "non-numeric coordinates")
            else:
                la, lo = float(lat), float(lon)
                if not (KE_BBOX["lat_min"] <= la <= KE_BBOX["lat_max"]
                        and KE_BBOX["lon_min"] <= lo <= KE_BBOX["lon_max"]):
                    err(where, f"coordinates outside Kenya bbox: {la},{lo}")
                if prec == "unknown":
                    warn(where, "has coordinates but precision=unknown")
        check_score_range(where, r)
    return len(rows)


def validate_legal():
    rows = load("seed_legal_defaults.csv")
    for r in rows:
        rid = r["rule_id"]
        where = f"legal/{rid}"
        if not r.get("source_name", "").strip():
            err(where, "missing source_name")
        if not is_number(r.get("speed_limit_kmh")):
            err(where, f"speed_limit_kmh not numeric: {r.get('speed_limit_kmh')!r}")
        if not bucket_ok(r.get("confidence_score"), r.get("confidence_level")):
            err(where, f"score {r.get('confidence_score')} != level {r.get('confidence_level')}")
        check_score_range(where, r)
    return len(rows)


def validate_sources_referential():
    """Every source_url used in zones/cameras should ideally exist in sources.csv."""
    srcs = load("sources.csv")
    known_urls = {s["url"].strip() for s in srcs if s.get("url", "").strip()}
    for fname in ("seed_speed_zones.csv", "seed_cameras.csv"):
        for r in load(fname):
            url = r.get("source_url", "").strip()
            if url and url not in known_urls:
                warn(f"{fname}/{r.get('zone_id', r.get('camera_id'))}",
                     f"source_url not in sources.csv: {url}")
    return len(srcs)


def main():
    print("=" * 64)
    print("  Kenya Speed Camera Map - data validation")
    print("=" * 64)
    nz = validate_zones()
    # validate geocoded cameras if present, else seed
    cam_file = "cameras_geocoded.csv" if os.path.exists(
        os.path.join(DATA, "cameras_geocoded.csv")) else "seed_cameras.csv"
    nc = validate_cameras(cam_file)
    nl = validate_legal()
    ns = validate_sources_referential()

    print(f"\nChecked: {nz} zones, {nc} cameras ({cam_file}), {nl} legal rules, {ns} sources\n")

    for w in warnings:
        print(w)
    for e in errors:
        print(e)

    print("\n" + "-" * 64)
    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    print(f"PASSED: 0 errors, {len(warnings)} warning(s)")


if __name__ == "__main__":
    main()
