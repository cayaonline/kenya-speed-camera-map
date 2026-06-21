"""
landmarks.py
------------
A small, hand-curated registry of APPROXIMATE coordinates for well-known
Nairobi-area landmarks used as geometry anchors.

CRITICAL ACCURACY NOTE
======================
None of these coordinates are camera locations. They are approximate
positions of public landmarks (hotels, stadia, interchanges, estates),
used only to give a seed record a provisional place on the map.

Every coordinate carries a `precision` flag:
  - "geocoded_landmark": a well-known fixed landmark; position good to ~tens of metres
  - "approximate":       a fuzzy/loosely-located place; treat with caution

NTSA has not published exact camera coordinates. Until field verification
or an official dataset is obtained, no point in this project should be
presented as an exact camera position.

Coordinates are (lat, lon) in WGS84 / EPSG:4326.
"""

LANDMARKS = {
    # key: (lat, lon, precision, human_name)
    "safari_park":                (-1.2316, 36.8839, "geocoded_landmark", "Safari Park Hotel, Thika Rd"),
    "jomoko_turnoff":             (-1.2120, 36.8990, "approximate",        "Jomoko / Thika Road turnoff"),
    "allsops":                    (-1.2540, 36.8665, "geocoded_landmark", "Allsops, Thika Rd"),
    "pangani_interchange":        (-1.2660, 36.8390, "geocoded_landmark", "Pangani / Muthaiga interchange"),
    "roysambu_trm":               (-1.2186, 36.8880, "geocoded_landmark", "Thika Road Mall (TRM), Roysambu"),
    "southern_bypass_ngong":      (-1.3170, 36.7470, "approximate",        "Southern Bypass / Ngong Rd interchange"),
    "southern_bypass_weighbridge":(-1.3300, 36.8150, "approximate",        "Southern Bypass virtual weighbridge (uncertain)"),
    "northern_bypass_gitaru":     (-1.2370, 36.6920, "approximate",        "Northern Bypass / Gitaru"),
    "northern_bypass_wangige":    (-1.2330, 36.7050, "approximate",        "Northern Bypass / Wangige"),
    "expressway_museum_hill":     (-1.2740, 36.8160, "geocoded_landmark", "Museum Hill, Nairobi Expressway"),
    "expressway_westlands":       (-1.2670, 36.8095, "geocoded_landmark", "Westlands, Nairobi Expressway"),
    "expressway_nyayo":           (-1.3050, 36.8275, "geocoded_landmark", "Nyayo Stadium (Expressway)"),
    "mombasa_nyayo":              (-1.3050, 36.8290, "geocoded_landmark", "Nyayo Stadium (Mombasa Rd)"),
    "mombasa_sameer":             (-1.3210, 36.8520, "geocoded_landmark", "Sameer Business Park, Mombasa Rd"),
    "mombasa_gm":                 (-1.3170, 36.8470, "geocoded_landmark", "General Motors, Mombasa Rd"),
    "mombasa_cabanas":            (-1.3300, 36.8870, "geocoded_landmark", "Cabanas, Mombasa Rd"),
    "jkia_approach":              (-1.3290, 36.9080, "geocoded_landmark", "JKIA approach, Mombasa Rd"),
    "waiyaki_kangemi":            (-1.2640, 36.7470, "geocoded_landmark", "Kangemi, Waiyaki Way"),
    "waiyaki_uthiru":             (-1.2570, 36.7180, "geocoded_landmark", "Uthiru, Waiyaki Way"),
    "langata_uhuru_gardens":      (-1.3163, 36.8047, "geocoded_landmark", "Uhuru Gardens, Lang'ata Rd"),
    "western_bypass_ruaka":       (-1.2050, 36.7795, "geocoded_landmark", "Ruaka, Western Bypass"),
    "redhill_link":               (-1.2150, 36.7400, "approximate",        "Redhill Link Rd (approximate)"),
}


def resolve(key):
    """Return (lat, lon, precision, name) for a landmark key, or None if unknown."""
    if not key:
        return None
    return LANDMARKS.get(key.strip())


if __name__ == "__main__":
    print(f"{len(LANDMARKS)} landmarks registered:\n")
    for k, (lat, lon, prec, name) in sorted(LANDMARKS.items()):
        print(f"  {k:32s} {lat:>9.4f},{lon:>9.4f}  [{prec:18s}] {name}")
