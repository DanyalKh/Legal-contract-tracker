"""
Contracts API endpoints
"""

from typing import Union, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload
from io import BytesIO

from ..database import get_db
from ..models import ClauseLabel, ClauseType, Contract, Sentence
from ..schemas import ContractListParams, ContractOut, ContractSummary, ContractsByClauseType
from ..utils.text_parser import parse_sentences

router = APIRouter(tags=["Contracts"])


@router.get("/contracts", response_model=Union[list[ContractSummary], list[ContractsByClauseType]])
def list_contracts(
    search: Optional[str] = None,
    clause_type_id: Optional[int] = None,
    group_by_clause: bool = False,
    db: Session = Depends(get_db)
):
    """
    List contracts with optional search and filtering.
    Use group_by_clause=true to group by clause types.
    """

    query = db.query(Contract)

    if search:
        query = query.filter(Contract.filename.ilike(f"%{search}%"))

    if clause_type_id:
        query = query.join(Contract.sentences).join(Sentence.label).filter(
            ClauseLabel.clause_type_id == clause_type_id
        ).distinct()
    
    if group_by_clause:
        from ..schemas import ContractsByClauseType

        clause_type_query = db.query(ClauseType)
        if clause_type_id:
            clause_type_query = clause_type_query.filter(ClauseType.id == clause_type_id)
        clause_types = clause_type_query.all()

        grouped_results = []
        for clause_type in clause_types:
            contracts_with_type = (
                db.query(Contract)
                .join(Contract.sentences)
                .join(Sentence.label)
                .filter(ClauseLabel.clause_type_id == clause_type.id)
                .distinct()
                .all()
            )

            contract_summaries = []
            for contract in contracts_with_type:
                total_sentences = len(contract.sentences)
                labeled_count = sum(1 for s in contract.sentences if s.label is not None)

                contract_summaries.append(ContractSummary(
                    id=contract.id,
                    filename=contract.filename,
                    uploaded_at=contract.uploaded_at,
                    total_sentences=total_sentences,
                    labeled_count=labeled_count
                ))

            grouped_results.append(ContractsByClauseType(
                clause_type=clause_type,
                contracts=contract_summaries
            ))

        return grouped_results

    contracts = query.order_by(Contract.uploaded_at.desc()).all()

    summaries = []
    for contract in contracts:
        total_sentences = len(contract.sentences)
        labeled_count = sum(1 for s in contract.sentences if s.label is not None)

        summaries.append(ContractSummary(
            id=contract.id,
            filename=contract.filename,
            uploaded_at=contract.uploaded_at,
            total_sentences=total_sentences,
            labeled_count=labeled_count
        ))

    return summaries



@router.get("/contracts/{contract_id}", response_model=ContractOut)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    """Get contract with all sentences and labels."""
    contract = (
        db.query(Contract)
        .options(
            selectinload(Contract.sentences)
            .selectinload(Sentence.label)
            .selectinload(ClauseLabel.clause_type)
        )
        .filter(Contract.id == contract_id)
        .first()
    )

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id {contract_id} not found"
        )

    return contract


@router.post("/contracts", response_model=ContractOut, status_code=status.HTTP_201_CREATED)
async def upload_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and parse a contract file."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    if not file.filename.lower().endswith((".txt", ".md")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .txt and .md files are supported"
        )

    try:
        content_bytes = await file.read()

        if not content_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        try:
            content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be UTF-8 encoded text"
            )

        sentence_texts = parse_sentences(content)

        if not sentence_texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No sentences found in file"
            )

        contract = Contract(
            filename=file.filename,
            content=content
        )

        db.add(contract)
        db.flush()

        for position, text in enumerate(sentence_texts, start=1):
            sentence = Sentence(
                contract_id=contract.id,
                text=text,
                position=position
            )
            db.add(sentence)

        db.commit()
        db.refresh(contract)

        return contract

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@router.delete("/contracts/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    """Delete a contract and all its sentences/labels."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id {contract_id} not found"
        )

    db.delete(contract)
    db.commit()


@router.get("/contracts/{contract_id}/download")
def download_contract(contract_id: int, db: Session = Depends(get_db)):
    """Download the original contract file."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id {contract_id} not found"
        )

    file_content = BytesIO(contract.content.encode('utf-8'))

    return StreamingResponse(
        file_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename={contract.filename}"
        }
    )