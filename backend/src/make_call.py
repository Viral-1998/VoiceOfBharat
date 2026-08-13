import argparse
import asyncio
import json
import logging
import os
import sys

from dotenv import load_dotenv

# Ensure backend/src is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telephony.outbound import trigger_outbound_call

load_dotenv(".env.local")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("make_call")


async def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Day 6 Telephony Outbound Call Dispatcher (#VoiceForBharat)"
    )
    parser.add_argument(
        "--phone",
        type=str,
        default=os.getenv("TEST_PHONE_NUMBER", "+919876543210"),
        help="Recipient phone number (E.164 format e.g. +919876543210) or Linphone SIP URI",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Ramesh Kumar",
        help="Recipient full name",
    )
    parser.add_argument(
        "--reminder",
        type=str,
        default="Scheduled Medication & Vaccination Follow-up",
        help="Outbound call reminder purpose",
    )
    parser.add_argument(
        "--sip-trunk",
        type=str,
        default=os.getenv("SIP_TRUNK_ID", ""),
        help="LiveKit Outbound SIP Trunk ID (e.g. ST_xxxx)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 75)
    print("🚀 10 DAYS OF VOICE AGENTS — DAY 6: MAKE OUTBOUND CALLS (#VoiceForBharat)")
    print("   Track: Health Access (Arogya Seva Telehealth Voice Assistant)")
    print("   Voice Engine: Murf Falcon TTS (Anisha)")
    print("=" * 75)

    print(f"\n📞 Initiating Outbound Call Dispatch to: {args.name} ({args.phone})")
    print(f"📋 Reason / Reminder: {args.reminder}")

    if args.sip_trunk:
        print(f"🔑 Using LiveKit SIP Trunk ID: {args.sip_trunk}")
    else:
        print("\n⚠️  NOTICE: No SIP_TRUNK_ID provided in CLI or backend/.env.local!")
        print(
            "   To make an actual phone ring on a mobile phone (Twilio) or Linphone softphone:"
        )
        print(
            "   1. Create an Outbound SIP Trunk in LiveKit Cloud Console (https://cloud.livekit.io/)."
        )
        print("   2. Add SIP_TRUNK_ID=ST_xxxx to backend/.env.local")
        print("   3. Re-run: uv run python src/make_call.py --phone '+919876543210'\n")

    res = await trigger_outbound_call(
        phone_number=args.phone,
        patient_name=args.name,
        reminder_type=args.reminder,
        sip_trunk_id=args.sip_trunk,
    )

    print("-" * 75)
    print("Dispatch Result Summary:")
    print(json.dumps(res, indent=2))
    print("-" * 75 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
