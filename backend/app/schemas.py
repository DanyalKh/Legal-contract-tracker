import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class _OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Clause Types
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

class ClauseTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name required")
        return v


class ClauseTypeOut(_OrmBase):
    id: int
    name: str
    color: str


# Labels
class LabelCreate(BaseModel):
    clause_type_id: int = Field(..., gt=0)


class LabelOut(_OrmBase):
    id: int
    sentence_id: int
    clause_type_id: int
    source: Literal["manual", "ai"] = "manual"
    labeled_at: datetime
    clause_type: ClauseTypeOut


# Sentences
class SentenceOut(_OrmBase):
    id: int
    contract_id: int
    text: str
    position: int
    label: Optional[LabelOut] = None


# Contracts
class ContractCreate(BaseModel):
    filename: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)

    @field_validator("filename")
    @classmethod
    def allowed_extension(cls, v: str) -> str:
        if not v.lower().endswith((".txt", ".md")):
            raise ValueError("only .txt and .md files accepted")
        return v


class ContractOut(_OrmBase):
    id: int
    filename: str
    content: str
    uploaded_at: datetime
    sentences: list[SentenceOut] = []


class ContractSummary(_OrmBase):
    id: int
    filename: str
    uploaded_at: datetime
    total_sentences: int = Field(..., ge=0)
    labeled_count: int = Field(..., ge=0)

    @model_validator(mode="after")
    def labeled_not_exceed_total(self) -> "ContractSummary":
        if self.labeled_count > self.total_sentences:
            raise ValueError("labeled_count cannot exceed total_sentences")
        return self


class ContractsByClauseType(BaseModel):
    clause_type: ClauseTypeOut
    contracts: list[ContractSummary]


class ContractListParams(BaseModel):
    search: Optional[str] = Field(default=None, max_length=200)
    clause_type_id: Optional[int] = Field(default=None, gt=0)
    group_by_clause: bool = False