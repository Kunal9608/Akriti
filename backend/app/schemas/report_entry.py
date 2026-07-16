"""Schemas for structured report result submission (§2.2 / §2.4)."""
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid


class ParameterResultItem(BaseModel):
    parameter_id: uuid.UUID
    entered_value: str = Field(..., max_length=100)
    is_abnormal: Optional[bool] = None
    interpretation_note: Optional[str] = None


class TestResultGroup(BaseModel):
    test_id: uuid.UUID
    results: List[ParameterResultItem]
    interpretation_note: Optional[str] = None


class ReportEntrySubmit(BaseModel):
    tests: List[TestResultGroup]
