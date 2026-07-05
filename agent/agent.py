"""
Voice Clinic Assistant - LiveKit Agent
mic audio -> VAD -> STT -> LLM (with tools) -> TTS -> speaker audio
Run it with:  python agent.py dev
"""
import logging
from dotenv import load_dotenv

from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
    RoomInputOptions,
)
from livekit.plugins import elevenlabs, groq, silero, noise_cancellation

import tools
from prompts import SYSTEM_PROMPT, GREETINGS

load_dotenv()
logger = logging.getLogger("clinic-agent")

LANGUAGE_CODES = {"en": "en", "hi": "hi", "kn": "kn"}


class ClinicAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool()
    async def find_doctors(self, context: RunContext, specialty: str | None = None):
        return await tools.find_doctors(specialty)

    @function_tool()
    async def find_available_slots(self, context: RunContext, doctor_id: int, day_iso: str | None = None):
        return await tools.find_available_slots(doctor_id, day_iso)

    @function_tool()
    async def book_slot(self, context: RunContext, slot_id: int, patient_name: str, patient_phone: str | None = None):
        return await tools.book_slot(slot_id, patient_name, patient_phone)

    @function_tool()
    async def cancel_appointment(self, context: RunContext, appointment_id: int):
        return await tools.cancel_appointment(appointment_id)

    @function_tool()
    async def reschedule_appointment(self, context: RunContext, appointment_id: int, new_slot_id: int):
        return await tools.reschedule_appointment(appointment_id, new_slot_id)

    @function_tool()
    async def get_clinic_info(self, context: RunContext, key: str):
        return await tools.get_clinic_info(key)


async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession(
        vad=silero.VAD.load(),
        stt=elevenlabs.STT(),
        llm=groq.LLM(model="llama-3.1-8b-instant"),
        tts=elevenlabs.TTS(),
    )

    await session.start(
        agent=ClinicAssistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await session.say(GREETINGS["en"], allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
