from sqlalchemy.orm import Session
import models, schemas

def get_items(db: Session):
    return db.query(models.Item).all()

def create_item(db: Session, item: schemas.ItemCreate):
    # Ensure description is always provided (default to empty string if None)
    description = item.description if item.description is not None else ""
    db_item = models.Item(name=item.name, description=description)
    db.add(db_item)
    try:
        db.commit()
        db.refresh(db_item)
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to create item: {str(e)}")
    return db_item

def update_item(db: Session, item_id: int, item: schemas.ItemUpdate):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        return {"error": "Item not found"}

    try:
        # Only update fields that are provided (not None)
        if item.name is not None:
            db_item.name = item.name
        if item.description is not None:
            db_item.description = item.description

        db.commit()
        db.refresh(db_item)
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to update item: {str(e)}"}
    return db_item

def delete_item(db: Session, item_id: int):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        return {"error": "Item not found"}

    try:
        db.delete(db_item)
        db.commit()
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to delete item: {str(e)}"}
    return {"message": "Item deleted"}
