from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from models.user import User
from core.security import hash_password, verify_password, create_access_token

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest):
    existing = await User.find_one(User.email == body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )

    user = User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password)
    )
    await user.insert()

    token = create_access_token(str(user.id))
    return AuthResponse(
        access_token=token,
        user={"id": str(user.id), "email": user.email, "name": user.name}
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    user = await User.find_one(User.email == body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    token = create_access_token(str(user.id))
    return AuthResponse(
        access_token=token,
        user={"id": str(user.id), "email": user.email, "name": user.name}
    )


@router.get("/me")
async def me(user: User = None):
    # Protected via dependency in calling code — returns current user info
    return {"id": str(user.id), "email": user.email, "name": user.name}
