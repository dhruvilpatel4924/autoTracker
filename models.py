# models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vin = Column(String(34), unique=True, nullable=False, index=True)
    year = Column(String(10))
    maker = Column(String(100))
    model = Column(String(100))

    maintenance_logs = relationship("MaintenanceLog", back_populates="vehicle", cascade="all, delete-orphan")

class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    mileage = Column(Integer, nullable=False)
    type = Column(String(100), nullable=False)
    description = Column(Text)
    date_created = Column(DateTime(timezone=True), server_default=func.now())

    vehicle = relationship("Vehicle", back_populates="maintenance_logs")
