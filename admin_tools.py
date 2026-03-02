from database import SessionLocal, User
from auth import get_password_hash
import uuid


def create_new_customer(email, password):
    """
    Crée un utilisateur en base de données et génère sa clé API.
    """
    db = SessionLocal()

    # On vérifie si l'utilisateur existe déjà
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        print(f"Erreur : L'utilisateur {email} existe déjà.")
        db.close()
        return

    # On hache le mot de passe pour la sécurité
    hashed = get_password_hash(password)

    # On crée l'entrée en base
    new_user = User(
        email=email,
        hashed_password=hashed,
        api_key=str(uuid.uuid4()),  # Génère une clé unique type : 550e8400...
        is_active=True
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print("--- CLIENT CREE AVEC SUCCES ---")
        print(f"Email: {new_user.email}")
        print(f"API KEY (A donner au client) : {new_user.api_key}")
        print("-------------------------------")
    except Exception as e:
        print(f"Erreur lors de la création : {e}")
    finally:
        db.close()


if __name__ == "__main__":
    # EXECUTION : Change l'email et le mot de passe ici pour ton premier client
    create_new_customer("contact@mon-entreprise.com", "password123")