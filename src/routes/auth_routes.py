from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from app.dependencies import get_guest_user, get_authenticated_user
from app.middleware import MetricsMiddleware

app = APIRouter()

# Mock database
fake_users_db = {
    "user@example.com": {
        "email": "user@example.com",
        "password": "fakehashedpassword",
        "remember": True
    }
}

# Pydantic model for login form data
class LoginForm(BaseModel):
    email: str
    password: str
    remember: Optional[bool] = False

# Dependency to get the form data
def get_login_form(
    email: str = Form(...),
    password: str = Form(...),
    remember: Optional[bool] = Form(False)
) -> LoginForm:
    return LoginForm(email=email, password=password, remember=remember)

@app.post("/login")
async def login(form_data: LoginForm = Depends(get_login_form)):
    user = fake_users_db.get(form_data.email)
    if not user or user['password'] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Redirect to home on successful login
    response = RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)
    return response


guest_router = APIRouter(dependencies=[Depends(get_guest_user)])
auth_router = APIRouter(dependencies=[Depends(get_authenticated_user)])
router.middleware("http")(MetricsMiddleware)

@guest_router.get("/auth/login", tags=["auth"])
async def login():
    return {"message": "Login"}

@guest_router.get("/auth/register", tags=["auth"])
async def register():
    return {"message": "Register"}

@guest_router.get("/auth/forgot-password", tags=["auth"])
async def forgot_password():
    return {"message": "Forgot Password"}

@guest_router.get("/auth/forgot-password/reset/{token}", tags=["auth"])
async def password_reset(token: str):
    return {"token": token}

@guest_router.get("/auth/oauth/google", tags=["auth"])
async def oauth_google():
    return {"message": "OAuth Google"}

@guest_router.get("/auth/oauth/google/callback", tags=["auth"])
async def oauth_google_callback():
    return {"message": "OAuth Google Callback"}

@auth_router.post("/logout", tags=["auth"])
async def logout():
    return {"message": "Logout"}
