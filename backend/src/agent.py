import asyncio
import contextlib
import json
import logging
import os
import time

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db
import health_data

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# =============================================================================
# DAY 5 — TRACK: Health Access (#VoiceForBharat)
# AGENT: Arogya Seva Telehealth Voice Assistant (with Real Domain Data & Tools)
# VOICE: Anisha (en-IN) — Murf Falcon Indian English Voice
# =============================================================================

SYSTEM_PROMPT = """IDENTITY:
You are 'Arogya Seva', an empathetic, clear, and calm telehealth and health access voice assistant for Bharat. You provide accessible health guidance, preventive care advice, preliminary triage classification, real domain health facility lookups, and remember returning callers with privacy-first consent.

OBJECTIVES:
1. Classify symptom triage level using `classify_symptom_triage` when callers describe symptoms or ask about urgency.
2. Lookup real Primary Health Centres (PHCs), CHCs, and District Hospitals using `lookup_nearest_phc` when callers ask for nearby facilities, clinics, bed availability, or emergency contacts.
3. Support Tool Chaining: If caller's district or location is available in memory (`lookup_caller`), use that district directly in `lookup_nearest_phc` without re-asking location.
4. Handle API / portal failure gracefully out loud: If `lookup_nearest_phc` returns service unavailable or offline status, inform the caller calmly and clearly that the registry is unreachable and advise calling emergency 108 or 104 health helpline immediately.
5. Manage caller memory using function tools: `lookup_caller`, `save_caller` (only after explicit consent), and `forget_caller`.
6. Handle Outbound Calls & Opt-Outs (DAY 6): When making outbound calls, state who is calling, why, and how to opt out in the first two sentences. If the caller requests to opt out ("opt out", "stop calling me", "unsubscribe"), call `opt_out_caller` immediately.

OUTBOUND CALL OPENING RULE (HARD COMPULSORY RULE FOR DAY 6):
When initiating or opening an outbound call, the response MUST open with these two exact elements in the first two sentences:
Sentence 1: State WHO is calling and WHY (e.g., "Namaste, this is Arogya Seva calling from your District Health Centre regarding your scheduled medication follow-up and vaccination reminder.")
Sentence 2: State HOW to make it stop or opt out (e.g., "If you wish to stop receiving these outbound health reminders at any time, please say 'opt out' or press 9 to unsubscribe.")

TIMESTAMPING & DATA SOURCES (HARD RULE):
- Whenever returning health facility data or triage classification, state when the data is from (e.g. "Data from National Health Facility Registry as of today" or state the timestamp returned by the tool).

MEMORY & PRIVACY CONSENT (HARD RULE):
- You have tools to access SQLite memory: `lookup_caller`, `save_caller`, and `forget_caller`.
- BEFORE saving any caller information or facts (name, age band, ongoing conditions, triage outcome), you MUST explicitly ask the caller for consent. Example: "May I save your name and basic health details so I can remember you next time?"
- If the caller says YES (agrees), call the `save_caller` tool immediately with their details.
- If the caller says NO (denies consent), DO NOT call `save_caller`. Respect their choice and confirm that their details will not be saved.
- If the caller asks to be forgotten or to delete their records ("Forget me", "Delete my record"), call `forget_caller` immediately.
- For returning callers, use `lookup_caller` if needed, greet them warmly by name, and follow up on their previous triage outcome.

OPT-OUT & UNSUBSCRIBE REGISTRY (HARD RULE):
- If the user says "opt out", "stop calling me", "unsubscribe", "don't call again", or presses 9, invoke `opt_out_caller` immediately. Confirm politely that they have been unsubscribed and end the call gracefully.

HEALTH ACCESS FACTS BOUNDARY:
- Only store non-confidential structured facts: `age_band`, `ongoing_conditions`, `district`, and `last_triage_outcome`.
- NEVER store written-out medical notes, clinical diagnostic claims, prescription dosages, government IDs (Aadhaar/PAN), OTPs, or financial details.

LANGUAGE & SCRIPT (COMPULSORY HARD RULE):
Always write every language in its own native script:
- Hindi → Devanagari script (e.g. नमस्ते), never romanized (never write "namaste" when responding in Hindi).
- Same rule for all non-English languages.
- Dynamically mirror the user's language (English, Hindi, or Hinglish code-mixed).

GUARDRAILS:
- NEVER give a definitive medical diagnosis or name a specific medical condition as a clinical fact.
- NEVER name, recommend, or prescribe any prescription medication, drug dosage, or chemical treatment.
- NEVER claim to be a human doctor, physician, or medical officer, nor guarantee recovery.
- NEVER request private or confidential data such as OTP, PIN, bank account details, or Aadhaar number.
- ESCALATION SCRIPT: If the user describes red-flag or emergency symptoms (e.g., chest pain, severe dyspnea, heavy bleeding, sudden weakness, unconsciousness, severe injury), immediately state: "I am an AI assistant, not a doctor. Your symptoms sound serious. Please call emergency services at 108 immediately or go to the nearest Primary Health Centre right away."

STYLE:
- Optimized strictly for voice: keep replies brief (1 to 2 short sentences, maximum 20 words per sentence).
- Speak with natural conversational pauses. Do NOT use bullet points, numbered lists, asterisks, brackets, emojis, or markdown formatting.
- Speak naturally and clearly, as if speaking directly over a telephone call."""

VOICE_JUSTIFICATION = (
    "Anisha (en-IN) selected for Health Access track: "
    "A calm, articulate Indian English voice that delivers high clarity and reassurance for health guidance."
)


class HealthAccessAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def lookup_nearest_phc(
        self,
        context: RunContext,
        district_or_pincode: str,
        state: str = "",
        simulate_offline: bool = False,
    ) -> str:
        """Look up nearest Primary Health Centre (PHC), Community Health Centre (CHC), or District Hospital by district name or pincode.
        Call this tool whenever the caller asks for nearby health facilities, clinics, hospitals, emergency helplines, or bed availability.

        Args:
            district_or_pincode: District name (e.g. 'Pune', 'Mumbai', 'Delhi', 'Jaipur') or Indian pincode.
            state: Optional Indian state name (e.g. 'Maharashtra', 'Rajasthan').
            simulate_offline: Set to True ONLY if testing or user asks to test offline/failure mode.
        """
        res = health_data.lookup_phc_data(
            district_or_pincode=district_or_pincode,
            state=state,
            simulate_offline=simulate_offline,
        )

        if res.get("status") == "error":
            # Graceful failure instruction
            return f"FAILURE ERROR ({res.get('timestamp')}): {res.get('message')}"

        facilities = res.get("facilities", [])
        if not facilities:
            return f"No registered health centres found for '{district_or_pincode}' as of {res.get('timestamp')}. Advise caller to call national health helpline 104 or emergency 108."

        fac = facilities[0]
        beds = fac.get("available_beds", 0)
        phone = fac.get("phone", "104")
        addr = fac.get("address", "")
        name = fac.get("name", "District PHC")
        timestamp = res.get("timestamp")

        return (
            f"Health Facility Data (Source: {res.get('data_source')}, as of {timestamp}):\n"
            f"Facility: {name}\n"
            f"Address: {addr}\n"
            f"Contact Phone: {phone}\n"
            f"Emergency Helpline: 108\n"
            f"Available Beds: {beds}\n"
            f"Operating Hours: {fac.get('operating_hours')}"
        )

    @function_tool
    async def classify_symptom_triage(
        self,
        context: RunContext,
        symptoms: str,
        duration_days: int = 1,
    ) -> str:
        """Classify symptom clinical triage urgency (RED Emergency, YELLOW Urgent Doctor Visit, GREEN Home Care).
        Call this tool whenever the caller describes physical symptoms, fever, pain, or asks how urgently they need medical care.

        Args:
            symptoms: Caller's described symptoms (e.g. 'fever and headache for 2 days', 'severe chest pain').
            duration_days: Number of days symptoms have persisted.
        """
        res = health_data.classify_triage_engine(
            symptoms=symptoms,
            duration_days=duration_days,
        )
        return (
            f"Triage Assessment Result (Guideline Source: {res.get('guideline_source')}, evaluated on {res.get('timestamp')}):\n"
            f"Triage Level: {res.get('triage_level')}\n"
            f"Urgency: {res.get('urgency_window')}\n"
            f"Recommended Action: {res.get('action_recommended')}\n"
            f"Clinical Rationale: {res.get('clinical_rationale')}"
        )

    @function_tool
    async def lookup_caller(self, context: RunContext, user_id: str = "") -> str:
        """Look up a caller's saved facts from the database by user_id or identity.

        Args:
            user_id: The unique identifier or phone number of the caller.
        """
        if not user_id:
            user_id = "default_caller"
        caller = db.get_caller(user_id)
        if not caller:
            return f"No record found for caller '{user_id}'."
        return (
            f"Caller Record Found:\n"
            f"Name: {caller['name']}\n"
            f"Language Preference: {caller['language_preference']}\n"
            f"Facts: {caller['facts']}\n"
            f"Last Interaction: {caller['last_interaction']}"
        )

    @function_tool
    async def save_caller(
        self,
        context: RunContext,
        name: str,
        language_preference: str = "English",
        age_band: str = "Not specified",
        ongoing_conditions: str = "None",
        district: str = "Not specified",
        last_triage_outcome: str = "Triage completed",
        user_id: str = "",
    ) -> str:
        """Save or update caller information in the database.
        IMPORTANT: Only call this tool AFTER the caller has given explicit verbal consent.

        Args:
            name: The caller's name.
            language_preference: Caller's preferred language (e.g., English, Hindi, Hinglish).
            age_band: Caller's age group (e.g., '30-40', 'Senior (60+)').
            ongoing_conditions: Brief summary of ongoing health conditions (e.g., 'Mild fever', 'Hypertension').
            district: Caller's location or district (e.g. 'Pune', 'Jaipur', 'Mumbai').
            last_triage_outcome: Summary outcome or advice given during triage.
            user_id: Unique caller ID (defaults to 'default_caller' if not specified).
        """
        if not user_id:
            user_id = "default_caller"

        facts = {
            "age_band": age_band,
            "ongoing_conditions": ongoing_conditions,
            "district": district,
            "last_triage_outcome": last_triage_outcome,
        }
        db.save_caller(
            user_id=user_id,
            name=name,
            language_preference=language_preference,
            facts=facts,
        )
        return f"Successfully saved memory for {name} (ID: {user_id})."

    @function_tool
    async def forget_caller(self, context: RunContext, user_id: str = "") -> str:
        """Delete caller information from the database upon request ('forget me').

        Args:
            user_id: Unique caller ID (defaults to 'default_caller' if not specified).
        """
        if not user_id:
            user_id = "default_caller"
        success = db.delete_caller(user_id)
        if success:
            return f"Successfully deleted memory for caller ID '{user_id}'."
        return f"No memory record was found to delete for caller ID '{user_id}'."

    @function_tool
    async def opt_out_caller(
        self,
        context: RunContext,
        phone_number: str = "",
        reason: str = "User requested opt-out during call",
    ) -> str:
        """Register the caller or phone number in the opt-out registry to stop future outbound calls.
        Call this tool immediately whenever the caller asks to opt out, stop receiving calls, or unsubscribe.

        Args:
            phone_number: The caller's phone number or identifier.
            reason: Reason for opt-out request.
        """
        if not phone_number:
            phone_number = "default_caller"
        db.register_opt_out(phone_number, reason=reason)
        return f"Successfully registered opt-out for '{phone_number}'. No further outbound calls will be made."


# Backward compatibility alias for tests
Assistant = HealthAccessAssistant


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    db.init_db()
    logger.info("=" * 60)
    logger.info("🚀 10 Days of Voice Agents — #VoiceForBharat | Day 6")
    logger.info("Track: Health Access (Arogya Seva Telehealth Voice Assistant)")
    logger.info("Feature: Outbound Calling & Opt-Out Registry (Twilio/LiveKit SIP)")
    logger.info("Voice: Murf Falcon (Anisha / en-IN)")
    logger.info(f"Justification: {VOICE_JUSTIFICATION}")
    logger.info("=" * 60)


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
        "track": "Health Access",
    }

    db.init_db()

    # Parse room metadata for outbound call details
    room_meta = {}
    if ctx.room.metadata:
        with contextlib.suppress(Exception):
            room_meta = json.loads(ctx.room.metadata)

    is_outbound = (
        room_meta.get("is_outbound", False)
        or "outbound" in ctx.room.name.lower()
    )
    patient_name = room_meta.get("patient_name", "")
    reminder_type = room_meta.get(
        "reminder_type", "scheduled medication follow-up and vaccination reminder"
    )
    call_id = room_meta.get("call_id", "")

    # Tracking latency from end-of-user-speech to first audio output
    last_user_speech_end_time = [None]

    # LLM Provider Selection (Groq > OpenAI > Google Gemini)
    if os.getenv("GROQ_API_KEY"):
        from livekit.plugins import groq
        llm_instance = groq.LLM(model="llama-3.3-70b-versatile")
        logger.info("🤖 LLM Engine: Groq llama-3.3-70b-versatile (Free 14,400 requests/day)")
    elif os.getenv("OPENAI_API_KEY"):
        from livekit.plugins import openai
        llm_instance = openai.LLM(model="gpt-4o-mini")
        logger.info("🤖 LLM Engine: OpenAI gpt-4o-mini")
    else:
        llm_instance = google.LLM(model="gemini-3.5-flash")
        logger.info("🤖 LLM Engine: Google Gemini (gemini-3.5-flash)")

    session = AgentSession(
        # Speech-to-text (STT) via Deepgram Nova-3 (language="multi" for multilingual detection)
        stt=deepgram.STT(model="nova-3", language="multi"),
        # LLM Engine
        llm=llm_instance,
        # Murf Falcon TTS — dynamic multi-locale voice synthesis
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # Event handlers for Latency Logging
    @session.on("user_speech_committed")
    def _on_user_speech_committed(msg):
        last_user_speech_end_time[0] = time.perf_counter()
        logger.info("🎙️ User speech finished. Sent to LLM & Murf Falcon TTS...")

    @session.on("agent_speech_started")
    def _on_agent_speech_started():
        if last_user_speech_end_time[0] is not None:
            latency_ms = (time.perf_counter() - last_user_speech_end_time[0]) * 1000
            logger.info(
                f"⚡ [LATENCY LOG] End-of-user-speech to first audio output: {latency_ms:.2f} ms"
            )
            last_user_speech_end_time[0] = None

    @session.on("metrics_collected")
    def _on_metrics_collected(metrics):
        logger.info(f"📊 [SESSION METRICS] {metrics}")

    # Start session event listeners on room
    await session.start(
        agent=HealthAccessAssistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Connect worker to LiveKit room
    await ctx.connect()

    # Wait for recipient to connect to room
    try:
        participant = await ctx.wait_for_participant()
        logger.info(f"👤 Remote participant connected: {participant.identity} ({participant.name})")
    except Exception as e:
        logger.warning(f"⚠️ Note on participant wait: {e}")

    # For outbound calls, pause 1 second to allow SIP audio channel on softphone/phone to stabilize
    if is_outbound:
        await asyncio.sleep(1.0)

    # Determine caller user_id from connected room participants
    user_id = "default_caller"
    for participant in ctx.room.remote_participants.values():
        if participant.identity:
            user_id = participant.identity
            break

    caller_profile = db.get_caller(user_id)
    phone_number = room_meta.get("phone_number", user_id)

    # Check for opt-out status on outbound calls
    if is_outbound and db.is_opted_out(phone_number):
        logger.info(f"🛑 Phone number {phone_number} is on opt-out registry. Ending call.")
        with contextlib.suppress(RuntimeError):
            await session.say(
                "Namaste. This phone number is registered on our opt-out list. Arogya Seva will not place further outbound calls. Goodbye.",
                allow_interruptions=False,
            )
        if call_id:
            db.update_call_outcome(call_id, outcome="opt_out")
        return

    # Determine dynamic opening speech
    if is_outbound:
        # STEP 4 COMPLIANCE: Must open with: (1) Who is calling & why, (2) How to opt out
        greeting_text = (
            f"Namaste {patient_name if patient_name else ''}, this is Arogya Seva calling from your District Health Centre regarding your {reminder_type}. "
            f"If you wish to stop receiving these outbound health reminders at any time, please say 'opt out' or press 9 to unsubscribe."
        )
    elif caller_profile:
        name = caller_profile["name"]
        last_outcome = caller_profile["facts"].get(
            "last_triage_outcome", "our previous health consultation"
        )
        greeting_text = (
            f"Namaste {name}, welcome back to Arogya Seva! Last time we spoke about {last_outcome}. "
            f"How are you feeling today?"
        )
    else:
        greeting_text = "Namaste! I am Arogya Seva, your health guidance assistant. How can I help you with your health today?"

    with contextlib.suppress(RuntimeError):
        await session.say(
            greeting_text,
            allow_interruptions=True,
        )


if __name__ == "__main__":
    import os
    import sys

    required_keys = [
        "LIVEKIT_URL",
        "LIVEKIT_API_KEY",
        "LIVEKIT_API_SECRET",
        "MURF_API_KEY",
        "DEEPGRAM_API_KEY",
        "GOOGLE_API_KEY",
    ]

    missing = []
    for key in required_keys:
        val = os.getenv(key, "")
        if not val or "your_" in val or "your-project" in val:
            missing.append(key)

    if missing:
        print("\n" + "=" * 70)
        print("⚠️  MISSING / PLACEHOLDER API KEYS DETECTED:")
        print("   The following keys in backend/.env.local are not configured:")
        for k in missing:
            print(f"   - {k}")
        print("\n   👉 Please edit backend/.env.local and add your real API keys:")
        print("   - LiveKit:   https://cloud.livekit.io/")
        print("   - Murf AI:   https://murf.ai/api/dashboard")
        print("   - Deepgram:  https://deepgram.com")
        print("   - Gemini:    https://aistudio.google.com/apikey")
        print("=" * 70 + "\n")

    if len(sys.argv) == 1:
        sys.argv.append("dev")
    cli.run_app(server)
