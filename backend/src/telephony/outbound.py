import argparse
import asyncio
import json
import logging
import os
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from dotenv import load_dotenv

# Add parent directory to sys.path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import db

logger = logging.getLogger("telephony.outbound")
load_dotenv(".env.local")

# =============================================================================
# OUTCOME RETRY TIMINGS & RULES (DAY 6 ADVANCED REQUIREMENTS)
# =============================================================================
RETRY_CONFIG = {
    "no_answer": {"retry_delay_minutes": 15, "max_retries": 3},
    "busy": {"retry_delay_minutes": 5, "max_retries": 3},
    "voicemail": {"retry_delay_minutes": 0, "max_retries": 0, "leave_message": True},
    "immediate_hangup": {"retry_delay_minutes": 30, "max_retries": 1},
    "opt_out": {"retry_delay_minutes": 0, "max_retries": 0},
    "completed": {"retry_delay_minutes": 0, "max_retries": 0},
}


def calculate_next_retry(outcome: str, current_retry_count: int = 0) -> Optional[str]:
    """Calculate the ISO-formatted timestamp for the next call retry based on outcome."""
    config = RETRY_CONFIG.get(outcome)
    if not config:
        return None

    max_retries = config.get("max_retries", 0)
    if current_retry_count >= max_retries:
        logger.info(
            f"Max retries ({max_retries}) reached for outcome '{outcome}'. No further retry scheduled."
        )
        return None

    delay = config.get("retry_delay_minutes", 0)
    if delay <= 0:
        return None

    next_time = datetime.now(timezone.utc) + timedelta(minutes=delay)
    return next_time.isoformat()


def normalize_sip_call_to(raw_target: str) -> str:
    """Normalize phone number or Linphone SIP URI into valid sip_call_to parameter for LiveKit API."""
    target = raw_target.strip()
    if target.startswith("sip:"):
        target = target[4:]
    if "@" in target:
        target = target.split("@")[0]
    return target


class OutboundCallManager:
    """Manages outbound call dispatch via LiveKit SIP or room dispatch with outcome handling."""

    def __init__(self) -> None:
        self.livekit_url = os.getenv("LIVEKIT_URL", "")
        self.api_key = os.getenv("LIVEKIT_API_KEY", "")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET", "")
        db.init_db()

    def can_place_call(self, phone_number_or_id: str) -> tuple[bool, str]:
        """Check if caller is eligible for outbound call (not opted out)."""
        if db.is_opted_out(phone_number_or_id):
            return (
                False,
                f"Number '{phone_number_or_id}' has opted out of outbound calls.",
            )
        return True, "Eligible"

    async def initiate_outbound_call(
        self,
        phone_number: str,
        patient_name: str,
        reminder_type: str = "Medication Follow-up",
        sip_trunk_id: str = "",
        sip_domain: str = "",
    ) -> dict[str, Any]:
        """Initiate an outbound call for a given patient via Twilio / Linphone SIP trunk and log to SQLite database."""
        eligible, reason = self.can_place_call(phone_number)
        if not eligible:
            logger.warning(f"🚫 Outbound call cancelled: {reason}")
            return {
                "status": "opted_out",
                "reason": reason,
                "phone_number": phone_number,
            }

        sip_trunk_id = sip_trunk_id or os.getenv("SIP_TRUNK_ID", "")
        call_id = f"outbound_{uuid.uuid4().hex[:10]}"
        room_name = f"outbound_call_{call_id}"
        clean_call_to = normalize_sip_call_to(phone_number)
        clean_identity = re.sub(r"[^a-zA-Z0-9_-]", "_", f"phone_{clean_call_to}")

        # Room metadata carries explicit outbound context for agent.py
        room_metadata = json.dumps(
            {
                "is_outbound": True,
                "call_id": call_id,
                "phone_number": phone_number,
                "patient_name": patient_name,
                "reminder_type": reminder_type,
            }
        )

        db.log_outbound_call(
            call_id=call_id,
            phone_number=phone_number,
            patient_name=patient_name,
            reminder_type=reminder_type,
            status="initiated",
        )

        logger.info("=" * 70)
        logger.info(f"📞 OUTBOUND CALL DISPATCH INITIATED [ID: {call_id}]")
        logger.info(
            f"Recipient: {patient_name} ({phone_number}) -> Normalized SIP Target: '{clean_call_to}'"
        )
        logger.info(f"Reminder Context: {reminder_type}")
        logger.info(f"Target Room: {room_name}")

        livekit_dispatch_success = False
        sip_dispatched = False

        if (
            self.livekit_url
            and self.api_key
            and self.api_secret
            and "your_" not in self.api_key
        ):
            try:
                from livekit import api

                lkapi = api.LiveKitAPI(
                    self.livekit_url,
                    self.api_key,
                    self.api_secret,
                )
                # Create room with metadata
                await lkapi.room.create_room(
                    api.CreateRoomRequest(
                        name=room_name,
                        metadata=room_metadata,
                        empty_timeout=300,
                    )
                )
                livekit_dispatch_success = True

                # Dispatch agent worker 'my-agent' to the outbound room
                try:
                    agent_dispatch = await lkapi.agent_dispatch.create_dispatch(
                        api.CreateAgentDispatchRequest(
                            agent_name="my-agent",
                            room=room_name,
                            metadata=room_metadata,
                        )
                    )
                    logger.info(
                        f"🤖 AGENT WORKER DISPATCHED: Dispatch ID '{agent_dispatch.id}' assigned to room '{room_name}'"
                    )
                except Exception as dispatch_err:
                    logger.warning(
                        f"⚠️ Agent dispatch warning (worker may auto-dispatch): {dispatch_err}"
                    )

                # Check for SIP authentication credentials in env
                sip_auth_user = os.getenv(
                    "SIP_AUTH_USERNAME", os.getenv("LINPHONE_USERNAME", "")
                )
                sip_auth_pass = os.getenv(
                    "SIP_AUTH_PASSWORD", os.getenv("LINPHONE_PASSWORD", "")
                )

                if sip_trunk_id:
                    res = await lkapi.sip.create_sip_participant(
                        api.CreateSIPParticipantRequest(
                            sip_trunk_id=sip_trunk_id,
                            sip_call_to=clean_call_to,
                            room_name=room_name,
                            participant_identity=clean_identity,
                            participant_name=patient_name,
                            play_ringtone=True,
                        )
                    )
                    sip_dispatched = True
                    logger.info(
                        f"✅ TELEPHONY RINGING: LiveKit SIP Participant dispatched successfully! ID: {res.participant_id}"
                    )
                    logger.info(
                        f"   Calling '{clean_call_to}' via SIP Trunk '{sip_trunk_id}'"
                    )
                elif sip_auth_user and sip_auth_pass:
                    inline_trunk = api.SIPOutboundConfig(
                        hostname="sip.linphone.org",
                        auth_username=sip_auth_user,
                        auth_password=sip_auth_pass,
                    )
                    res = await lkapi.sip.create_sip_participant(
                        api.CreateSIPParticipantRequest(
                            trunk=inline_trunk,
                            sip_call_to=clean_call_to,
                            room_name=room_name,
                            participant_identity=clean_identity,
                            participant_name=patient_name,
                            play_ringtone=True,
                        )
                    )
                    sip_dispatched = True
                    logger.info(
                        f"✅ TELEPHONY RINGING: Authenticated Linphone SIP Participant dispatched! ID: {res.participant_id}"
                    )
                    logger.info(
                        f"   Calling '{clean_call_to}' via Inline Trunk (User: {sip_auth_user})"
                    )
                else:
                    logger.warning(
                        "⚠️ SIP_TRUNK_ID is not configured in backend/.env.local!"
                    )
                    logger.warning(
                        "   To make a real phone call ring on a mobile phone (Twilio) or Linphone softphone:"
                    )
                    logger.warning(
                        "   1. Create an Outbound SIP Trunk in LiveKit Cloud Console."
                    )
                    logger.warning(
                        "   2. Add SIP_TRUNK_ID=ST_xxxx to backend/.env.local."
                    )
                    logger.warning(
                        "   3. Re-run: uv run python make_call.py --phone 'viral'"
                    )

                await lkapi.aclose()
            except Exception as e:
                logger.error(f"❌ LIVEKIT SIP DISPATCH ERROR: {e}")

        logger.info("=" * 70)

        return {
            "call_id": call_id,
            "room_name": room_name,
            "phone_number": phone_number,
            "patient_name": patient_name,
            "reminder_type": reminder_type,
            "status": "initiated",
            "sip_trunk_id": sip_trunk_id,
            "sip_dispatched": sip_dispatched,
            "livekit_dispatched": livekit_dispatch_success,
        }

    def record_call_outcome(
        self,
        call_id: str,
        phone_number: str,
        outcome: str,
        current_retry_count: int = 0,
    ) -> dict[str, Any]:
        """Record the call session outcome and calculate next retry if needed."""
        if outcome == "opt_out":
            db.register_opt_out(
                phone_number, reason="User requested opt-out during outbound call"
            )
            db.update_call_outcome(call_id, outcome="opt_out", next_retry_iso=None)
            logger.info(
                f"🛑 Call {call_id}: User opted out. Marked in opt-out registry."
            )
            return {"status": "opt_out", "next_retry_at": None}

        next_retry_iso = calculate_next_retry(
            outcome, current_retry_count=current_retry_count
        )
        db.update_call_outcome(call_id, outcome=outcome, next_retry_iso=next_retry_iso)

        logger.info(f"📊 Call {call_id} Outcome: {outcome.upper()}")
        if next_retry_iso:
            logger.info(f"🔄 Retry scheduled at: {next_retry_iso}")
        else:
            logger.info("✅ Call processing complete (No retries scheduled).")

        return {
            "call_id": call_id,
            "outcome": outcome,
            "next_retry_at": next_retry_iso,
        }


async def trigger_outbound_call(
    phone_number: str,
    patient_name: str,
    reminder_type: str = "Medication Follow-up",
    sip_trunk_id: str = "",
) -> dict[str, Any]:
    """Convenience helper to trigger an outbound call."""
    manager = OutboundCallManager()
    return await manager.initiate_outbound_call(
        phone_number=phone_number,
        patient_name=patient_name,
        reminder_type=reminder_type,
        sip_trunk_id=sip_trunk_id,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Trigger an Outbound Call for Arogya Seva Telehealth Assistant (Day 6)"
    )
    parser.add_argument(
        "--phone",
        type=str,
        default="+919876543210",
        help="Target phone number or SIP URI",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Ramesh Kumar",
        help="Patient full name",
    )
    parser.add_argument(
        "--reminder",
        type=str,
        default="Scheduled Medication & Vaccination Follow-up",
        help="Reminder description",
    )
    parser.add_argument(
        "--sip-trunk",
        type=str,
        default="",
        help="LiveKit SIP Trunk ID (optional)",
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 Launching Outbound Call Dispatch CLI (Day 6 — #VoiceForBharat)")
    res = asyncio.run(
        trigger_outbound_call(
            phone_number=args.phone,
            patient_name=args.name,
            reminder_type=args.reminder,
            sip_trunk_id=args.sip_trunk,
        )
    )
    print("\n" + "=" * 50)
    print("Outbound Call Dispatch Result:")
    print(json.dumps(res, indent=2))
    print("=" * 50 + "\n")
