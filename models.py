from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, select, Time, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from database import Base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True, index=True)
    password = Column(String(60))
    name = Column(String(50))
    full_name = Column(String(50))
    

class Pet(Base):
    __tablename__ = 'pets'

    pet_id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(50))
    berat = Column(Integer)
    porsi_makan = Column(Integer)
    tipe_hewan = Column(String(30))
    ras_hewan = Column(String(30))
    umur = Column(Integer)
    device_id = Column(Integer, ForeignKey("devices.device_id"))

    device = relationship("Device", back_populates="pets")

class Device(Base):
    __tablename__ = 'devices'

    device_id = Column(Integer, primary_key=True, index=True)
    model = Column(String(30))
    mac_address = Column(String(50))
    user_id = Column(Integer, ForeignKey("user.user_id"))

    # Define the relationship with users
    pets = relationship("Pet", back_populates="device")

class FeedingSchedule(Base):
    __tablename__ = 'FeedingSchedule'

    schedule_id = Column(Integer, primary_key=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.pet_id"))
    jam_makan = Column(Time)

    FeedingHistory = relationship("FeedingHistory",back_populates="FeedingSchedule")


class FeedingHistory(Base):
    __tablename__ = 'FeedingHistory'
    
    feeding_id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("FeedingSchedule.schedule_id"))
    feeding_date = Column(Date)
    dimakan = Column(Integer)

    FeedingSchedule = relationship("FeedingSchedule",back_populates="FeedingHistory")


class TestArduino(Base):
    __tablename__ = 'testArduino'
    test_id = Column(Integer, primary_key=True, index=True)
    berat = Column(Integer)


