from __future__ import annotations
"""Simple CSV importer for the Sydney Live Map backend.

Supports two modes:
 - locations: CSV with columns name, latitude, longitude, type
 - metrics: CSV with columns timestamp, pedestrian_count, traffic_count and either location_id or location_name

Usage examples:
 python backend/app/import_csv.py --mode locations --file new_locations.csv
 python backend/app/import_csv.py --mode metrics --file metrics.csv --by name
"""
import argparse
import csv
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from .database import SessionLocal
from . import models


def _get_field(row: dict, *names: str) -> str:
    """Return the first non-empty string value from row for the provided names, or empty string."""
    for n in names:
        v = row.get(n)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return ""


def parse_timestamp(s: str) -> datetime:
    # Accept ISO-8601 strings. If no timezone provided assume UTC.
    s = s.strip()
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        # fallback: try parsing as integer epoch seconds
        try:
            ts = int(s)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        except Exception as exc:
            raise ValueError(f"Could not parse timestamp '{s}': {exc}")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def import_locations(path: str, session, update_existing: bool = False, batch_size: int = 100):
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        added = 0
        updated = 0
        for i, row in enumerate(reader, start=1):
            name = _get_field(row, 'name', 'Name')
            if not name:
                print(f"Skipping row {i}: missing 'name'")
                continue
            try:
                lat_s = _get_field(row, 'latitude', 'Latitude')
                lon_s = _get_field(row, 'longitude', 'Longitude')
                if not lat_s or not lon_s:
                    raise ValueError('missing lat/lon')
                lat = float(lat_s)
                lon = float(lon_s)
            except Exception:
                print(f"Skipping row {i} ('{name}'): invalid latitude/longitude")
                continue
            typ = _get_field(row, 'type', 'Type') or 'pedestrian'

            existing = session.scalar(select(models.Location).where(models.Location.name == name))
            if existing:
                if update_existing:
                    existing.latitude = lat
                    existing.longitude = lon
                    existing.type = typ
                    updated += 1
                else:
                    print(f"Row {i}: location '{name}' exists, skipping (use --update to overwrite)")
                    continue
            else:
                loc = models.Location(name=name, latitude=lat, longitude=lon, type=typ)
                session.add(loc)
                added += 1

            if (i % batch_size) == 0:
                session.commit()
        session.commit()
    print(f"Import locations finished. Added={added} Updated={updated}")


def import_metrics(path: str, session, by: str = 'id', batch_size: int = 500):
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        added = 0
        skipped = 0
        for i, row in enumerate(reader, start=1):
            ts_raw = _get_field(row, 'timestamp', 'Timestamp')
            if not ts_raw:
                print(f"Skipping row {i}: missing 'timestamp'")
                skipped += 1
                continue
            try:
                ts = parse_timestamp(ts_raw)
            except Exception as exc:
                print(f"Skipping row {i}: invalid timestamp '{ts_raw}': {exc}")
                skipped += 1
                continue

            try:
                ped_s = _get_field(row, 'pedestrian_count', 'Pedestrian_count', 'pedestrian', 'Pedestrian')
                traf_s = _get_field(row, 'traffic_count', 'Traffic_count', 'traffic', 'Traffic')
                if not ped_s or not traf_s:
                    raise ValueError('missing counts')
                ped = int(ped_s)
                traf = int(traf_s)
            except Exception:
                print(f"Skipping row {i} (ts={ts}): missing or invalid counts")
                skipped += 1
                continue

            loc_id: Optional[int] = None
            if by == 'id':
                lid = _get_field(row, 'location_id', 'Location_id', 'locationId')
                if not lid:
                    print(f"Skipping row {i}: missing 'location_id' (mode id)")
                    skipped += 1
                    continue
                try:
                    loc_id = int(lid)
                except Exception:
                    print(f"Skipping row {i}: invalid location_id '{lid}'")
                    skipped += 1
                    continue
            else:
                lname = _get_field(row, 'location_name', 'Location_name', 'location', 'Location')
                if not lname:
                    print(f"Skipping row {i}: missing 'location_name' (mode name)")
                    skipped += 1
                    continue
                loc = session.scalar(select(models.Location).where(models.Location.name == lname))
                if not loc:
                    print(f"Skipping row {i}: location named '{lname}' not found")
                    skipped += 1
                    continue
                loc_id = loc.id

            # Avoid duplicates (unique constraint on location_id + timestamp)
            exists = session.scalar(select(models.Metric).where(models.Metric.location_id == loc_id, models.Metric.timestamp == ts))
            if exists:
                print(f"Row {i}: metric for location_id={loc_id} timestamp={ts.isoformat()} already exists, skipping")
                skipped += 1
                continue

            metric = models.Metric(location_id=loc_id, timestamp=ts, pedestrian_count=ped, traffic_count=traf)
            session.add(metric)
            added += 1

            if (i % batch_size) == 0:
                session.commit()
        session.commit()
    print(f"Import metrics finished. Added={added} Skipped={skipped}")


def main():
    parser = argparse.ArgumentParser(description='CSV importer for Sydney Live Map backend')
    parser.add_argument('--mode', choices=['locations', 'metrics'], required=True, help='What to import')
    parser.add_argument('--file', required=True, help='CSV file path')
    parser.add_argument('--update', action='store_true', help='When importing locations, update existing by name')
    parser.add_argument('--by', choices=['id', 'name'], default='id', help='When importing metrics, match location by id or name')
    parser.add_argument('--batch-size', type=int, default=500, help='Commit batch size')

    args = parser.parse_args()

    session = SessionLocal()
    try:
        if args.mode == 'locations':
            import_locations(args.file, session, update_existing=args.update, batch_size=args.batch_size)
        else:
            import_metrics(args.file, session, by=args.by, batch_size=args.batch_size)
    finally:
        session.close()


if __name__ == '__main__':
    main()
