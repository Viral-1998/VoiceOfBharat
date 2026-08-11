# Outbound Telephony & SIP Calling Guide — Day 6 (#VoiceForBharat)

This guide explains how to configure and trigger real telephony outbound calls for **Arogya Seva** (the Health Access telehealth voice assistant powered by **Murf Falcon TTS**).

---

## Architecture Overview

```mermaid
flowchart LR
    A[make_call.py / Next.js UI] -->|create_sip_participant| B[LiveKit Cloud API]
    B -->|SIP Outbound Trunk| C[Twilio / Linphone SIP Provider]
    C -->|PSTN / IP Ringing| D[User Phone / Softphone App]
    D -->|Answers Call| E[Arogya Seva Voice Agent]
    E -->|Step 4 Opening| F["(1) Who & Why\n(2) How to Opt-Out"]
```

---

## Option A: Real Mobile Phone Calls via Twilio SIP Trunk

### Step 1: Create Outbound SIP Trunk in LiveKit Cloud
1. Go to your [LiveKit Cloud Console](https://cloud.livekit.io/).
2. Navigate to **Telephony** → **Outbound Trunks** → **Create Outbound Trunk**.
3. Select **Twilio** as your SIP Trunk Provider.
4. Enter your Twilio Termination Domain, SIP Username, and Password.
5. Save the trunk and copy the generated **Trunk ID** (starts with `ST_...`).

### Step 2: Add Trunk ID to Environment Files
Copy your Trunk ID into both `backend/.env.local` and `frontend/.env.local`:
```env
SIP_TRUNK_ID=ST_your_trunk_id_here
```

### Step 3: Trigger Outbound Call via CLI
Run the standalone outbound call script from the `backend/` directory:
```bash
cd backend
uv run python make_call.py --phone "+919876543210" --name "Ramesh Kumar" --reminder "Medication & Polio Vaccination Follow-up"
```
The user's mobile phone will ring. When they pick up, **Arogya Seva** speaks the Step 4 compliant opening greeting!

---

## Option B: Free Outbound Calls via Linphone (SIP Softphone)

If your Twilio trial balance is exhausted, you can use **Linphone** for free outbound SIP testing over WiFi/IP:

### Step 1: Install Linphone
1. Download and install [Linphone Softphone App](https://linphone.org/) on your desktop or smartphone.
2. Create a free SIP account (e.g. `your_name@sip.linphone.org`).

### Step 2: Configure Linphone SIP Trunk in LiveKit Cloud
1. In LiveKit Cloud Console → **Telephony** → **Outbound Trunks** → **Create Outbound Trunk**.
2. Set Address: `sip.linphone.org`.
3. Save and copy the generated Trunk ID (`ST_...`).

### Step 3: Call your Linphone SIP URI
```bash
cd backend
uv run python make_call.py --phone "sip:your_name@sip.linphone.org" --name "Ramesh Kumar"
```
Your Linphone application will ring like an incoming phone call!

---

## Option C: Browser UI Local Simulator (Instant Testing)

If you are testing without an active SIP trunk:
1. Start the backend: `cd backend && uv run python src/agent.py dev`
2. Start the frontend: `cd frontend && pnpm dev`
3. Open `http://localhost:3000` in your browser.
4. Click **`[ DISPATCH OUTBOUND CALL ]`**, enter patient details, and click **DISPATCH CALL NOW**.
5. The session will open directly in your browser microphone/audio, playing the exact Step 4 opening greeting.

---

## Step 4 Compliance Checklist

Every outbound call delivers:
- **Sentence 1 (Who & Why)**: *"Namaste Ramesh Kumar, this is Arogya Seva calling from your District Health Centre regarding your scheduled medication follow-up and vaccination reminder."*
- **Sentence 2 (Opt-Out)**: *"If you wish to stop receiving these outbound health reminders at any time, please say 'opt out' or press 9 to unsubscribe."*
- **Native Script Adherence**: Non-English responses render in native script (Hindi → Devanagari **नमस्ते**).
- **Opt-Out Action**: Saying *"opt out"* calls `@function_tool opt_out_caller` and persists the preference in SQLite `opt_out_registry`.
