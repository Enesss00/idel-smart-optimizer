from passlib.context import CryptContext
from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from database import SessionLocal, User

# Configuration pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password):
    """Transforme un mot de passe clair en hash sécurisé."""
    return pwd_context.hash(password)

def verify_api_key(api_key: str = Security(api_key_header), db: Session = Depends(get_db)):
    """Vérifie si la clé API existe et si l'abonnement est actif."""
    user = db.query(User).filter(User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Clé API invalide.")
    if not user.is_active:
        raise HTTPException(status_code=402, detail="Paiement requis : abonnement suspendu.")
    return user