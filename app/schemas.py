from datetime import datetime
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

class CriminalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str | None
    nickname: str
    reward: Decimal
    last_known_location: str
    difficulty: int
    armed: bool
    has_crew: bool
    escape_master: bool

class HuntCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criminal_id: Annotated[int, Field(strict=True, gt=0)]
    success: StrictBool
    notes: Annotated[str, Field(max_length=10000)]

class HuntPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: StrictBool | None = None
    notes: Annotated[str, Field(max_length=10000)] | None = None

    @model_validator(mode="after")
    def valid_patch(self):
        if not self.model_fields_set:
            raise ValueError("Provide success or notes")
        if any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError("Updated fields cannot be null")
        return self

class HuntOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    criminal_id: int
    success: bool
    notes: str
    created_at: datetime
