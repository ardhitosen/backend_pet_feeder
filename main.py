from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()
models.Base.metadata.create_all(bind = engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from pydantic import BaseModel


class UserCreate(BaseModel):
    nama: str
    device: str
    password: str
    jumlah_hewan: int

class User(UserCreate):
    user_id: int

    class Config:
        orm_mode = True

class UserCredentials(BaseModel):
    nama:str
    password:str

class PetBase(BaseModel):
    nama: str
    berat: int
    porsi_makan: int
    tipe_hewan: str
    ras_hewan: str
    umur: int

class PetCreate(PetBase):
    pass

class Pet(PetBase):
    pet_id: int
    user_id: int
    device_id: int

    class Config:
        orm_mode = True

class DeviceBase(BaseModel):
    models: str

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    device_id: int
    user_id: int

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@app.post("/user/", status_code = status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: db_dependency):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()

@app.post("/login")
def login_user(user: UserCredentials, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.nama == user.nama).first()
    if db_user is None or db_user.password != user.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return db_user

@app.get("/pets/{device_id}", status_code=status.HTTP_200_OK)
async def get_pet(device_id: int, db: db_dependency):
    pet = db.query(models.Pet).filter(models.Pet.device_id == device_id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet

@app.post("/devices/{user_id}",status_code=status.HTTP_200_OK)
async def get_devices(user_id: int,db: db_dependency):
    devices = db.query(models.Device).filter(models.Device.user_id == user_id).all()
    if devices is None:
        raise HTTPException(status_code=404, detail="Devices not found")
    return devices
