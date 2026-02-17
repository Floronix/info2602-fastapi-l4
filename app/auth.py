from pwdlib import PasswordHash
from app.models import *
from app.database import get_session
from sqlmodel import select
from datetime import timedelta, datetime, timezone
from app.database import SessionDep
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, Any
from fastapi import Depends, HTTPException, status, APIRouter
import jwt
from jwt.exceptions import InvalidTokenError


SECRET_KEY = "ThisIsAnExampleOfWhatNotToUseAsTheSecretKeyIRL"
ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Converts plaintext password to encrypted password
def encrypt_password(password:str):
    return password_hash.hash(password)

# Verifies if a plaintext password, when encrypted, gives the same output as the expected encrypted password
def verify_password(plaintext_password:str, encrypted_password):
    return password_hash.verify(password=plaintext_password, hash=encrypted_password)

# This takes some information and converts it into a JWT
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Gets the current user who is making the request
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db:SessionDep)->User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub",None)
        user_role: Any | None = payload.get("role", None)
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = db.get(RegularUser, user_id)
    if user is None:
        raise credentials_exception
    return user

auth_router = APIRouter(tags=["Authentication"])


@auth_router.get("/identify", response_model=UserResponse)
def get_user_by_id(db: SessionDep, user:AuthDep):
    return user

AuthDep = Annotated[User, Depends(get_current_user)]

