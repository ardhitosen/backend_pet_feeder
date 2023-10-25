from fastapi import FastAPI, HTTPException, Depends, status
from datetime import time
from pydantic import BaseModel
from typing import Annotated, Optional, List
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

app = FastAPI()
models.Base.metadata.create_all(bind = engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class UserCreate(BaseModel):
    nama: str
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
    tipe_hewan: str
    ras_hewan: str
    umur: int
    jam_makan: Optional[time] = None

class updateJamMakan(BaseModel):
    jam_makan: time

class PetCreate(PetBase):
    pass

class Pet(PetBase):
    pet_id: int
    device_id: int

    class Config:
        orm_mode = True

class DeviceBase(BaseModel):
    model: str

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


################ Bagian User ################
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


################ Bagian Pet ################
@app.post("/pet/{pet_id}", status_code = status.HTTP_201_CREATED)
async def create_pet(pets: PetBase, pet_id: int, db: db_dependency):
    porsi_makan= pets.berat/1000 * 30
    db_pet = models.Pet(**pets.dict(), pet_id = pet_id, porsi_makan = porsi_makan)
    db.add(db_pet)
    db.commit()


@app.get("/pet/{device_id}", status_code=status.HTTP_200_OK)
async def get_pet(device_id: int, db: db_dependency):
    pet = db.query(models.Pet).filter(models.Pet.device_id == device_id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet


@app.get("/pet/{pet_id}/feedtime",status_code=status.HTTP_200_OK, response_model=str)
async def get_feedTime(pet_id: int,db: db_dependency):
    feedTime = db.query(models.Pet.jam_makan).filter(models.Pet.pet_id == pet_id).first()
    if feedTime is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    jam_makan = feedTime[0]

    if jam_makan is not None:
        # Convert the time to a string in "HH:MM:SS" format
        jam_makan_str = jam_makan.strftime("%H:%M:%S")
        return jam_makan_str
    else:
        return None
    
    
@app.get("/pet/{device_id}/foodporsion", status_code=status.HTTP_200_OK)
async def get_foodPorsion(device_id: int, db:db_dependency):
    pet = db.query(models.Pet.porsi_makan).filter(models.Pet.device_id == device_id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    porsi = pet[0]
    return porsi    

    
@app.put("/pet/edit/{pet_id}", status_code = status.HTTP_202_ACCEPTED)
async def edit_pet(pet_update: PetBase, pet_id: int, db: db_dependency):
    pet = db.query(models.Pet).filter(models.Pet.pet_id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    new_porsi_makan = pet_update.berat/1000*30
    for field, value in pet_update.dict().items():
        setattr(pet, field, value)
    pet.porsi_makan = new_porsi_makan
    db.commit()
    db.close()
    return {"message": "pet updated successfully"}


@app.put("/pet/edit/jam_makan/{pet_id}", status_code= status.HTTP_202_ACCEPTED)
async def edit_jam_makan(update_jamMakan: updateJamMakan, pet_id: int, db: db_dependency):
    pet = db.query(models.Pet).filter(models.Pet.pet_id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet not found")
    pet.jam_makan = update_jamMakan.jam_makan.strftime("%H:%M:%S")
    db.commit()
    db.close()
    return {"message": "jam_makan updated successfully"}


################ Bagian Device ################
@app.get("/device/{user_id}",status_code=status.HTTP_200_OK)
async def get_devices(user_id: int,db: db_dependency):
    devices = db.query(models.Device).filter(models.Device.user_id == user_id).all()
    if devices is None:
        raise HTTPException(status_code=404, detail="Devices not found")
    return devices


@app.post("/device/{user_id}", status_code = status.HTTP_201_CREATED)
async def create_device(devices: DeviceCreate, user_id: int, db: db_dependency):
    db_device = models.Device(**devices.dict(), user_id = user_id)
    db.add(db_device)
    db.commit()