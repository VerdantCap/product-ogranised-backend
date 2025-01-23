from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class CreateUserIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    password: str = Field(..., min_length=8)
    name: str = Field(..., max_length=100)

class AccessToken(BaseModel):
    access_token: str
    token_type: str


class ForgotPassword(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(..., pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

class VerifyOtpRequest(BaseModel):
    email: str
    otp: str

class ForgotPasswordReset(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    token: str
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password must contain at least 1 digit, 1 uppercase letter, 1 lowercase letter, and 1 special character.",
    )

class ReplacePassword(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    old_password: str
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password must contain at least 1 digit, 1 uppercase letter, 1 lowercase letter, and 1 special character.",
    )

class Profile(BaseModel):
    id: str
    unique_identifier: str
    name: Optional[str] = None
    introduction: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    languages: Optional[list[str]] = []
    summary: Optional[str] = None
    avatar_url: Optional[str] = None
    page_cover_url: Optional[str] = None