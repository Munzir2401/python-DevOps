"""
Two-Phase Migration: Backfill NULL descriptions and make column NOT NULL

This migration script handles the transition from nullable to non-nullable description column.

Phase 1: Backfill existing NULL description values with empty string
Phase 2: Alter the column to NOT NULL (run this separately after verifying Phase 1)

Usage:
    python migration_backfill_description.py
"""

import os
from sqlalchemy import text, create_engine
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(SQLALCHEMY_DATABASE_URL)


def phase_1_backfill_nulls():
    """Phase 1: Backfill existing NULL descriptions with empty string"""
    print("Phase 1: Starting backfill of NULL descriptions...")
    
    with engine.connect() as connection:
        try:
            # Backfill existing NULL descriptions with empty string
            result = connection.execute(
                text("UPDATE items SET description = '' WHERE description IS NULL")
            )
            connection.commit()
            print(f"✓ Phase 1 complete: {result.rowcount} rows updated")
            
            # Verify the backfill
            verify_result = connection.execute(
                text("SELECT COUNT(*) as null_count FROM items WHERE description IS NULL")
            )
            null_count = verify_result.scalar()
            print(f"✓ Verification: {null_count} NULL descriptions remaining")
            
            if null_count == 0:
                print("✓ All NULL descriptions have been backfilled!")
                return True
            else:
                print(f"✗ Warning: {null_count} NULL descriptions still exist")
                return False
        except Exception as e:
            print(f"✗ Phase 1 failed: {str(e)}")
            connection.rollback()
            return False


def phase_2_alter_column():
    """Phase 2: Alter the description column to NOT NULL"""
    print("\nPhase 2: Altering description column to NOT NULL...")
    
    with engine.connect() as connection:
        try:
            # Different ALTER syntax depending on database type
            db_url = SQLALCHEMY_DATABASE_URL.lower()
            
            if 'postgresql' in db_url:
                alter_sql = "ALTER TABLE items ALTER COLUMN description SET NOT NULL"
            elif 'mysql' in db_url:
                alter_sql = "ALTER TABLE items MODIFY COLUMN description VARCHAR(255) NOT NULL"
            elif 'sqlite' in db_url:
                # SQLite requires a more complex migration (recreate table)
                print("✗ SQLite detected: Manual migration required")
                print("  SQLite does not support ALTER COLUMN NOT NULL directly.")
                print("  Consider using Alembic for proper SQLite migrations.")
                return False
            else:
                print("✗ Unknown database type. Manual migration required.")
                return False
            
            connection.execute(text(alter_sql))
            connection.commit()
            print(f"✓ Phase 2 complete: description column is now NOT NULL")
            return True
        except Exception as e:
            print(f"✗ Phase 2 failed: {str(e)}")
            connection.rollback()
            return False


def verify_constraint():
    """Verify that the NOT NULL constraint is in place"""
    print("\nVerifying constraint...")
    
    with engine.connect() as connection:
        try:
            # Try to insert a row with NULL description (should fail)
            connection.execute(
                text("INSERT INTO items (name, description) VALUES ('test', NULL)")
            )
            print("✗ Constraint verification failed: NULL was accepted!")
            connection.rollback()
            return False
        except Exception as e:
            print(f"✓ Constraint verified: {type(e).__name__}")
            connection.rollback()
            return True


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION: Backfill descriptions and add NOT NULL")
    print("=" * 60)
    
    # Run Phase 1
    phase1_success = phase_1_backfill_nulls()
    
    if phase1_success:
        print("\n" + "=" * 60)
        print("Phase 1 PASSED")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run Phase 2: python migration_backfill_description.py --phase2")
        print("2. Or run full migration with: python migration_backfill_description.py --full")
    else:
        print("\n" + "=" * 60)
        print("Phase 1 FAILED - Fix the issues before proceeding")
        print("=" * 60)
        exit(1)


# Support for --phase2 and --full flags
if __name__ == "__main__":
    import sys
    
    if "--phase2" in sys.argv or "--full" in sys.argv:
        if "--full" in sys.argv and not phase1_success:
            print("Skipping Phase 2 because Phase 1 must complete first")
            exit(1)
        
        print("\nProceeding to Phase 2...")
        phase2_success = phase_2_alter_column()
        
        if phase2_success:
            verify_constraint()
            print("\n" + "=" * 60)
            print("MIGRATION COMPLETE")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("Phase 2 FAILED")
            print("=" * 60)
            exit(1)
