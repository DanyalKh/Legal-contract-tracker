"""
Clauses/Labels Router
Endpoints for applying and removing clause type labels to sentences.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from typing import Optional
from datetime import datetime, timezone, timedelta

from ..database import get_db
from ..models import ClauseLabel, ClauseType, Sentence
from ..schemas import LabelCreate, LabelOut
# from ..services.analysis_service import analysis_service

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

@router.get("/sentences/label", status_code=status.HTTP_200_OK)
def labelled_count(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Return labeled sentences, optionally filtered by date range (YYYY-MM-DD).

    Query params:
    - start_date: inclusive (YYYY-MM-DD)
    - end_date: inclusive (YYYY-MM-DD)
    """
    query = db.query(ClauseLabel).options(
        selectinload(ClauseLabel.sentence),
        selectinload(ClauseLabel.clause_type),
    )

    # parse dates if provided — default to current UTC date when none provided
    try:
        if not start_date and not end_date:
            today = datetime.now(timezone.utc).date()
            sd = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
            ed = sd + timedelta(days=1)
            query = query.filter(ClauseLabel.labeled_at >= sd, ClauseLabel.labeled_at < ed)
        else:
            if start_date:
                sd = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                query = query.filter(ClauseLabel.labeled_at >= sd)
            if end_date:
                # make end_date inclusive by adding one day and using <
                ed = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
                query = query.filter(ClauseLabel.labeled_at < ed)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dates must be in YYYY-MM-DD format")

    results = query.order_by(ClauseLabel.labeled_at.desc()).all()

    # Build serializable response
    items = []
    for lbl in results:
        items.append({
            "id": lbl.id,
            "sentence_id": lbl.sentence_id,
            "sentence_text": getattr(lbl.sentence, 'text', None),
            "clause_type": getattr(lbl.clause_type, 'name', None),
            "source": lbl.source,
            "labeled_at": lbl.labeled_at.isoformat() if lbl.labeled_at else None,
        })

    return {"count": len(items), "labels": items}



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


# @router.post('/contracts/{contract_id}/auto-label')
# def auto_label_contract(contract_id: int, only_unlabeled: bool = True, db: Session = Depends(get_db)):
#     """Trigger AI auto-labeling for a contract's sentences."""
#     return analysis_service.auto_label_contract(db=db, contract_id=contract_id, only_unlabeled=only_unlabeled)