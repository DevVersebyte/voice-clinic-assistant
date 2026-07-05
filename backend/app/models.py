from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, Text, func
)
from sqlalchemy.orm import relationship
from .database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    specialty = Column(Text, nullable=False)
    bio = Column(Text)
    active = Column(Boolean, default=True)

    slots = relationship("AvailabilitySlot", back_populates="doctor")


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    slot_start = Column(TIMESTAMP(timezone=True), nullable=False)
    slot_end = Column(TIMESTAMP(timezone=True), nullable=False)
    is_booked = Column(Boolean, default=False)

    doctor = relationship("Doctor", back_populates="slots")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("availability_slots.id"), nullable=False)
    patient_name = Column(Text, nullable=False)
    patient_phone = Column(Text)
    status = Column(Text, nullable=False, default="confirmed")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class ClinicInfo(Base):
    __tablename__ = "clinic_info"

    id = Column(Integer, primary_key=True)
    key = Column(Text, unique=True, nullable=False)
    value = Column(Text, nullable=False)
