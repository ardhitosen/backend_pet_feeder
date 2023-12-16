from fastapi import FastAPI, HTTPException, Depends, status
from datetime import time, date, datetime
from pydantic import BaseModel
from typing import Annotated, Optional, List
import paho.mqtt.client as mqtt
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
import auth
from jose import JWTError, jwt
from auth import oauth2_bearer, SECRET_KEY, ALGORITHM

app = FastAPI()
app.include_router(auth.router)
models.Base.metadata.create_all(bind = engine)

mqtt_broker = "broker.emqx.io"
mqtt_port = 1883
mqtt_topic = "PETFEEDER012312333"

mqtt_client = mqtt.Client()

mqtt_client.connect(mqtt_broker, mqtt_port)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class UserCreate(BaseModel):
    name: str
    password: str
    full_name: str
    

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

class PetCreate(PetBase):
    pass

class Pet(PetBase):
    pet_id: int
    device_id: int

    class Config:
        orm_mode = True

class DeviceBase(BaseModel):
    mac_address: str
    model: str

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    device_id: int
    user_id: int
    mac_address: str

    class Config:
        orm_mode = True

class FeedingScheduleBase(BaseModel):
    jam_makan : time

class ScheduleCreate(FeedingScheduleBase):
    pass

class FeedingSchedule(FeedingScheduleBase):
    schedule_id: int
    pet_id: int

class FeedingHistoryBase(BaseModel):
    feeding_date: date
    dimakan: int

class CreateFeedingHistory(FeedingHistoryBase):
    pass
    
class FeedingHistory(FeedingHistoryBase):
    feeding_id: int
    schedule_id: int

    class Config:
        orm_mode = True

class InputBerat(BaseModel):
    berat: int

class Test(InputBerat):
    test_id: int

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
    db_user = db.query(models.User).filter(models.User.full_name == user.nama).first()
    if db_user is None or db_user.password != user.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return db_user


################ Bagian Pet ################
@app.post("/pet/{pet_id}", status_code=status.HTTP_201_CREATED)
async def create_pet(pets: PetBase, pet_id: int, db: db_dependency):
    # Your existing code for creating pet goes here
    porsi_makan = pets.berat / 1000 * 30
    db_pet = models.Pet(**pets.dict(), pet_id=pet_id, porsi_makan=porsi_makan)
    db.add(db_pet)
    db.commit()

    feeding_schedule_1 = models.FeedingSchedule(
        jam_makan=time(hour=8, minute=0, second=0),
        pet_id=pet_id
    )
    feeding_schedule_2 = models.FeedingSchedule(
        jam_makan=time(hour=18, minute=0, second=0),
        pet_id=pet_id
    )
    
    db.add_all([feeding_schedule_1, feeding_schedule_2])
    db.commit()

    return {"message": "Pet created successfully"}


@app.get("/pet/{device_id}", status_code=status.HTTP_200_OK)
async def get_pet(device_id: int, db: db_dependency):
    pet = db.query(models.Pet).filter(models.Pet.pet_id == device_id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet not found")
    return pet


@app.get("/pet/{pet_id}/feedtime",status_code=status.HTTP_200_OK)
async def get_feedTime(pet_id: int, db: db_dependency):
    feedTimes = db.query(models.FeedingSchedule).filter(models.FeedingSchedule.pet_id == pet_id).all()
    if not feedTimes:
        raise HTTPException(status_code=404, detail="Feed times not found")

    return feedTimes


@app.put("/pet/schedule/edit/{schedule_id}", status_code=status.HTTP_202_ACCEPTED, response_model=List[str])
async def edit_schedule(time_edited: str, schedule_id: int, db: db_dependency):
    try:
        schedule = db.query(models.FeedingSchedule).filter(models.FeedingSchedule.schedule_id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        schedule.jam_makan = datetime.strptime(time_edited, "%H:%M:%S").time()
        db.commit()
        
        updated_schedules = db.query(models.FeedingSchedule.jam_makan).filter(models.FeedingSchedule.pet_id == schedule.pet_id).all()
        if updated_schedules is None:
            raise HTTPException(status_code=404, detail="Schedules not found")
        
        jam_makan_str_list = [time[0].strftime("%H:%M:%S") for time in updated_schedules if time[0] is not None]

        mqtt_client.publish(mqtt_topic, ','.join(jam_makan_str_list))
        
        return jam_makan_str_list
    except Exception as e:
        return {"error": str(e)} 
    
@app.get("/pet/{pet_id}/foodporsion", status_code=status.HTTP_200_OK)
async def get_foodPorsion(pet_id: int, db:db_dependency):
    pet = db.query(models.Pet.porsi_makan).filter(models.Pet.pet_id == pet_id).first()
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

@app.post("/pet/history/add", status_code = status.HTTP_201_CREATED)
async def create_history(FeedingHistory: CreateFeedingHistory, db: db_dependency):
    db_FeedingHistory = models.FeedingHistory(**FeedingHistory.dict())
    db.add(db_FeedingHistory)
    db.commit()

################ Bagian Device ################
@app.get("/device/{user_id}",status_code=status.HTTP_200_OK)
async def get_devices(user_id: int,db: db_dependency):
    devices = db.query(models.Device).filter(models.Device.user_id == user_id).all()
    if devices is None:
        raise HTTPException(status_code=404, detail="Devices not found")
    return devices


@app.post("/device/{user_id}", status_code = status.HTTP_201_CREATED)
async def create_device(
    devices: DeviceCreate,
    user_id: int,
    db: db_dependency
):

    # Your existing code for creating device goes here
    db_device = models.Device(**devices.dict(), user_id=user_id)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)

    mac_address = devices.mac_address 
    mqtt_client.publish(mqtt_topic, mac_address)

    return {"message": "Device created successfully"}

    return db_device

@app.post("/test", status_code = status.HTTP_201_CREATED)
async def test_Berat(berat: InputBerat, db: db_dependency):
    db_test = models.TestArduino(**berat.dict())
    db.add(db_test)
    db.commit()

@app.get("/pairing/{mac_address}", status_code = status.HTTP_200_OK) #COBA MQTT (WORKING)
async def publish_mac_mqtt(mac_address: str):
    mqtt_client.publish(mqtt_topic, mac_address)
    return {"message": "mac address published"}

