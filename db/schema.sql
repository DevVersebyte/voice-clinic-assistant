-- Voice Clinic Assistant — Database Schema
-- Run this against your Neon Postgres database.

CREATE TABLE IF NOT EXISTS doctors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    specialty TEXT NOT NULL,
    bio TEXT,
    active BOOLEAN DEFAULT TRUE
);

-- Each row is one bookable slot for a doctor.
-- is_booked flips to TRUE once an appointment takes it.
CREATE TABLE IF NOT EXISTS availability_slots (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    slot_start TIMESTAMPTZ NOT NULL,
    slot_end TIMESTAMPTZ NOT NULL,
    is_booked BOOLEAN DEFAULT FALSE,
    UNIQUE (doctor_id, slot_start)
);

CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id),
    slot_id INTEGER NOT NULL REFERENCES availability_slots(id),
    patient_name TEXT NOT NULL,
    patient_phone TEXT,
    status TEXT NOT NULL DEFAULT 'confirmed', -- confirmed | cancelled | rescheduled
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clinic_info (
    id SERIAL PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,   -- e.g. 'opening_hours', 'address'
    value TEXT NOT NULL
);

-- ---------- Seed data so the app has something real to talk about ----------

INSERT INTO doctors (name, specialty, bio) VALUES
    ('Dr. Anita Rao', 'General Physician', 'Handles general checkups and common illnesses.'),
    ('Dr. Vikram Shetty', 'Cardiologist', 'Specializes in heart-related conditions.'),
    ('Dr. Meera Nair', 'Pediatrician', 'Specializes in child healthcare.'),
    ('Dr. Sanjay Kumar', 'Dermatologist', 'Specializes in skin conditions.')
ON CONFLICT DO NOTHING;

INSERT INTO clinic_info (key, value) VALUES
    ('opening_hours', 'Monday to Saturday, 9:00 AM to 6:00 PM'),
    ('address', 'City Care Clinic, MG Road, Mangaluru')
ON CONFLICT (key) DO NOTHING;

-- Generate some open slots for the next 7 days, every hour 9am-5pm, for each doctor.
INSERT INTO availability_slots (doctor_id, slot_start, slot_end)
SELECT d.id,
       gs.slot_start,
       gs.slot_start + interval '30 minutes'
FROM doctors d
CROSS JOIN LATERAL (
    SELECT generate_series(
        date_trunc('day', now()) + interval '1 day' + interval '9 hours',
        date_trunc('day', now()) + interval '7 days' + interval '17 hours',
        interval '1 hour'
    ) AS slot_start
) gs
ON CONFLICT (doctor_id, slot_start) DO NOTHING;
