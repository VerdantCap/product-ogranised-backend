from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List, Literal
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from enums import ItemSpace, ItemType, BillingPlan

# Base schemas for common fields
class TimestampedModel(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Auth related schemas
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
    # Profile fields
    address: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None
    languages: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    marketing_email: bool = False
    marketing_phone: bool = False

class CreateUserIn(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


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

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None
    languages: Optional[str] = None

class UserPreferencesUpdate(BaseModel):
    email_notification: Optional[bool] = None
    sms_notification: Optional[bool] = None
    push_notification: Optional[bool] = None
    marketing_email: Optional[bool] = None
    marketing_phone: Optional[bool] = None

class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    address: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    bio: Optional[str] = None
    languages: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    email_notification: bool = False
    sms_notification: bool = False
    push_notification: bool = False
    marketing_email: bool = False
    marketing_phone: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Workspace related schemas
class Workspace(BaseModel):
    id: str
    name: str
    owner_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    expires_at: Optional[datetime]
    spaces_order: List[ItemSpace]

class WorkspaceCreate(BaseModel):
    user_id: str
    plan: BillingPlan = BillingPlan.STANDARD
    name: str
    spaces_order: Optional[List[ItemSpace]]
    success_url: str
    cancel_url: str

class WorkspaceUpdate(BaseModel):
    name: Optional[str]
    spaces_order: Optional[List[ItemSpace]]
    cancelled_at: Optional[datetime]
    expires_at: Optional[datetime]

# File related schemas
class File(BaseModel):
    id: str
    workspace_id: str
    path: str
    type: str
    folder: Optional[str]
    category: Optional[str]

class FileCreate(BaseModel):
    workspace_id: str
    path: str
    type: str
    folder: Optional[str] = None
    category: Optional[str] = None

class FileUpdate(BaseModel):
    path: Optional[str] = None
    type: Optional[str] = None
    folder: Optional[str] = None
    category: Optional[str] = None

# Item related schemas
class Item(BaseModel):
    workspace_id: str
    owner_id: str
    space: ItemSpace
    type: ItemType
    title: str
    description: Optional[str]
    fields: Optional[dict]
    files: List[File]
    related_items: List["Item"] = []
    transports: List["Transport"] = []
    accommodations: List["Accommodation"] = []
    excursions: List["Excursion"] = []

class ItemCreate(BaseModel):
    workspace_id: str
    space: ItemSpace
    type: ItemType
    title: str
    description: Optional[str]
    fields: Optional[dict]

class ItemUpdate(BaseModel):
    space: Optional[ItemSpace]
    type: Optional[ItemType]
    title: Optional[str]
    description: Optional[str]
    fields: Optional[dict]

# Transport related schemas
class Transport(BaseModel):
    item_id: str
    type: str
    provider: str
    booking_reference: Optional[str] = None
    departure_location: str
    arrival_location: str
    departure_time: datetime
    arrival_time: datetime
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    item: Item

class TransportCreate(BaseModel):
    item_id: str
    type: str
    provider: str
    booking_reference: Optional[str] = None
    departure_location: str
    arrival_location: str
    departure_time: datetime
    arrival_time: datetime
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None

class TransportUpdate(BaseModel):
    type: Optional[str] = None
    provider: Optional[str] = None
    booking_reference: Optional[str] = None
    departure_location: Optional[str] = None
    arrival_location: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None

# Accommodation related schemas
class Accommodation(BaseModel):
    item_id: str
    type: str
    provider: str
    booking_ref: Optional[str]
    location: str
    departure_date: date
    arrival_date: date
    deposit_date: date
    total_cost: float
    notes: Optional[str]
    item: Item

class AccommodationCreate(BaseModel):
    item_id: str
    type: str
    provider: str
    booking_reference: Optional[str] = None
    location: str
    check_in: datetime
    check_out: datetime
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None

class AccommodationUpdate(BaseModel):
    type: Optional[str] = None
    provider: Optional[str] = None
    booking_reference: Optional[str] = None
    location: Optional[str] = None
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None

# Excursion related schemas
class Excursion(BaseModel):
    item_id: int
    type: str
    provider: str
    booking_ref: Optional[str]
    location: str
    start_time: datetime
    end_time: datetime
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    item: Item

class ExcursionCreate(BaseModel):
    item_id: int
    type: str
    provider: str
    booking_ref: Optional[str] = None
    location: str
    start_time: datetime
    end_time: datetime
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None

class ExcursionUpdate(BaseModel):
    type: Optional[str] = None
    provider: Optional[str] = None
    booking_ref: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    cost: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None

class Event(BaseModel):
    id: str
    workspace_id: str
    owner_id: str
    name: str
    description: Optional[str]
    start_at: str
    end_at: str
    lead: Optional[str] = None

class EventCreate(BaseModel):
    name: str
    description: Optional[str]
    start_at: str
    end_at: str
    lead: Optional[str] = None

class EventUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    start_at: Optional[str]
    end_at: Optional[str]
    lead: Optional[str]

class Task(BaseModel):
    id: str
    workspace_id: str
    owner_id: str
    assignee_id: str
    title: str
    description: Optional[str]
    due_at: Optional[datetime]
    completed_at: Optional[datetime]
    assignee: Optional[User]

class TaskCreate(BaseModel):
    workspace_id: str
    owner_id: str
    assignee_id: str
    title: str
    description: str
    due_at: Optional[datetime]

class TaskUpdate(BaseModel):
    workspace_id: str
    owner_id: str
    assignee_id: str
    title: str
    description: str
    due_at: Optional[datetime]
    completed_at: Optional[datetime]

class TaskResponse(BaseModel):
    id: str
    workspace_id: str
    owner_id: str
    assignee_id: str
    title: str
    description: Optional[str]
    due_at: Optional[datetime]
    completed_at: Optional[datetime]
    assignee: Optional[User]

# Activity related schemas
class Activity(BaseModel):
    type: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    details: Optional[dict] = None

class ActivityCreate(Activity):
    activity_type: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    details: Optional[dict] = None

class ActivityUpdate(Activity):
    pass

class ActivityResponse(Activity):
    id: str
    user_id: str
    workspace_id: str
    type: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime

    class Config:
        orm_mode = True
