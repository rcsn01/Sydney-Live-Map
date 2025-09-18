from __future__ import annotations
"""Simple CSV importer for the Sydney Live Map backend.

 Supports two modes:
 - locations: CSV with columns name, latitude, longitude, type
 - metrics: CSV with columns timestamp, count (or pedestrian_count/traffic_count) and either location_id or location_name

Usage examples:
python backend/app/import_csv.py --mode locations --file "file path" --db-url postgresql+psycopg://dev:dev@localhost:5433/sydmap
python backend/app/import_csv.py --mode metrics --file "file path" --db-url postgresql+psycopg://dev:dev@localhost:5433/sydmap
"""
import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

# Add the parent directory to Python path to allow absolute imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Now use absolute imports
from app import models

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


def normalize_type(s: str) -> str:
    """Normalize classification/type strings to a short internal form."""
    if not s:
        return ""
    s = s.strip().lower()
    if "light" in s:
        return "light_vehicles"
    if "heavy" in s:
        return "heavy_vehicles"
    if "all" in s:
        return "all_vehicles"
    return s.replace(" ", "_")


def create_session(db_url: str):
    """Create a database session from the provided URL."""
    # Use psycopg3 driver explicitly for better performance
    if db_url.startswith('postgresql://') and ':///' not in db_url:
        db_url = db_url.replace('postgresql://', 'postgresql+psycopg://')
    
    print(f"Creating engine with URL: {db_url.split('@')[0]}****@{db_url.split('@')[1] if '@' in db_url else '****'}")
    
    # Add connection timeout and better error handling
    engine = create_engine(
        db_url, 
        pool_pre_ping=True,
        connect_args={
            'connect_timeout': 10,  # 10 second connection timeout
            'application_name': 'csv_importer'
        }
    )
    
    # Test connection
    try:
        print("Testing database connection...")
        start_time = time.time()
        with engine.connect() as test_conn:
            test_conn.execute(select(1))
        print(f"Connection successful! (took {time.time() - start_time:.2f}s)")
    except OperationalError as e:
        print(f"Database connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Is PostgreSQL running on localhost:5432?")
        print("2. Check if the database 'sydmap' exists")
        print("3. Verify username 'dev' and password 'dev' are correct")
        print("4. Check if PostgreSQL allows connections from localhost")
        raise
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def import_locations(path: str, session, update_existing: bool = False, batch_size: int = 100):
    print(f"Reading locations from: {path}")
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        print(f"CSV columns: {reader.fieldnames}")
        added = 0
        skipped = 0
        for i, row in enumerate(reader, start=1):
            name = _get_field(row, 'name', 'Name')
            if not name:
                print(f"Skipping row {i}: missing 'name'")
                skipped += 1
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
                skipped += 1
                continue
            typ = _get_field(row, 'type', 'Type') or 'pedestrian'

            # Check if a location already exists with SAME lat, lon, and type
            existing = session.scalar(
                select(models.Location).where(
                    models.Location.latitude == lat,
                    models.Location.longitude == lon,
                    models.Location.type == typ
                )
            )
            if existing:
                if update_existing:
                    existing.name = name  # Optionally update the name
                    updated = 1
                    print(f"Row {i}: updated location at ({lat}, {lon}, {typ}) with new name '{name}'")
                else:
                    print(f"Row {i}: location at ({lat}, {lon}, {typ}) already exists, skipping")
                    skipped += 1
                    continue
            else:
                # Insert a new location
                loc = models.Location(name=name, latitude=lat, longitude=lon, type=typ)
                session.add(loc)
                added += 1
                if added % 10 == 0:
                    print(f"Added {added} locations...")

            if (i % batch_size) == 0:
                print(f"Committing batch of {batch_size} records...")
                session.commit()
        session.commit()
    print(f"Import locations finished. Added={added} Skipped={skipped}")


def import_metrics(path: str, session, batch_size: int = 500):
    print(f"Reading metrics from: {path}")
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        print(f"CSV columns: {reader.fieldnames}")
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

            # Parse count
            try:
                count_s = _get_field(row, 'count', 'Count')
                if not count_s:
                    ped_s = _get_field(row, 'pedestrian_count', 'Pedestrian_count')
                    traf_s = _get_field(row, 'traffic_count', 'Traffic_count')
                    if not ped_s and not traf_s:
                        raise ValueError('missing counts')
                    ped = int(ped_s) if ped_s else 0
                    traf = int(traf_s) if traf_s else 0
                    count = ped + traf
                else:
                    count = int(count_s)
            except Exception:
                print(f"Skipping row {i} (ts={ts}): missing or invalid counts")
                skipped += 1
                continue

            # Parse type
            type_s = _get_field(row, 'type', 'Type', 'classification_type')
            if not type_s:
                print(f"Skipping row {i}: missing 'type'")
                skipped += 1
                continue
            type_norm = normalize_type(type_s)

            # Parse latitude/longitude
            try:
                lat_s = _get_field(row, 'latitude', 'Latitude')
                lon_s = _get_field(row, 'longitude', 'Longitude')
                if not lat_s or not lon_s:
                    raise ValueError("missing lat/lon")
                lat = float(lat_s)
                lon = float(lon_s)
            except Exception:
                print(f"Skipping row {i}: invalid or missing latitude/longitude")
                skipped += 1
                continue

            # Find matching location
            loc = session.scalar(
                select(models.Location).where(
                    models.Location.latitude == lat,
                    models.Location.longitude == lon,
                    models.Location.type == type_norm
                )
            )
            if not loc:
                print(f"Skipping row {i}: no Location found with lat={lat}, lon={lon}, type='{type_norm}'")
                skipped += 1
                continue

            loc_id = loc.id

            # Skip duplicates (location_id + timestamp)
            exists = session.scalar(
                select(models.Metric).where(
                    models.Metric.location_id == loc_id,
                    models.Metric.timestamp == ts
                )
            )
            if exists:
                print(f"Row {i}: metric for location_id={loc_id} timestamp={ts.isoformat()} already exists, skipping")
                skipped += 1
                continue

            metric = models.Metric(location_id=loc_id, timestamp=ts, count=count)
            session.add(metric)
            added += 1
            if added % 100 == 0:
                print(f"Added {added} metrics...")

            if (i % batch_size) == 0:
                print(f"Committing batch of {batch_size} records...")
                session.commit()
        session.commit()
    print(f"Import metrics finished. Added={added} Skipped={skipped}")


def main():
    parser = argparse.ArgumentParser(description='CSV importer for Sydney Live Map backend')
    parser.add_argument('--mode', choices=['locations', 'metrics'], required=True, help='What to import')
    parser.add_argument('--file', required=True, help='CSV file path')
    parser.add_argument('--update', action='store_true', help='When importing locations, update existing by name')
    parser.add_argument('--batch-size', type=int, default=500, help='Commit batch size')
    
    # Database connection arguments
    parser.add_argument('--db-url', help='Database URL (e.g., postgresql://user:pass@host:port/dbname)')
    parser.add_argument('--db-host', default='localhost', help='Database host')
    parser.add_argument('--db-port', default='5432', help='Database port')
    parser.add_argument('--db-name', default='sydmap', help='Database name')
    parser.add_argument('--db-user', default='dev', help='Database username')
    parser.add_argument('--db-password', default='dev', help='Database password')

    args = parser.parse_args()

    # Create database URL
    if args.db_url:
        db_url = args.db_url
    else:
        # Construct URL from individual components
        db_url = f"postgresql://{args.db_user}:{args.db_password}@{args.db_host}:{args.db_port}/{args.db_name}"

    print(f"Connecting to database: {db_url.split('@')[0]}****@{db_url.split('@')[1] if '@' in db_url else '****'}")
    
    try:
        session = create_session(db_url)
        try:
            if args.mode == 'locations':
                import_locations(args.file, session, update_existing=args.update, batch_size=args.batch_size)
            else:
                import_metrics(args.file, session, batch_size=args.batch_size)
        except Exception as e:
            print(f"Error during import: {e}")
            session.rollback()
            raise
        finally:
            session.close()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()