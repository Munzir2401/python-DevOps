from pydantic import BaseModel, field_validator, ConfigDict

class ItemBase(BaseModel):
    name: str
    description: str  # Non-optional: enforced at write time
    
    @field_validator('description', mode='before')
    @classmethod
    def coerce_null_description_on_write(cls, v):
        """
        Enforce non-null description at write time.
        Coerce None to empty string to handle optional input gracefully,
        but prevent new NULL descriptions from being stored.
        """
        if v is None:
            return ""
        if not isinstance(v, str):
            raise ValueError("description must be a string")
        return v

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    """Update DTO - all fields optional for partial updates"""
    name: str | None = None
    description: str | None = None
    
    model_config = ConfigDict(extra='forbid')
    
    @field_validator('description', mode='before')
    @classmethod
    def coerce_null_description_on_write(cls, v):
        """
        Coerce None to empty string on updates.
        If description is provided but None, convert to empty string.
        If None is passed, it means "don't update" so leave as None.
        """
        if v is None:
            return None  # Explicit None = don't update this field
        if not isinstance(v, str):
            raise ValueError("description must be a string")
        return v

class Item(ItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
    
    # Note: Read-time coercion removed. Legacy NULL descriptions from DB
    # should be handled via migration (migration_backfill_description.py)
    # or at the CRUD layer when mapping DB rows to schema.
