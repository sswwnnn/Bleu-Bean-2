from datetime import timedelta, datetime
from typing import Annotated
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from database import get_db_connection
import aioodbc

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

# JWT config
SECRET_KEY = "15882913506880857248f72d1dbc38dd7d2f8f352786563ef5f23dc60987c632"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    userRole: str
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_user_from_db(username: str):
    """Fetch user details from database."""
    conn = await get_db_connection()
    cursor = await conn.cursor()
    await cursor.execute(
        '''SELECT Username, UserPassword, UserRole, isDisabled 
           FROM Users WHERE Username = ?''', (username,)
    )
    user_row = await cursor.fetchone()
    await cursor.close()
    await conn.close()

    if user_row:
        return UserInDB(
            username=user_row[0],
            hashed_password=user_row[1],
            userRole=user_row[2],
            disabled=bool(user_row[3])
        )
    return None

def get_password_hash(password: str):
    return pwd_context.hash(password)

# Ensure admin account exists on startup
async def create_admin_user():
    admin_user = await get_user_from_db('admin')
    if not admin_user:
        hashed_password = get_password_hash('admin123')
        conn = await get_db_connection()
        cursor = await conn.cursor()
        try:
            await cursor.execute(
                '''INSERT INTO Users (FullName, Username, Email, UserPassword, UserRole, isDisabled) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                ('Admin', 'admin', 'admin@bleu.com', hashed_password, 'admin', 0)
            )
            await conn.commit()
        except Exception as e:
            print("Error inserting admin user:", e)
        finally:
            await cursor.close()
            await conn.close()

@router.on_event("startup")
async def on_startup():
    await create_admin_user()

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

async def authenticate_user(username: str, password: str):
    user = await get_user_from_db(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credential_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception

    user = await get_user_from_db(token_data.username)
    if user is None:
        raise credential_exception

    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def role_required(required_roles: List[str]):
    async def role_checker(current_user: UserInDB = Depends(get_current_active_user)):
        if current_user.userRole not in required_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        return current_user
    return role_checker

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.userRole}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/admin-only-route", dependencies=[Depends(role_required(["admin"]))])
async def admin_only_route():
    return {"message": "This is restricted to admins only"}