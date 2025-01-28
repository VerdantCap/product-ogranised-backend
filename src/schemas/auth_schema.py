from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field, EmailStr

class User(BaseModel):
    name: str 
    email: EmailStr
    is_email_verified: bool = False
    google_sub: Optional[str] = None
    apple_sub: Optional[str] = None
    oauth_provider: Optional[Literal["google", "apple"]] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    email_notification: bool = False
    sms_notification: bool = False
    push_notification: bool = False
    active_workspace_id: Optional[str] = None
    
class CreateUserIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., max_length=100)

class OAuthUserIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    
    email: EmailStr
    name: str
    sub: str
    provider: Literal["google", "apple"]
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None

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
