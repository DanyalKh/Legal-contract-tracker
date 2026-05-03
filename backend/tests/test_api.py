"""
API Integration Tests
Tests all endpoints including contract upload, labeling, filtering, and error handling.
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import ClauseType

# Test database setup (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Create test database tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def seed_clause_types(setup_database):
    """Seed test database with clause types."""
    db = TestingSessionLocal()
    try:
        clause_types = [
            ClauseType(id=1, name="Confidentiality", color="#1ABC9C"),
            ClauseType(id=2, name="Termination", color="#E74C3C"),
            ClauseType(id=3, name="Liability", color="#F39C12"),
        ]
        db.add_all(clause_types)
        db.commit()
    finally:
        db.close()
    return clause_types


# =============================================================================
# Clause Types Tests
# =============================================================================

def test_get_clause_types(seed_clause_types):
    """Test GET /api/clause-types returns all clause types."""
    response = client.get("/api/clause-types")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Confidentiality"
    assert data[0]["color"] == "#1ABC9C"


def test_create_clause_type(setup_database):
    """Test POST /api/clause-types creates new clause type."""
    response = client.post(
        "/api/clause-types",
        json={"name": "Data Privacy", "color": "#9B59B6"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Data Privacy"
    assert data["color"] == "#9B59B6"
    assert "id" in data


def test_create_duplicate_clause_type(seed_clause_types):
    """Test POST /api/clause-types with duplicate name returns 400."""
    response = client.post(
        "/api/clause-types",
        json={"name": "Confidentiality", "color": "#FF0000"}
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_clause_type_invalid_color(setup_database):
    """Test POST /api/clause-types with invalid color format."""
    response = client.post(
        "/api/clause-types",
        json={"name": "Test", "color": "invalid"}
    )
    
    assert response.status_code == 422  # Validation error


# =============================================================================
# Contract Tests
# =============================================================================

def test_upload_contract_success(seed_clause_types):
    """Test POST /api/contracts uploads and parses contract successfully."""
    file_content = "This is the first sentence. This is the second sentence."
    files = {
        "file": ("test_contract.txt", io.BytesIO(file_content.encode()), "text/plain")
    }
    
    response = client.post("/api/contracts", files=files)
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test_contract.txt"
    assert data["content"] == file_content
    assert len(data["sentences"]) == 2
    assert data["sentences"][0]["text"] == "This is the first sentence."
    assert data["sentences"][0]["position"] == 1


def test_upload_contract_invalid_file_type(seed_clause_types):
    """Test POST /api/contracts rejects invalid file types."""
    files = {
        "file": ("test.pdf", io.BytesIO(b"fake pdf"), "application/pdf")
    }
    
    response = client.post("/api/contracts", files=files)
    
    assert response.status_code == 400
    assert "Only .txt and .md files" in response.json()["detail"]


def test_upload_empty_contract(seed_clause_types):
    """Test POST /api/contracts rejects empty files."""
    files = {
        "file": ("empty.txt", io.BytesIO(b""), "text/plain")
    }
    
    response = client.post("/api/contracts", files=files)
    
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_list_contracts(seed_clause_types):
    """Test GET /api/contracts returns contract list."""
    # Upload a contract first
    file_content = "This is the first sentence. This is the second sentence."
    files = {
        "file": ("test.txt", io.BytesIO(file_content.encode()), "text/plain")
    }
    client.post("/api/contracts", files=files)
    
    # List contracts
    response = client.get("/api/contracts")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["filename"] == "test.txt"
    assert data[0]["total_sentences"] == 2
    assert data[0]["labeled_count"] == 0


def test_search_contracts(seed_clause_types):
    """Test GET /api/contracts with search filter."""
    # Upload two contracts
    files1 = {
        "file": ("nda_contract.txt", io.BytesIO(b"Test sentence."), "text/plain")
    }
    files2 = {
        "file": ("service_agreement.txt", io.BytesIO(b"Another test."), "text/plain")
    }
    client.post("/api/contracts", files=files1)
    client.post("/api/contracts", files=files2)
    
    # Search for "nda"
    response = client.get("/api/contracts?search=nda")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "nda" in data[0]["filename"].lower()


def test_get_contract_by_id(seed_clause_types):
    """Test GET /api/contracts/{id} returns full contract with sentences."""
    # Upload contract
    file_content = "Sentence one. Sentence two. Sentence three."
    files = {
        "file": ("test.txt", io.BytesIO(file_content.encode()), "text/plain")
    }
    upload_response = client.post("/api/contracts", files=files)
    contract_id = upload_response.json()["id"]
    
    # Get contract by ID
    response = client.get(f"/api/contracts/{contract_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == contract_id
    assert data["filename"] == "test.txt"
    assert len(data["sentences"]) == 3


def test_get_nonexistent_contract(setup_database):
    """Test GET /api/contracts/{id} with invalid ID returns 404."""
    response = client.get("/api/contracts/99999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_contract(seed_clause_types):
    """Test DELETE /api/contracts/{id} deletes contract."""
    # Upload contract
    files = {
        "file": ("test.txt", io.BytesIO(b"Test content."), "text/plain")
    }
    upload_response = client.post("/api/contracts", files=files)
    contract_id = upload_response.json()["id"]
    
    # Delete contract
    response = client.delete(f"/api/contracts/{contract_id}")
    
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f"/api/contracts/{contract_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_contract(setup_database):
    """Test DELETE /api/contracts/{id} with invalid ID returns 404."""
    response = client.delete("/api/contracts/99999")
    
    assert response.status_code == 404


# =============================================================================
# Sentence Labeling Tests
# =============================================================================

def test_label_sentence_success(seed_clause_types):
    """Test POST /api/sentences/{id}/label applies label to sentence."""
    # Upload contract
    files = {
        "file": ("test.txt", io.BytesIO(b"Test sentence."), "text/plain")
    }
    upload_response = client.post("/api/contracts", files=files)
    sentence_id = upload_response.json()["sentences"][0]["id"]
    
    # Apply label
    response = client.post(
        f"/api/sentences/{sentence_id}/label",
        json={"clause_type_id": 1}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["sentence_id"] == sentence_id
    assert data["clause_type_id"] == 1
    assert data["source"] == "manual"
    assert data["clause_type"]["name"] == "Confidentiality"


def test_label_sentence_replace_existing(seed_clause_types):
    """Test relabeling a sentence replaces the existing label."""
    # Upload contract and label sentence
    files = {
        "file": ("test.txt", io.BytesIO(b"Test sentence."), "text/plain")
    }
    upload_response = client.post("/api/contracts", files=files)
    sentence_id = upload_response.json()["sentences"][0]["id"]
    
    # Apply first label
    client.post(
        f"/api/sentences/{sentence_id}/label",
        json={"clause_type_id": 1}
    )
    
    # Apply second label (should replace first)
    response = client.post(
        f"/api/sentences/{sentence_id}/label",
        json={"clause_type_id": 2}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["clause_type_id"] == 2
    assert data["clause_type"]["name"] == "Termination"


def test_label_nonexistent_sentence(seed_clause_types):
    """Test POST /api/sentences/{id}/label with invalid sentence ID."""
    response = client.post(
        "/api/sentences/99999/label",
        json={"clause_type_id": 1}
    )
    
    assert response.status_code == 404
    assert "sentence" in response.json()["detail"].lower()


def test_label_with_invalid_clause_type(seed_clause_types):
    """Test POST /api/sentences/{id}/label with invalid clause type ID."""
    # Upload contract
    files = {
        "file": ("test.txt", io.BytesIO(b"Test sentence."), "text/plain")
    }
    upload_response = client.post("/api/contracts", files=files)
    sentence_id = upload_response.json()["sentences"][0]["id"]
    
    # Try to label with non-existent clause type
    response = client.post(
        f"/api/sentences/{sentence_id}/label",
        json={"clause_type_id": 99999}
    )
    
    assert response.status_code == 404
    assert "clause type" in response.json()["detail"].lower()


def test_remove_label_success(seed_clause_types):
    """Test DELETE /api/sentences/{id}/label removes label."""
    # Upload contract and label sentence
    files = {
        "file": ("test.txt", io.BytesIO(b"Test sentence."), "text/plain")
    }
    upload_response = client.post("/api/contracts", files=files)
    sentence_id = upload_response.json()["sentences"][0]["id"]
    
    client.post(
        f"/api/sentences/{sentence_id}/label",
        json={"clause_type_id": 1}
    )
    
    # Remove label
    response = client.delete(f"/api/sentences/{sentence_id}/label")
    
    assert response.status_code == 204


def test_remove_nonexistent_label(seed_clause_types):
    """Test DELETE /api/sentences/{id}/label when no label exists."""
    # Upload contract (no label)
    files = {
        "file": ("test.txt", io.BytesIO(b"Test sentence."), "text/plain")
    }
    upload_response = client.post("/api/contracts", files=files)
    sentence_id = upload_response.json()["sentences"][0]["id"]
    
    # Try to remove non-existent label
    response = client.delete(f"/api/sentences/{sentence_id}/label")
    
    assert response.status_code == 404
    assert "no label" in response.json()["detail"].lower()


# =============================================================================
# Integration Tests (End-to-End)
# =============================================================================

def test_full_contract_workflow(seed_clause_types):
    """Test complete workflow: upload → label → filter → delete."""
    # 1. Upload contract
    file_content = "This is confidential. This agreement may be terminated."
    files = {
        "file": ("nda.txt", io.BytesIO(file_content.encode()), "text/plain")
    }
    upload_response = client.post("/api/contracts", files=files)
    assert upload_response.status_code == 201
    
    contract_id = upload_response.json()["id"]
    sentences = upload_response.json()["sentences"]
    
    # 2. Label sentences
    client.post(
        f"/api/sentences/{sentences[0]['id']}/label",
        json={"clause_type_id": 1}  # Confidentiality
    )
    client.post(
        f"/api/sentences/{sentences[1]['id']}/label",
        json={"clause_type_id": 2}  # Termination
    )
    
    # 3. Verify labels in contract
    get_response = client.get(f"/api/contracts/{contract_id}")
    assert get_response.status_code == 200
    labeled_sentences = get_response.json()["sentences"]
    assert labeled_sentences[0]["label"]["clause_type"]["name"] == "Confidentiality"
    assert labeled_sentences[1]["label"]["clause_type"]["name"] == "Termination"
    
    # 4. Filter by clause type
    filter_response = client.get("/api/contracts?clause_type_id=1")
    assert filter_response.status_code == 200
    assert len(filter_response.json()) == 1
    
    # 5. Delete contract
    delete_response = client.delete(f"/api/contracts/{contract_id}")
    assert delete_response.status_code == 204


def test_labeled_count_accuracy(seed_clause_types):
    """Test that labeled_count in contract summary is accurate."""
    # Upload contract with 3 sentences
    file_content = "First sentence. Second sentence. Third sentence."
    files = {
        "file": ("test.txt", io.BytesIO(file_content.encode()), "text/plain")
    }
    upload_response = client.post("/api/contracts", files=files)
    contract_id = upload_response.json()["id"]
    sentences = upload_response.json()["sentences"]
    
    # Label 2 out of 3 sentences
    client.post(f"/api/sentences/{sentences[0]['id']}/label", json={"clause_type_id": 1})
    client.post(f"/api/sentences/{sentences[1]['id']}/label", json={"clause_type_id": 2})
    
    # Check contract summary
    list_response = client.get("/api/contracts")
    summary = list_response.json()[0]
    
    assert summary["total_sentences"] == 3
    assert summary["labeled_count"] == 2


def test_filter_contracts_by_clause_type(seed_clause_types):
    """Test GET /api/contracts?clause_type_id filters contracts correctly."""
    # Upload two contracts
    files1 = {
        "file": ("contract1.txt", io.BytesIO(b"Confidential information."), "text/plain")
    }
    files2 = {
        "file": ("contract2.txt", io.BytesIO(b"Regular agreement."), "text/plain")
    }
    client.post("/api/contracts", files=files1)
    client.post("/api/contracts", files=files2)

    # Get contract IDs and label one sentence in first contract
    list_response = client.get("/api/contracts")
    contracts = list_response.json()
    contract1_id = contracts[0]["id"]
    contract2_id = contracts[1]["id"]

    # Label sentence in contract1 with clause type 1 (Confidentiality)
    contract1_response = client.get(f"/api/contracts/{contract1_id}")
    sentence_id = contract1_response.json()["sentences"][0]["id"]
    client.post(f"/api/sentences/{sentence_id}/label", json={"clause_type_id": 1})

    # Filter by clause type 1 - should return contract1
    filter_response = client.get("/api/contracts?clause_type_id=1")
    assert filter_response.status_code == 200
    filtered_contracts = filter_response.json()
    assert len(filtered_contracts) == 1
    assert filtered_contracts[0]["id"] == contract1_id

    # Filter by clause type 2 - should return no contracts
    filter_response2 = client.get("/api/contracts?clause_type_id=2")
    assert filter_response2.status_code == 200
    assert len(filter_response2.json()) == 0


def test_group_contracts_by_clause_type(seed_clause_types):
    """Test GET /api/contracts?group_by_clause groups contracts by clause type."""
    # Upload contracts and label them with different clause types
    files1 = {
        "file": ("nda.txt", io.BytesIO(b"Confidential agreement."), "text/plain")
    }
    files2 = {
        "file": ("service.txt", io.BytesIO(b"Service termination."), "text/plain")
    }
    files3 = {
        "file": ("liability.txt", io.BytesIO(b"Liability clause."), "text/plain")
    }

    client.post("/api/contracts", files=files1)
    client.post("/api/contracts", files=files2)
    client.post("/api/contracts", files=files3)

    # Get contract IDs and label sentences
    list_response = client.get("/api/contracts")
    contracts = list_response.json()

    # Label each contract with different clause types
    for i, contract in enumerate(contracts):
        contract_response = client.get(f"/api/contracts/{contract['id']}")
        sentence_id = contract_response.json()["sentences"][0]["id"]
        client.post(f"/api/sentences/{sentence_id}/label", json={"clause_type_id": i + 1})

    # Group by clause type
    group_response = client.get("/api/contracts?group_by_clause=true")
    assert group_response.status_code == 200
    grouped_data = group_response.json()

    # Should have 3 groups (all clause types, even those without contracts)
    assert len(grouped_data) == 3

    # Each group should have the correct structure
    for group in grouped_data:
        assert "clause_type" in group
        assert "contracts" in group
        # Only the first clause type should have contracts (since we only labeled with type 1)
        if group["clause_type"]["id"] == 1:
            assert len(group["contracts"]) == 1
        else:
            assert len(group["contracts"]) == 0
        assert group["clause_type"]["id"] in [1, 2, 3]


def test_group_contracts_empty_groups_filtered(seed_clause_types):
    """Test that all clause types are included in grouped view, even with no contracts."""
    # Only create contracts for some clause types
    files = {
        "file": ("test.txt", io.BytesIO(b"Test sentence."), "text/plain")
    }
    client.post("/api/contracts", files=files)

    # Label with clause type 1 only
    list_response = client.get("/api/contracts")
    contract = list_response.json()[0]
    contract_response = client.get(f"/api/contracts/{contract['id']}")
    sentence_id = contract_response.json()["sentences"][0]["id"]
    client.post(f"/api/sentences/{sentence_id}/label", json={"clause_type_id": 1})

    # Group by clause type - should return all clause types
    group_response = client.get("/api/contracts?group_by_clause=true")
    grouped_data = group_response.json()

    assert len(grouped_data) == 3  # All clause types included
    for group in grouped_data:
        if group["clause_type"]["id"] == 1:
            assert len(group["contracts"]) == 1
        else:
            assert len(group["contracts"]) == 0
