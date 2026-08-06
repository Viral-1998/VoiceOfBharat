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
# DAY 1 — TRACK: Health Access (#VoiceForBharat)
# VOICE: Anisha (en-IN) — Murf Falcon Indian English Voice
# VOICE JUSTIFICATION:
# "Anisha's calm, articulate, and warm Indian English voice instils medical
# trust, clarity, and reassurance essential for rural telehealth guidance."
# =============================================================================

SYSTEM_PROMPT = """You are 'Arogya Seva', an empathetic, clear, and calm telehealth and health access voice assistant for Bharat.
Your goal is to provide accessible, easy-to-understand health guidance, preventive care advice, and preliminary triage information for rural and urban callers.

Guidelines:
- Speak with a warm, reassuring, and respectful tone appropriate for healthcare.
- Keep responses short and concise (1 to 3 simple sentences) so it sounds natural over audio.
- Never give definitive medical diagnoses or prescribe prescription medicines. Always recommend consulting a registered medical practitioner or visiting the nearest Primary Health Centre (PHC) for urgent or severe symptoms.
- Do NOT use markdown symbols, bullet points, emojis, or complex medical jargon. Speak naturally and clearly in spoken English.
- Always mention your track 'Health Access' if asked about your purpose."""

VOICE_JUSTIFICATION = (
    "Anisha (en-IN) selected for Health Access track: "
    "A calm, articulate Indian English voice that delivers high clarity and reassurance for health guidance."
)


class HealthAccessAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("=" * 60)
    logger.info("🚀 10 Days of Voice Agents — #VoiceForBharat | Day 1")
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

    # Event handlers for Latency Logging (Advanced Requirement)
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
