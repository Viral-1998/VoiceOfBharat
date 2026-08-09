import logging
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

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# =============================================================================
# DAY 4 — TRACK: Health Access (#VoiceForBharat)
# AGENT: Arogya Seva Telehealth Voice Assistant (with Persistent Memory & Privacy)
# VOICE: Anisha (en-IN) — Murf Falcon Indian English Voice
# =============================================================================

SYSTEM_PROMPT = """IDENTITY:
You are 'Arogya Seva', an empathetic, clear, and calm telehealth and health access voice assistant for Bharat. You provide accessible health guidance, preventive care advice, preliminary triage information, and remember returning callers with privacy-first consent.

OBJECTIVES:
1. Conduct preliminary health triage by asking brief clarifying questions about the caller's symptoms and duration.
2. Provide safe, easy-to-understand home care and preventive wellness guidance for non-critical health concerns.
3. Help callers identify when they should consult a doctor and guide them to visit their nearest Primary Health Centre (PHC) or clinic.
4. Manage caller memory using function tools: look up returning callers (`lookup_caller`), save caller profiles after receiving explicit consent (`save_caller`), and delete memory upon request (`forget_caller`).

MEMORY & PRIVACY CONSENT (HARD RULE):
- You have tools to access SQLite memory: `lookup_caller`, `save_caller`, and `forget_caller`.
- BEFORE saving any caller information or facts (name, age band, ongoing conditions, triage outcome), you MUST explicitly ask the caller for consent. Example: "May I save your name and basic health details so I can remember you next time?"
- If the caller says YES (agrees), call the `save_caller` tool immediately with their details.
- If the caller says NO (denies consent), DO NOT call `save_caller`. Respect their choice and confirm that their details will not be saved.
- If the caller asks to be forgotten or to delete their records ("Forget me", "Delete my record"), call `forget_caller` immediately.
- For returning callers, use `lookup_caller` if needed, greet them warmly by name, and follow up on their previous triage outcome.

HEALTH ACCESS FACTS BOUNDARY:
- Only store non-confidential structured facts: `age_band`, `ongoing_conditions`, and `last_triage_outcome`.
- NEVER store written-out medical notes, clinical diagnostic claims, prescription dosages, government IDs (Aadhaar/PAN), OTPs, or financial details.

LANGUAGE & SCRIPT:
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
            last_triage_outcome: Summary outcome or advice given during triage.
            user_id: Unique caller ID (defaults to 'default_caller' if not specified).
        """
        if not user_id:
            user_id = "default_caller"

        facts = {
            "age_band": age_band,
            "ongoing_conditions": ongoing_conditions,
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


# Backward compatibility alias for tests
Assistant = HealthAccessAssistant


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    db.init_db()
    logger.info("=" * 60)
    logger.info("🚀 10 Days of Voice Agents — #VoiceForBharat | Day 4")
    logger.info("Track: Health Access (Arogya Seva Voice Assistant)")
    logger.info("Feature: Persistent Memory & Privacy Consent (SQLite)")
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

    # Determine caller user_id from room participants or room identity
    user_id = "default_caller"
    for participant in ctx.room.remote_participants.values():
        if participant.identity:
            user_id = participant.identity
            break

    caller_profile = db.get_caller(user_id)

    # Tracking latency from end-of-user-speech to first audio output
    last_user_speech_end_time = [None]

    session = AgentSession(
        # Speech-to-text (STT) via Deepgram Nova-3 (language="multi" for multilingual detection)
        stt=deepgram.STT(model="nova-3", language="multi"),
        # LLM via Google Gemini 3.5 Flash Lite (Day 4 recommended model)
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
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

    # Start session and connect to LiveKit room
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

    await ctx.connect()

    # Dynamic greeting based on returning caller memory
    if caller_profile:
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
