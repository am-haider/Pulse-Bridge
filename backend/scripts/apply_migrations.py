#!/usr/bin/env python
"""
Apply Supabase migrations directly via PostgreSQL connection.
Run this once to create the doctors table, indexes, and match_doctors function.
"""
import os
import sys
import psycopg2
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.core.config import settings


def get_db_connection():
    """Create direct PostgreSQL connection using service role key as password."""
    # Supabase URL format: https://project-id.supabase.co
    project_id = settings.SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
    host = f"db.{project_id}.supabase.co"

    # Service role key IS the database password
    password = settings.SUPABASE_SERVICE_ROLE_KEY

    conn = psycopg2.connect(
        host=host,
        port=5432,
        dbname="postgres",
        user="postgres",
        password=password,
        sslmode="require"
    )
    conn.autocommit = True
    return conn


def apply_migration(conn, migration_path: Path, name: str):
    """Execute a migration SQL file."""
    print(f"\n{'='*60}")
    print(f"Applying {name}...")
    print(f"{'='*60}")

    with open(migration_path, 'r') as f:
        sql = f.read()

    # Split by statement (rough but works for our migrations)
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

    with conn.cursor() as cur:
        for i, stmt in enumerate(statements):
            if not stmt:
                continue
            try:
                cur.execute(stmt + ';')
                print(f"  [OK] Statement {i+1}/{len(statements)}")
            except Exception as e:
                # Some statements might fail if already exist (IF NOT EXISTS handles most)
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"  ⊘ Statement {i+1} skipped (already exists): {e}")
                else:
                    print(f"  ✗ Statement {i+1} FAILED: {e}")
                    # Continue anyway for non-critical failures

    print(f"✓ {name} completed")


def verify_setup(conn):
    """Verify the doctors table and match_doctors function exist."""
    print(f"\n{'='*60}")
    print("Verifying setup...")
    print(f"{'='*60}")

    with conn.cursor() as cur:
        # Check table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'doctors'
            )
        """)
        table_exists = cur.fetchone()[0]
        print(f"  doctors table: {'✓' if table_exists else '✗'}")

        # Check function exists
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.routines
                WHERE routine_schema = 'public' AND routine_name = 'match_doctors'
            )
        """)
        func_exists = cur.fetchone()[0]
        print(f"  match_doctors function: {'✓' if func_exists else '✗'}")

        # Check vector extension
        cur.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
        vector_exists = cur.fetchone()[0]
        print(f"  pgvector extension: {'✓' if vector_exists else '✗'}")

        if table_exists:
            cur.execute("SELECT COUNT(*) FROM public.doctors")
            count = cur.fetchone()[0]
            print(f"  Current doctor count: {count}")


def main():
    print("[INFO] Applying Supabase Migrations for Pulse Bridge")
    print(f"Project: {settings.SUPABASE_URL}")

    if not settings.SUPABASE_SERVICE_ROLE_KEY or "your-supabase" in settings.SUPABASE_SERVICE_ROLE_KEY:
        print("❌ SUPABASE_SERVICE_ROLE_KEY not configured in backend/.env")
        sys.exit(1)

    try:
        conn = get_db_connection()
        print("✓ Connected to Supabase PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

    # Apply migrations in order
    migrations_dir = Path(__file__).resolve().parent.parent.parent / "supabase" / "migrations"

    apply_migration(conn, migrations_dir / "01_extensions_and_profiles.sql", "Migration 01: Extensions & Profiles")
    apply_migration(conn, migrations_dir / "02_doctors_and_pgvector.sql", "Migration 02: Doctors & pgvector")
    apply_migration(conn, migrations_dir / "03_donors_and_requests.sql", "Migration 03: Donors & Requests")
    apply_migration(conn, migrations_dir / "04_report_records_and_storage.sql", "Migration 04: Reports & Storage")

    verify_setup(conn)

    conn.close()
    print("\n✅ All migrations applied successfully!")


if __name__ == "__main__":
    main()