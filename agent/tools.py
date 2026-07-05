"""
These are the ONLY ways the voice agent is allowed to touch clinic data.
Every function calls the backend API — nothing here is invented by the LLM.
This is what enforces the "must not hallucinate availability" rule.
"""
import os
import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


async def find_doctors(specialty: str | None = None) -> list[dict]:
    async with httpx.AsyncClient() as client:
        params = {"specialty": specialty} if specialty else {}
        r = await client.get(f"{BACKEND_URL}/doctors", params=params)
        r.raise_for_status()
        return r.json()


async def find_available_slots(doctor_id: int, day_iso: str | None = None) -> list[dict]:
    # Guard against the LLM sending words like "tomorrow" instead of a real date.
    if day_iso:
        try:
            from datetime import date
            date.fromisoformat(day_iso)
        except ValueError:
            day_iso = None  # ignore invalid dates instead of crashing

    async with httpx.AsyncClient() as client:
        params = {"day": day_iso} if day_iso else {}
        r = await client.get(f"{BACKEND_URL}/doctors/{doctor_id}/slots", params=params)
        r.raise_for_status()
        return r.json()

async def book_slot(slot_id: int, patient_name: str, patient_phone: str | None = None) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BACKEND_URL}/appointments",
            json={"slot_id": slot_id, "patient_name": patient_name, "patient_phone": patient_phone},
        )
        if r.status_code == 409:
            return {"error": r.json().get("detail", "Could not book that slot.")}
        r.raise_for_status()
        return r.json()


async def cancel_appointment(appointment_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BACKEND_URL}/appointments/cancel", json={"appointment_id": appointment_id})
        if r.status_code == 409:
            return {"error": r.json().get("detail", "Could not cancel that appointment.")}
        r.raise_for_status()
        return r.json()


async def reschedule_appointment(appointment_id: int, new_slot_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BACKEND_URL}/appointments/reschedule",
            json={"appointment_id": appointment_id, "new_slot_id": new_slot_id},
        )
        if r.status_code == 409:
            return {"error": r.json().get("detail", "Could not reschedule that appointment.")}
        r.raise_for_status()
        return r.json()


async def get_clinic_info(key: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BACKEND_URL}/clinic-info/{key}")
        if r.status_code == 404:
            return {"error": "No clinic data configured. Please contact support."}
        r.raise_for_status()
        return r.json()
