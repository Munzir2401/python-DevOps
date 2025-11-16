from sqlalchemy.orm import Session
from typing import Optional
import logging
import models, schemas

# Configure logger for this module
logger = logging.getLogger(__name__)

def get_items(db: Session) -> list[models.Item]:
    return db.query(models.Item).all()

def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    # ItemBase enforces non-null description via validator (coerces None to "")
    # So item.description is guaranteed to be a string
    db_item = models.Item(name=item.name, description=item.description)
    db.add(db_item)
    try:
        db.commit()
        db.refresh(db_item)
    except Exception:
        db.rollback()
        logger.exception("Database error occurred while creating item")
        raise Exception("Failed to create item")
    return db_item

def update_item(db: Session, item_id: int, item: schemas.ItemUpdate) -> Optional[models.Item]:
    """
    Update an item by ID.
    
    Returns:
        models.Item: The updated item
        None: If item not found
    
    Raises:
        Exception: If database operation fails
    """
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        return None

    try:
        # Only update fields that are provided (not None)
        if item.name is not None:
            db_item.name = item.name
        if item.description is not None:
            db_item.description = item.description

        db.commit()
        db.refresh(db_item)
    except Exception:
        db.rollback()
        logger.exception("Database error occurred while updating item with id=%s", item_id)
        raise Exception("Failed to update item")
    return db_item

def delete_item(db: Session, item_id: int) -> Optional[models.Item]:
    """
    Delete an item by ID.
    
    Returns:
        models.Item: The deleted item (before deletion)
        None: If item not found
    
    Raises:
        Exception: If database operation fails
    """
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        return None

    try:
        db.delete(db_item)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Database error occurred while deleting item with id=%s", item_id)
        raise Exception("Failed to delete item")
    return db_item
