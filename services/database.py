from sqlalchemy.orm import Session
from models import Partner, SessionLocal


# Получение сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Добавление партнера в базу данных
def add_partner(db: Session, user_id: int, partner_id: str):
    db_partner = Partner(user_id=user_id, partner_id=partner_id)
    db.add(db_partner)
    db.commit()
    db.refresh(db_partner)
    return db_partner


# Получение ID партнера по user_id
def get_partner_id(db: Session, user_id: int):
    partner = db.query(Partner).filter(Partner.user_id == user_id).first()
    return partner.partner_id if partner else None
