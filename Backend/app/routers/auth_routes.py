# app/routers/auth_routes.py
from fastapi import APIRouter
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt
import os

from app.database import supabase
from app.schemas.user_schema import UserCreate, LoginRequest, UserPublic, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

# ------------------------
# Password hashing
# ------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password) -> str:
    # ensure plain string
    password = str(password).strip()

    if not password or password.lower() == "none":
        raise ValueError("Invalid password")

    # bcrypt max 72 bytes → safe cutoff
    p_bytes = password.encode("utf-8", errors="ignore")
    if len(p_bytes) > 72:
        p_bytes = p_bytes[:72]
        password = p_bytes.decode("utf-8", errors="ignore")

    return pwd_context.hash(password)


def verify_password(plain, hashed: str) -> bool:
    plain = str(plain).strip()

    if not plain or plain.lower() == "none":
        return False

    # enforce bcrypt 72-byte rule
    p_bytes = plain.encode("utf-8", errors="ignore")
    if len(p_bytes) > 72:
        p_bytes = p_bytes[:72]
        plain = p_bytes.decode("utf-8", errors="ignore")

    return pwd_context.verify(plain, hashed)


# ------------------------
# JWT config & helpers
# ------------------------

SECRET_KEY = os.getenv("AUTH_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8   # 8 hrs

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ------------------------
# Role reference
# ------------------------
ROLE_LABELS = {
    "SC": "Scientist/Researcher",
    "DM": "Data Manager",
    "DC": "Data Collector",
    "DE": "Domain Expert",
    "DA": "Admin"
}


# ---------------------------------------------------------
# 1) REGISTER
# ---------------------------------------------------------
@router.post("/register")
def register_user(payload: UserCreate):

    existing = supabase.table("users").select("id").or_(
        f"username.eq.{payload.username},email.eq.{payload.email}"
    ).execute()

    if existing.data:
        return {"status": "error", "detail": "Username or email already exists"}

    try:
        hashed = hash_password(payload.password)
    except Exception as e:
        return {"status": "error", "detail": f"Password invalid: {str(e)}"}

    row = {
        "username": payload.username,
        "email": payload.email,
        "password_hash": hashed,
        "contact_no": payload.contact_no,
        "full_name": payload.full_name,
        "role": payload.role,
        "drive_link": payload.drive_link
    }

    res = supabase.table("users").insert(row).execute()
    if not res.data:
        return {"status": "error", "detail": "Insert failed"}

    user_row = res.data[0]
    user_public = UserPublic(
        id=user_row["id"],
        username=user_row["username"],
        email=user_row["email"],
        contact_no=user_row.get("contact_no"),
        full_name=user_row.get("full_name"),
        role=user_row["role"],
        drive_link=user_row.get("drive_link"),
    )

    return {"status": "ok", "user": user_public}


# ---------------------------------------------------------
# 2) LOGIN
# ---------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):

    if not payload.username and not payload.email:
        return {"status": "error", "access_token": "", "token_type": "bearer", "user": None}

    query = supabase.table("users").select("*")
    if payload.email:
        res = query.eq("email", payload.email).execute()
    else:
        res = query.eq("username", payload.username).execute()

    if not res.data:
        return {"status": "error", "access_token": "", "token_type": "bearer", "user": None}

    user_row = res.data[0]

    if not verify_password(payload.password, user_row["password_hash"]):
        return {"status": "error", "access_token": "", "token_type": "bearer", "user": None}

    token = create_access_token({
        "sub": user_row["id"],
        "role": user_row["role"],
        "username": user_row["username"]
    })

    user_public = UserPublic(
        id=user_row["id"],
        username=user_row["username"],
        email=user_row["email"],
        contact_no=user_row.get("contact_no"),
        full_name=user_row.get("full_name"),
        role=user_row["role"],
        drive_link=user_row.get("drive_link")
    )

    return TokenResponse(
        status="ok",
        access_token=token,
        token_type="bearer",
        user=user_public
    )
