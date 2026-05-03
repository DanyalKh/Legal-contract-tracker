"""
Clause Types Router
Endpoints for managing clause type definitions (e.g., "Confidentiality", "Termination").
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ClauseType
from ..schemas import ClauseTypeOut, ClauseTypeCreate

router = APIRouter(tags=["Clause Types"])


@router.get("/clause-types", response_model=list[ClauseTypeOut])
def get_clause_types(db: Session = Depends(get_db)):
    """
    Retrieve all available clause types.
    
    Returns a list of clause types with id, name, and color.
    Used by the frontend to populate labeling dropdowns/buttons.
    """
    clause_types = db.query(ClauseType).order_by(ClauseType.name).all()
    return clause_types


@router.post("/clause-types", response_model=ClauseTypeOut, status_code=201)
def create_clause_type(clause_type: ClauseTypeCreate, db: Session = Depends(get_db)):
    """
    Create a new clause type (optional - for custom clause types).
    
    Request body:
    - name: Unique clause type name (e.g., "Data Privacy")
    - color: Hex color code (e.g., "#FF5733")
    
    Returns the created clause type with its assigned ID.
    """
    # Check if name already exists
    existing = db.query(ClauseType).filter(ClauseType.name == clause_type.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Clause type '{clause_type.name}' already exists"
        )
    
    # Create new clause type
    new_clause_type = ClauseType(
        name=clause_type.name,
        color=clause_type.color
    )
    
    db.add(new_clause_type)
    db.commit()
    db.refresh(new_clause_type)
    
    return new_clause_type
