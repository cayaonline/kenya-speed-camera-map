#!/usr/bin/env bash
# Run the full data pipeline, then tell you how to open the map.
# Usage: ./run.sh         (offline, deterministic)
#        ./run.sh --online (also try OSM Nominatim for unknown landmarks)
set -euo pipefail
cd "$(dirname "$0")"

echo "==> 1/3  Geocode camera anchors"
python3 scripts/geocode_locations.py "$@"

echo; echo "==> 2/3  Validate data integrity"
python3 scripts/validate_sources.py

echo; echo "==> 3/3  Build GeoJSON + app data"
python3 scripts/build_geojson.py

echo
echo "Done. Open the map with either:"
echo "  • Double-click  app/index.html          (works offline, uses app/data.js)"
echo "  • Or serve it:  python3 -m http.server -d app 8000  ->  http://localhost:8000"
