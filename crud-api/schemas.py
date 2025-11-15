from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    """Update DTO - all fields optional for partial updates"""
    name: str | None = None
    description: str | None = None
    
    model_config = ConfigDict(extra='forbid')

class Item(ItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('description', mode='before')
    @classmethod
    def coerce_null_description(cls, v):
        """Handle existing NULL description values on read - coerce to empty string"""
        if v is None:
            return ""
        return v

