from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from .config import settings

# pbkdf2_sha256 e' puro Python: nessuna dipendenza nativa da compilare.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(user_id) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_ttl_min)
    payload = {"sub": str(user_id), "exp": exp}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
