"""Test Parameter Pydantic schemas (§2.1 / §2.3)."""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
import uuid


class TestParameterBase(BaseModel):
    parameter_name: str = Field(..., max_length=120)
    unit: Optional[str] = Field(None, max_length=20)
    input_type: str = Field("numeric", pattern="^(numeric|text|dropdown|select)$")
    dropdown_options: Optional[List[str]] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    reference_text: Optional[str] = Field(None, max_length=200)
    applicable_gender: str = Field("all", pattern="^(all|male|female)$")
    display_order: int = Field(1, ge=1, le=1000)


class TestParameterCreate(TestParameterBase):
    pass


class TestParameterUpdate(BaseModel):
    parameter_name: Optional[str] = Field(None, max_length=120)
    unit: Optional[str] = Field(None, max_length=20)
    input_type: Optional[str] = Field(None, pattern="^(numeric|text|dropdown|select)$")
    dropdown_options: Optional[List[str]] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    reference_text: Optional[str] = Field(None, max_length=200)
    applicable_gender: Optional[str] = Field(None, pattern="^(all|male|female)$")
    display_order: Optional[int] = Field(None, ge=1, le=1000)


class TestParameterBulkSave(BaseModel):
    parameters: List[TestParameterCreate]


class TestParameterResponse(TestParameterBase):
    id: uuid.UUID
    test_id: uuid.UUID

    class Config:
        from_attributes = True
