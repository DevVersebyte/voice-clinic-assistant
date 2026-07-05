import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from livekit import api as lk_api

from . import crud, schemas
from .database import get_db, engine, Base

# NOTE: In production, prefer running db/schema.sql manually against Neon.
# This is a convenience so the API doesn't crash on a fresh, unmigrated DB.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Voice Clinic Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend's URL before submitting
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/doctors", response_model=list[schemas.DoctorOut])
def get_doctors(specialty: Optional[str] = None, db: Session = Depends(get_db)):
    return crud.list_doctors(db, specialty)


@app.get("/doctors/{doctor_id}/slots", response_model=list[schemas.SlotOut])
def get_slots(doctor_id: int, day: Optional[datetime] = None, db: Session = Depends(get_db)):
    doctor = crud.get_doctor(db, doctor_id)
    if not doctor:
        raise HTTPException(404, "Doctor not found")
    return crud.list_available_slots(db, doctor_id, day)


@app.post("/appointments", response_model=schemas.AppointmentOut)
def create_appointment(req: schemas.BookingRequest, db: Session = Depends(get_db)):
    try:
        return crud.book_appointment(db, req.slot_id, req.patient_name, req.patient_phone)
    except crud.BookingError as e:
        raise HTTPException(409, str(e))


@app.post("/appointments/cancel", response_model=schemas.AppointmentOut)
def cancel_appointment(req: schemas.CancelRequest, db: Session = Depends(get_db)):
    try:
        return crud.cancel_appointment(db, req.appointment_id)
    except crud.BookingError as e:
        raise HTTPException(409, str(e))


@app.post("/appointments/reschedule", response_model=schemas.AppointmentOut)
def reschedule_appointment(req: schemas.RescheduleRequest, db: Session = Depends(get_db)):
    try:
        return crud.reschedule_appointment(db, req.appointment_id, req.new_slot_id)
    except crud.BookingError as e:
        raise HTTPException(409, str(e))


@app.get("/livekit-token")
def livekit_token(name: str = "patient"):
    """
    Mints a LiveKit room-join token for the frontend. Public/no-auth by design
    (per the assignment), so we just generate a random room per call.
    """
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")
    if not (api_key and api_secret and livekit_url):
        raise HTTPException(500, "LiveKit is not configured on the server (.env).")

    room_name = f"clinic-call-{uuid.uuid4().hex[:8]}"
    identity = f"{name}-{uuid.uuid4().hex[:4]}"

    token = (
        lk_api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(name)
        .with_grants(lk_api.VideoGrants(room_join=True, room=room_name))
    )
    return {"token": token.to_jwt(), "url": livekit_url, "room": room_name}


@app.get("/clinic-info/{key}")
def clinic_info(key: str, db: Session = Depends(get_db)):
    value = crud.get_clinic_info(db, key)
    if value is None:
        raise HTTPException(404, "No clinic data configured. Please contact support.")
    return {"key": key, "value": value}
