"""
Database Connection Test Script

Tests PostgreSQL connection by:
1. Connecting to the database
2. Creating tables
3. Inserting test data
4. Retrieving and verifying data
5. Cleaning up test data

Run: python test_db_connection.py
"""

import sys
from datetime import datetime, timezone

# Add app to path
sys.path.insert(0, ".")

from app.database import SessionLocal, engine
from app.models import Base, ClauseType, Contract, Sentence, ClauseLabel


def test_connection():
    """Test basic database connection."""
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    
    try:
        # Test 1: Connection
        print("\n[1/5] Testing database connection...")
        db = SessionLocal()
        print("✓ Successfully connected to database")
        
        # Test 2: Create tables
        print("\n[2/5] Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created successfully")
        
        # Test 3: Insert test data
        print("\n[3/5] Inserting test data...")
        
        # Insert a clause type
        test_clause_type = ClauseType(
            name="Test Clause Type",
            color="#FF5733"
        )
        db.add(test_clause_type)
        db.commit()
        db.refresh(test_clause_type)
        print(f"✓ Inserted ClauseType: id={test_clause_type.id}, name='{test_clause_type.name}'")
        
        # Insert a contract
        test_contract = Contract(
            filename="test_contract.txt",
            content="This is a test contract. It contains multiple sentences.",
            uploaded_at=datetime.now(timezone.utc)
        )
        db.add(test_contract)
        db.commit()
        db.refresh(test_contract)
        print(f"✓ Inserted Contract: id={test_contract.id}, filename='{test_contract.filename}'")
        
        # Insert sentences
        sentence1 = Sentence(
            contract_id=test_contract.id,
            text="This is a test contract.",
            position=1
        )
        sentence2 = Sentence(
            contract_id=test_contract.id,
            text="It contains multiple sentences.",
            position=2
        )
        db.add_all([sentence1, sentence2])
        db.commit()
        db.refresh(sentence1)
        db.refresh(sentence2)
        print(f"✓ Inserted 2 Sentences: ids={sentence1.id}, {sentence2.id}")
        
        # Insert a label
        test_label = ClauseLabel(
            sentence_id=sentence1.id,
            clause_type_id=test_clause_type.id,
            source="manual",
            labeled_at=datetime.now(timezone.utc)
        )
        db.add(test_label)
        db.commit()
        db.refresh(test_label)
        print(f"✓ Inserted ClauseLabel: id={test_label.id}")
        
        # Test 4: Query data back
        print("\n[4/5] Querying data back...")
        
        # Query clause type
        queried_clause_type = db.query(ClauseType).filter(
            ClauseType.id == test_clause_type.id
        ).first()
        assert queried_clause_type is not None
        assert queried_clause_type.name == "Test Clause Type"
        print(f"✓ Retrieved ClauseType: {queried_clause_type.name}")
        
        # Query contract with relationships
        queried_contract = db.query(Contract).filter(
            Contract.id == test_contract.id
        ).first()
        assert queried_contract is not None
        assert len(queried_contract.sentences) == 2
        print(f"✓ Retrieved Contract: {queried_contract.filename} with {len(queried_contract.sentences)} sentences")
        
        # Query sentence with label
        queried_sentence = db.query(Sentence).filter(
            Sentence.id == sentence1.id
        ).first()
        assert queried_sentence is not None
        assert queried_sentence.label is not None
        assert queried_sentence.label.clause_type.name == "Test Clause Type"
        print(f"✓ Retrieved Sentence with label: '{queried_sentence.label.clause_type.name}'")
        
        # Test 5: Cleanup
        print("\n[5/5] Cleaning up test data...")
        db.delete(test_label)
        db.delete(sentence1)
        db.delete(sentence2)
        db.delete(test_contract)
        db.delete(test_clause_type)
        db.commit()
        print("✓ Test data cleaned up successfully")
        
        # Final verification
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nDatabase connection is working correctly.")
        print("You can now start your FastAPI application.")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify DATABASE_URL in app/database.py or environment variables")
        print("3. Ensure database 'clausetracker' exists")
        print("4. Check database credentials (username/password)")
        
        if db:
            db.rollback()
            db.close()
        
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
