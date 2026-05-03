
"""
Seed module for populating initial database records.
Called during application startup (lifespan event in main.py).
"""

from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import ClauseType


def seed_clause_types() -> None:
    """
    Populates the clause_types table with default values if it's empty.
    
    Steps:
    1. Open a database session
    2. Check if any clause types already exist
    3. If table is empty, insert default clause types
    4. Commit transaction and close session
    
    This function is idempotent - safe to call multiple times.
    It only inserts data if the table is empty.
    """
    db: Session = SessionLocal()
    
    try:
        # Step 1: Check if clause types already exist
        existing_count = db.query(ClauseType).count()
        
        if existing_count > 0:
            # Table already has data, skip seeding
            print(f"✓ Clause types already seeded ({existing_count} types found)")
            return
        
        # Step 2: Define default clause types
        # Each clause type has a name and color (hex format)
        # Colors should be distinct and visually accessible
        default_clause_types = [
            ClauseType(name="Confidentiality", color="#1ABC9C"),     # Turquoise
            ClauseType(name="Termination for Convenience", color="#E74C3C"),          # Red
            ClauseType(name="Limitation of Liability", color="#F39C12"),            # Orange
            ClauseType(name="Payment Terms", color="#3498DB"),        # Blue
            ClauseType(name="Governing Law", color="#9B59B6"),        # Purple
            ClauseType(name="Indemnification", color="#E67E22"),      # Dark Orange
            ClauseType(name="Intellectual Property", color="#16A085"), # Dark Turquoise
            ClauseType(name="Force Majeure", color="#95A5A6"),        # Gray
            ClauseType(name="Warranties", color="#27AE60"),           # Green
            ClauseType(name="Non-Compete", color="#C0392B"),          # Dark Red
        ]
        
        # Step 3: Bulk insert all clause types
        db.add_all(default_clause_types)
        
        # Step 4: Commit the transaction
        db.commit()
        
        print(f"✓ Seeded {len(default_clause_types)} default clause types")
        
    except Exception as e:
        # Rollback on error to maintain database consistency
        db.rollback()
        print(f"✗ Error seeding clause types: {e}")
        raise
    
    finally:
        # Step 5: Always close the database session
        db.close()
