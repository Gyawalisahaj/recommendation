from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlarchmy.orm import Sesson 
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

from . import models, database

SECRET_KEY = "SECRETkey123" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60




router = APIRouter()
pwd_context = CryptContext(schemes = ['bcrypt'], deprecated = 'auto')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db():
    db = database.SessonLocal()
    try :
        yield db
    finally:
        db.close()

class SignupRequest(BaseModel):
    first_name = str,
    last_name = str,
    email = EmailStr,
    password = str,
    conform_password

class LoginRequest(BaseModel):
    email = EmailStr,
    password = str

class UserResponse(BaseModel):
    id = int,
    frist_name = str,
    last_name = str, 
    email = EmailStr

    class config:
        orm_mode = True

class Token(BaseModel):
    access_token = str,
    token_type = str


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user_by_email(db, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user

@router.post("/signup", response_model = UserResponse)
def signup(request : SignupRequest, db : Session = Depends(get_db)):
    if request.password != request.conform_password:
        raise HTTPException(status_code=400, detail = 'Password doesmot match ...!')

    existing_user = db.query(models, User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered....!")

    hashed_password = password_context.hash(request.password)
    user = models.User(
        first_name = request.frist_name,
        last_name = request.last_name,
        email = request.email,
        hashed_password = hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model= UserResponse)
def login(request: LoginRequest, db: Sesson = Depends(get_db)):
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}
