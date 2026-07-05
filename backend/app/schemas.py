from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DoctorOut(BaseModel):
    id: int
    name: str
    specialty: str
    bio: Optional[str] = None

    class Config:
        from_attributes = True


class SlotOut(BaseModel):
    id: int
    doctor_id: int
    slot_start: datetime
    slot_end: datetime
    is_booked: bool

    class Config:
        from_attributes = True


class BookingRequest(BaseModel):
    slot_id: int
    patient_name: str
    patient_phone: Optional[str] = None


class RescheduleRequest(BaseModel):
    appointment_id: int
    new_slot_id: int


class CancelRequest(BaseModel):
    appointment_id: int


class AppointmentOut(BaseModel):
    id: int
    doctor_id: int
    slot_id: int
    patient_name: str
    status: str

    class Config:
        from_attributes = True
