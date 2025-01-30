from sqlalchemy.orm import Session
from models import Partner, SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def add_partner(
        db: Session, user_id: int,
        partner_id: str,
        bitrix_contact_id: str
        ):
    db_partner = Partner(
        user_id=user_id,
        partner_id=partner_id,
        bitrix_contact_id=bitrix_contact_id
        )
    db.add(db_partner)
    db.commit()
    db.refresh(db_partner)
    return db_partner


def get_partner_id(db: Session, user_id: int):
    partner = db.query(Partner).filter(Partner.user_id == user_id).first()
    return partner.partner_id if partner else None
