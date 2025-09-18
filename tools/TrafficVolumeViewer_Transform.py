"""Transform City-style traffic CSVs into the simple CSVs accepted by the
backend importer `backend/app/import_csv.py`.

This script expects a tab-separated input file with headers similar to the
sample the user provided (columns include `station_id`, `road_name`,
`classification_type`, `year`, `traffic_count`, `wgs84_latitude`,
`wgs84_longitude`). It writes two CSVs next to the script:

- `locations.csv` (columns: name,latitude,longitude,type)
- `metrics.csv`   (columns: timestamp,pedestrian_count,traffic_count,location_name)

It uses `station_id` + `road_name` to form stable location names, sets
`pedestrian_count` to 0 (because the source lacks pedestrian counts), and
creates a timestamp using the `year` (first day of the year at UTC midnight).

Usage:
    python tools/TrafficVolumeViewer_Transform.py /path/to/raw_traffic.tsv

You can then run the backend importer:
    python tools/import_csv.py --mode locations --file locations.csv --update
    python tools/import_csv.py --mode metrics --file metrics.csv --by name
"""
from __future__ import annotations
import csv
import sys
from datetime import datetime, timezone
import argparse
from pathlib import Path


def normalize_type(s: str) -> str:
    if not s:
        return "unknown"
    s = s.strip().lower()
    if "light" in s:
        return "light_vehicles"
    if "heavy" in s:
        return "heavy_vehicles"
    if "all" in s:
        return "all_vehicles"
    return s.replace(" ", "_")


def transform(
    infile: Path,
    out_dir: Path,
    log_locations: bool = True,
    log_metrics: bool = False,
    only_locations_with_metrics: bool = False,
):

    out_dir.mkdir(parents=True, exist_ok=True)
    out_loc = out_dir / "locations.csv"
    out_met = out_dir / "metrics.csv"

    with infile.open(newline='', encoding='utf-8') as fh:
        # input appears tab-separated in sample; fall back to csv.Sniffer if unsure
        sample = fh.read(8192)
        fh.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters='\t,')
        reader = csv.DictReader(fh, dialect=dialect)

        # key locations by (latitude, longitude, type) so we can emit multiple
        # rows for the same coords when the `type` differs
        # maps (lat, lon, type) -> name
        locs: dict[tuple[str, str, str], str] = {}
        mets: list[dict] = []
        kept_locations: set[tuple[str, str, str]] = set()

        total_rows = 0
        kept_metrics = 0
        skipped_metrics = 0

        def _cardinal_matches(s: str) -> bool:
            if not s:
                return False
            s2 = s.strip().upper()
            # require the word AND or BOTH somewhere in the string
            return ' AND ' in f' {s2} ' or ' BOTH ' in f' {s2} '

        for i, row in enumerate(reader, start=1):
            total_rows += 1
            station_id = (row.get("station_id") or row.get("stationid") or "").strip()
            road = (row.get("road_name") or "").strip()
            suburb = (row.get("suburb") or "").strip()
            # Prefer human-readable name: road +/- suburb. Do not include station_id
            if road and suburb:
                name = f"{road} - {suburb}"
            elif road:
                name = road
            elif suburb:
                name = suburb
            else:
                # fallback if no human name available (rare)
                name = station_id

            lat = (row.get('wgs84_latitude') or row.get('latitude') or '').strip()
            lon = (row.get('wgs84_longitude') or row.get('longitude') or '').strip()
            ctype = normalize_type(row.get('classification_type') or '')
            year = (row.get('year') or '').strip()
            traffic = (row.get('traffic_count') or '0').strip()

            # Only include metrics for rows where cardinal_direction_name contains AND or BOTH
            cdir = (row.get('cardinal_direction_name') or row.get('cardinal_direction') or '')
            if not _cardinal_matches(cdir):
                if log_metrics:
                    print(f"Row {i}: skipped metric - cardinal_direction_name='{cdir}' does not contain AND or BOTH")
                skipped_metrics += 1
                continue

            # Only include rows where period is 'ALL DAYS' (case-insensitive)
            period = (row.get('period') or '').strip().upper()
            if period != 'ALL DAYS':
                if log_metrics:
                    print(f"Row {i}: skipped metric - period='{period}' != 'ALL DAYS'")
                skipped_metrics += 1
                continue

            # Track location entries keyed by (lat, lon, type) so different
            # types at the same coords become distinct locations
            key = (lat, lon, ctype)
            prev = locs.get(key)
            if name and lat and lon:
                locs[key] = name
                if prev is None:
                    if log_locations:
                        print(f"Row {i}: added location lat={lat} lon={lon} name='{name}' type={ctype}")
                elif prev != name:
                    if log_locations:
                        print(f"Row {i}: updated location at lat={lat} lon={lon} type={ctype} from {prev} -> {name}")

            # build a reasonable timestamp from year; fall back to now UTC
            try:
                y = int(year)
                ts = datetime(y, 1, 1, tzinfo=timezone.utc).isoformat()
            except Exception:
                ts = datetime.now(tz=timezone.utc).isoformat()

            mets.append({
                'timestamp': ts,
                'count': traffic,
                'type': ctype,
                'latitude': lat,
                'longitude': lon,
            })
            kept_metrics += 1
            kept_locations.add(key)
            if log_metrics:
                print(f"Row {i}: kept metric timestamp={ts} count={traffic} type={ctype} location='{name}' coords=({lat},{lon})")

    # write locations.csv
    with out_loc.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['name', 'latitude', 'longitude', 'type'])
        writer.writeheader()
        # locs is keyed by (lat, lon, type) -> name
        if only_locations_with_metrics:
            items = ((lat, lon, t, n) for (lat, lon, t), n in locs.items() if (lat, lon, t) in kept_locations)
        else:
            items = ((lat, lon, t, n) for (lat, lon, t), n in locs.items())
        written = 0
        for lat, lon, ctype, name in items:
            writer.writerow({'name': name, 'latitude': lat, 'longitude': lon, 'type': ctype})
            written += 1

    # write metrics.csv
    with out_met.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=['timestamp', 'count', 'type', 'latitude', 'longitude'])
        writer.writeheader()
        for m in mets:
            writer.writerow(m)
    print(f"Wrote {out_loc} and {out_met}")
    print(f"Processed {total_rows} input rows")
    print(f"Kept metrics: {kept_metrics}")
    print(f"Skipped metrics: {skipped_metrics}")
    if only_locations_with_metrics:
        print(f"Locations written: {written} (only locations with kept metrics: {len(kept_locations)})")
    else:
        print(f"Locations written: {len(locs)} (locations with kept metrics: {len(kept_locations)})")


def main(argv: list[str] | None = None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(description='Transform City-format traffic CSV into locations.csv and metrics.csv')
    parser.add_argument('infile', help='input TSV/CSV file')
    parser.add_argument('out_dir', nargs='?', help='output directory (defaults to input file parent)')
    parser.add_argument('--log-locations', action='store_true', help='print per-row location add/update messages')
    parser.add_argument('--log-metrics', action='store_true', help='print per-row metric kept/skipped messages')
    parser.add_argument('--only-locations-with-metrics', action='store_true', help='write only locations that have at least one kept metric')
    args = parser.parse_args(argv)
    infile = Path(args.infile)
    out_dir = Path(args.out_dir) if args.out_dir else infile.parent
    if not infile.exists():
        print('input file not found:', infile)
        raise SystemExit(2)
    transform(infile, out_dir, log_locations=args.log_locations, log_metrics=args.log_metrics, only_locations_with_metrics=args.only_locations_with_metrics)


if __name__ == '__main__':
    main()
