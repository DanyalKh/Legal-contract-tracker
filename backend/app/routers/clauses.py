"""
Clauses/Labels Router
Endpoints for applying and removing clause type labels to sentences.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import ClauseLabel, ClauseType, Sentence
from ..schemas import LabelCreate, LabelOut

router = APIRouter(tags=["Labels"])


@router.post("/sentences/{sentence_id}/label", response_model=LabelOut, status_code=status.HTTP_201_CREATED)
def apply_label(
    sentence_id: int,
    label_data: LabelCreate,
    db: Session = Depends(get_db)
):
    """
    Apply a clause type label to a sentence.
    
    Path Parameter:
    - sentence_id: ID of the sentence to label
    
    Request Body:
    - clause_type_id: ID of the clause type to apply
    
    Process:
    1. Validate sentence exists
    2. Validate clause type exists
    3. Delete existing label if present (one label per sentence rule)
    4. Create new label with source="manual"
    
    Returns:
    - LabelOut with full clause_type details
    
    Raises:
    - 404: Sentence or clause type not found
    - 400: Validation error
    """
    # Step 1: Check if sentence exists
    sentence = db.query(Sentence).filter(Sentence.id == sentence_id).first()
    
    if not sentence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sentence with id {sentence_id} not found"
        )
    
    # Step 2: Check if clause type exists
    clause_type = db.query(ClauseType).filter(ClauseType.id == label_data.clause_type_id).first()
    
    if not clause_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clause type with id {label_data.clause_type_id} not found"
        )
    
    try:
        # Step 3: Delete existing label if present (enforce one label per sentence)
        existing_label = db.query(ClauseLabel).filter(ClauseLabel.sentence_id == sentence_id).first()
        
        if existing_label:
            db.delete(existing_label)
            db.flush()  # Ensure delete is processed before creating new label
        
        # Step 4: Create new label
        new_label = ClauseLabel(
            sentence_id=sentence_id,
            clause_type_id=label_data.clause_type_id,
            source="manual"  # Mark as manually applied (vs AI-generated)
        )
        
        db.add(new_label)
        db.commit()
        
        # Refresh to get the full object with relationships
        db.refresh(new_label)
        
        # Eager load clause_type to avoid additional query
        label_with_type = (
            db.query(ClauseLabel)
            .options(selectinload(ClauseLabel.clause_type))
            .filter(ClauseLabel.id == new_label.id)
            .first()
        )
        
        return label_with_type
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error applying label: {str(e)}"
        )


@router.delete("/sentences/{sentence_id}/label", status_code=status.HTTP_204_NO_CONTENT)
def remove_label(sentence_id: int, db: Session = Depends(get_db)):
    """
    Remove the clause type label from a sentence.
    
    Path Parameter:
    - sentence_id: ID of the sentence to unlabel
    
    Process:
    1. Validate sentence exists
    2. Find and delete the label
    
    Returns:
    - 204 No Content on success
    
    Raises:
    - 404: Sentence not found or sentence has no label
    """
    # Step 1: Check if sentence exists
    sentence = db.query(Sentence).filter(Sentence.id == sentence_id).first()
    
    if not sentence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sentence with id {sentence_id} not found"
        )
    
    # Step 2: Check if label exists
    label = db.query(ClauseLabel).filter(ClauseLabel.sentence_id == sentence_id).first()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No label found for sentence {sentence_id}"
        )
    
    try:
        # Step 3: Delete the label
        db.delete(label)
        db.commit()
        
        return None  # 204 No Content
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing label: {str(e)}"
        )