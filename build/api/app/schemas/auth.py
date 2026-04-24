from pydantic import BaseModel, EmailStr


class LoginInput(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    """Legacy body-token shape, kept for backwards compatibility if needed."""
    accessToken: str
    tokenType: str = "bearer"
    expiresIn: int
    refreshToken: str
