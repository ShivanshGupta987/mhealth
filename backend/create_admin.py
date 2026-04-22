# create_admin.py
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import POSTGRES_DB_URL
from app.models import Admins
import uuid

# Use bcrypt_sha256 to avoid bcrypt 72-byte limit (it pre-hashes with SHA256)
pwd_ctx = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

def get_password_hash(pw: str) -> str:
    # optional: enforce a max length for safety (bcrypt_sha256 already safe)
    if isinstance(pw, str):
        pw = pw.strip()
    if len(pw) == 0:
        raise ValueError("Password must not be empty")
    return pwd_ctx.hash(pw)

def main():
    # CHANGE THESE to your desired admin credentials
    email = "m.health@iitgn.ac.in"
    raw_password = "admin123"

    engine = create_engine(POSTGRES_DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Admins).filter(Admins.Email == email).first()
        if existing:
            print("Admin already exists:", existing.Email)
            return

        hashed = get_password_hash(raw_password)
        admin = Admins(Email=email, Password=hashed)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("Created admin:", admin.Email, "Admin_Id:", admin.Admin_Id)
    except Exception as e:
        db.rollback()
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    main()
