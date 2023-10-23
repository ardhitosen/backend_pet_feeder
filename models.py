from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, select, Time
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from database import Base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True, index=True)
    password = Column(String(60))
    nama = Column(String(50))
    jumlah_hewan = Column(Integer)

class Pet(Base):
    __tablename__ = 'pets'

    pet_id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(50))
    berat = Column(Integer)
    porsi_makan = Column(Integer)
    tipe_hewan = Column(String(30))
    ras_hewan = Column(String(30))
    umur = Column(Integer)
    jam_makan = Column(Time)
    device_id = Column(Integer, ForeignKey("devices.device_id"))

    device = relationship("Device", back_populates="pets")


class Device(Base):
    __tablename__ = 'devices'

    device_id = Column(Integer, primary_key=True, index=True)
    model = Column(String(30))
    user_id = Column(Integer, ForeignKey("user.user_id"))

    # Define the relationship with users
    pets = relationship("Pet", back_populates="device")
