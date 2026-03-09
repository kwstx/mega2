import os
import secrets
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from datetime import datetime

# Simple scaling: SQLite for now, but configured via DATABASE_URL to allow PostgreSQL/MySQL
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./cloud_backend.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# AES-256 Encryption Setup
# In production, this key must be securely loaded from an environment variable or KMS
encryption_key_hex = os.environ.get("AES_ENCRYPTION_KEY")
if not encryption_key_hex:
    # Generate a random 256-bit (32 byte) key for AES-256 if not provided
    encryption_key = AESGCM.generate_key(bit_length=256)
    encryption_key_hex = encryption_key.hex()
    os.environ["AES_ENCRYPTION_KEY"] = encryption_key_hex
else:
    encryption_key = bytes.fromhex(encryption_key_hex)

aesgcm = AESGCM(encryption_key)

def encrypt_data(data: str) -> str:
    if not data:
        return data
    nonce = os.urandom(12) # GCM standard nonce size
    ciphertext = aesgcm.encrypt(nonce, data.encode('utf-8'), None)
    return (nonce + ciphertext).hex()

def decrypt_data(encrypted_hex: str) -> str:
    if not encrypted_hex:
        return encrypted_hex
    try:
        data_bytes = bytes.fromhex(encrypted_hex)
        nonce = data_bytes[:12]
        ciphertext = data_bytes[12:]
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    except Exception as e:
        print(f"Decryption error: {e}")
        return ""

# Database Models
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    # Storing email encrypted (AES-256 at rest)
    encrypted_email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class DeviceState(Base):
    __tablename__ = "device_states"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    name = Column(String, default="Smart Device")
    energy_needed_kwh = Column(Float, default=40.0)
    ready_by_time = Column(String, default="07:00")
    manual_override = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
