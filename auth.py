from fastapi import FastAPI, HTTPException, Depends, status, APIRouter
from datetime import time, timedelta, datetime
from pydantic import BaseModel
from typing import Annotated, Optional, List
from models import User
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from starlette import status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm,OAuth2AuthorizationCodeBearer, OAuth2PasswordBearer
from jose import jwt, JWTError

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = '9BBC40E6CA02696E20183976E4FBECD7007F2004664B5C3298D7E741BC7112C6'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class CreateUserRequest(BaseModel):
    name: str
    password: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request:CreateUserRequest):
    create_user_model = User(
        name = create_user_request.name,
        password = bcrypt_context.hash(create_user_request.password),
        full_name = create_user_request.full_name
    )
    
    db.add(create_user_model)
    db.commit()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')
    token = create_access_token(user.name, user.user_id, timedelta(minutes=20))

    return {'access_token': token, 'token_type': 'bearer'}

def authenticate_user(name: str, password: str, db):
    user = db.query(User).filter(User.name == name).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user

def create_access_token(name: str, user_id: int, expires_delta: timedelta):
    encode = {'id': user_id, 'name': name }
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)