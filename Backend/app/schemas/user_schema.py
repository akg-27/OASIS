from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    contact_no: str | None = None
    full_name: str
    role: str
    drive_link: str | None = None

class LoginRequest(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str

class UserPublic(BaseModel):
    id: str
    username: str
    email: str
    contact_no: str | None = None
    full_name: str | None = None
    role: str
    drive_link: str | None = None

class TokenResponse(BaseModel):
    status: str
    access_token: str
    token_type: str
    user: UserPublic | None
