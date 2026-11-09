from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User
from auth import verify_password, get_password_hash, create_access_token, decode_token
import os

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    full_name: str
    email: str


class GoogleAuthRequest(BaseModel):
    credential: str  # Google ID token


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = User(email=req.email, full_name=req.full_name,
                hashed_password=get_password_hash(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, token_type="bearer",
                         user_id=user.id, full_name=user.full_name, email=user.email)


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, token_type="bearer",
                         user_id=user.id, full_name=user.full_name, email=user.email)


@router.post("/google", response_model=TokenResponse)
def google_auth(req: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Verify Google ID token via Google tokeninfo endpoint and return a platform JWT."""
    import httpx

    client_id = os.getenv("GOOGLE_CLIENT_ID", "315896697942-i7gd2m70ge7vos2dl2hc2lcir231vo4d.apps.googleusercontent.com")

    try:
        r = httpx.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": req.credential},
            timeout=10
        )
        if r.status_code != 200:
            raise HTTPException(status_code=401, detail="Google token verification failed")

        idinfo = r.json()

        if idinfo.get("aud") != client_id:
            raise HTTPException(status_code=401, detail="Token audience mismatch")

        email = idinfo.get("email")
        full_name = idinfo.get("name", idinfo.get("given_name", "User"))

        if not email:
            raise HTTPException(status_code=400, detail="Could not retrieve email from Google token")

        if not idinfo.get("email_verified"):
            raise HTTPException(status_code=400, detail="Google email is not verified")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(os.urandom(32).hex())
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_access_token({"sub": user.email})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user_id=user.id,
            full_name=user.full_name,
            email=user.email
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google auth error: {str(e)}")


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email,
            "full_name": current_user.full_name, "created_at": current_user.created_at}
