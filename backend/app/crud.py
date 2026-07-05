from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models


def list_doctors(db: Session, specialty: str | None = None):
    q = db.query(models.Doctor).filter(models.Doctor.active == True)  # noqa: E712
    if specialty:
        q = q.filter(models.Doctor.specialty.ilike(f"%{specialty}%"))
    return q.all()


def get_doctor(db: Session, doctor_id: int):
    return db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()


def list_available_slots(db: Session, doctor_id: int, day: datetime | None = None):
    q = db.query(models.AvailabilitySlot).filter(
        models.AvailabilitySlot.doctor_id == doctor_id,
        models.AvailabilitySlot.is_booked == False,  # noqa: E712
        models.AvailabilitySlot.slot_start >= datetime.utcnow(),
    )
    if day:
        start_of_day = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day.replace(hour=23, minute=59, second=59)
        q = q.filter(
            and_(
                models.AvailabilitySlot.slot_start >= start_of_day,
                models.AvailabilitySlot.slot_start <= end_of_day,
            )
        )
    return q.order_by(models.AvailabilitySlot.slot_start).all()


def get_slot(db: Session, slot_id: int):
    return db.query(models.AvailabilitySlot).filter(models.AvailabilitySlot.id == slot_id).first()


class BookingError(Exception):
    """Raised when a booking rule is violated. Message is safe to speak to the patient."""


def book_appointment(db: Session, slot_id: int, patient_name: str, patient_phone: str | None):
    slot = get_slot(db, slot_id)
    if not slot:
        raise BookingError("That slot does not exist. I don't have that information.")
    if slot.is_booked:
        raise BookingError("That slot has just been booked by someone else. Please choose another time.")

    slot.is_booked = True
    appointment = models.Appointment(
        doctor_id=slot.doctor_id,
        slot_id=slot.id,
        patient_name=patient_name,
        patient_phone=patient_phone,
        status="confirmed",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def cancel_appointment(db: Session, appointment_id: int):
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        raise BookingError("I couldn't find an appointment with that ID.")
    if appt.status == "cancelled":
        raise BookingError("That appointment is already cancelled.")

    appt.status = "cancelled"
    slot = get_slot(db, appt.slot_id)
    if slot:
        slot.is_booked = False
    db.commit()
    db.refresh(appt)
    return appt


def reschedule_appointment(db: Session, appointment_id: int, new_slot_id: int):
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        raise BookingError("I couldn't find an appointment with that ID.")

    new_slot = get_slot(db, new_slot_id)
    if not new_slot:
        raise BookingError("That new slot does not exist.")
    if new_slot.is_booked:
        raise BookingError("That new slot is already booked. Please choose another time.")

    old_slot = get_slot(db, appt.slot_id)
    if old_slot:
        old_slot.is_booked = False

    new_slot.is_booked = True
    appt.slot_id = new_slot.id
    appt.doctor_id = new_slot.doctor_id
    appt.status = "confirmed"
    db.commit()
    db.refresh(appt)
    return appt


def get_clinic_info(db: Session, key: str):
    row = db.query(models.ClinicInfo).filter(models.ClinicInfo.key == key).first()
    return row.value if row else None
