from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from database import Base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True, index=True)
    password = Column(String(60))
    nama = Column(String(50))
    device = Column(String(50), nullable = True)
    jumlah_hewan = Column(Integer)

    # Define the relationship with pets and devices
    pets = relationship("Pet", back_populates="owner")
    devices = relationship("Device", back_populates="owner")

class Pet(Base):
    __tablename__ = 'pets'

    pet_id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(50))
    berat = Column(Integer)
    porsi_makan = Column(Integer)
    tipe_hewan = Column(String(30))
    ras_hewan = Column(String(30))
    umur = Column(Integer)
    user_id = Column(Integer, ForeignKey("user.user_id"))

    # Define the relationship with users
    owner = relationship("User", back_populates="pets")

class Device(Base):
    __tablename__ = 'devices'

    device_id = Column(Integer, primary_key=True, index=True)
    model = Column(String(30))
    user_id = Column(Integer, ForeignKey("user.user_id"))

    # Define the relationship with users
    owner = relationship("User", back_populates="devices")
