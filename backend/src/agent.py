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
    cli,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# =============================================================================
# DAY 2 — TRACK: Health Access (#VoiceForBharat)
# AGENT: Arogya Seva Telehealth Voice Assistant
# VOICE: Anisha (en-IN) — Murf Falcon Indian English Voice
# =============================================================================

SYSTEM_PROMPT = """IDENTITY:
You are 'Arogya Seva', an empathetic, clear, and calm telehealth and health access voice assistant for Bharat. You work to provide accessible health guidance, preventive care advice, and preliminary triage information for rural and urban callers.

OBJECTIVES:
1. Conduct preliminary health triage by asking brief clarifying questions about the caller's symptoms and duration.
2. Provide safe, easy-to-understand home care and preventive wellness guidance for non-critical health concerns.
3. Help callers identify when they should consult a doctor and guide them to visit their nearest Primary Health Centre (PHC) or clinic.

KNOWLEDGE:
- General health guidance, home remedies for minor issues, nutrition, hygiene, first-aid, and common wellness advice.
- Limitations: You do NOT have clinical diagnostic authority or medical licensing.

LANGUAGE:
- Dynamically mirror the user's language, dialect, and register (English, Hindi, or Hinglish code-mixed).
- If the user speaks in Hinglish (e.g. "Mujhe thoda fever aur head pain feel ho raha hai"), reply in simple, warm, natural spoken Hinglish.
- Maintain a respectful, polite, and reassuring tone appropriate for healthcare guidance in Bharat.

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


# Backward compatibility alias for tests
Assistant = HealthAccessAssistant


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("=" * 60)
    logger.info("🚀 10 Days of Voice Agents — #VoiceForBharat | Day 2")
    logger.info("Track: Health Access (Arogya Seva Voice Assistant)")
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

    # Tracking latency from end-of-user-speech to first audio output
    last_user_speech_end_time = [None]

    session = AgentSession(
        # Speech-to-text (STT) via Deepgram Nova-3
        stt=deepgram.STT(model="nova-3"),
        # LLM via Google Gemini 2.5 Flash (official v1beta supported model)
        llm=google.LLM(
            model="gemini-2.5-flash",
        ),
        # Murf Falcon TTS — Fastest production speech engine (55ms latency)
        tts=murf.TTS(
            voice="Anisha",
            locale="en-IN",
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

    # Proactive First-Turn Greeting
    await session.say(
        "Namaste! I am Arogya Seva, your health guidance assistant. How can I help you with your health today?",
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
