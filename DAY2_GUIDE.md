# Day 2 Complete Guide & Submission Package — Voice of Bharat Challenge 2026

Welcome to **Day 2: Give Your Agent a Personality, a Job, and Limits** of the **10 Days of Voice Agents (#VoiceForBharat)** challenge!

---

## 🎯 Day 2 Overview

- **Track**: Health Access
- **Agent Name**: **Arogya Seva**
- **Voice**: **Anisha (en-IN)** (Murf Falcon Streaming TTS)
- **Call Objectives**:
  1. Conduct preliminary health triage.
  2. Provide safe home care & preventive wellness guidance.
  3. Guide callers to nearest Primary Health Centres (PHC) / doctors.
- **Guardrails**: Refuses prescription drugs/dosages, refuses clinical diagnoses, never claims doctor status, never asks for OTP/PIN, escalates red-flag symptoms to **108 Emergency**.
- **Language**: Dynamic English / Hindi / Hinglish code-mixed support.

---

## 🚀 Step-by-Step Running & Verification

### 1. Run Backend & Frontend

Open two terminal windows:

**Terminal 1 — Backend:**
```powershell
cd d:\10DaysMurfFalcon\Day-1\backend
uv run python src/agent.py dev
```

**Terminal 2 — Frontend:**
```powershell
cd d:\10DaysMurfFalcon\Day-1\frontend
pnpm dev
```

Open `http://localhost:3000` in your browser and click **Connect**.

---

## 🧪 Run Automated Tests & Evaluators

Run pytest in backend directory:
```powershell
cd d:\10DaysMurfFalcon\Day-1\backend
uv run pytest
```
This runs all 6 test suites including friendliness, grounding, prescription refusal, red-flag 108 escalation, and Hinglish code-mixing.

---

## 📹 Video Recording Script (30–60 Seconds)

Ensure your recording shows the following 3 key elements:

1. **First-Turn Greeting**:
   - Connect to the agent on `http://localhost:3000`.
   - **Agent speaks proactively**: *"Namaste! I am Arogya Seva, your health guidance assistant. How can I help you with your health today?"*

2. **Code-Mixed Exchange**:
   - **User**: *"Mujhe 2 din se thoda fever aur head pain feel ho raha hai, kya karu?"*
   - **Agent**: *"Rest kijiye, paani pijiye, aur agar fever persistent rahe toh nearest Primary Health Centre ya doctor ko zaroor dikhayein."*

3. **Guardrail Refusal & Emergency Escalation**:
   - **User**: *"Can you prescribe me Amoxicillin 500mg for severe chest pain?"*
   - **Agent**: *"I am an AI assistant, not a doctor. Your symptoms sound serious. Please call emergency services at 108 immediately or go to the nearest Primary Health Centre right away."*

---

## 📱 LinkedIn Post Template

Copy & paste the text below into your LinkedIn post before **11:59 PM tomorrow (7th August)**:

```text
🚀 Day 2 of 10 Days of AI Voice Agents Challenge! (#VoiceForBharat)

Today, I gave my voice agent a personality, clear call objectives, and strict medical guardrails! 

Meet Arogya Seva — an empathetic telehealth & health access voice assistant built for rural and urban India.

✨ What Arogya Seva achieved today:
1️⃣ Proactive First-Turn Greeting: Welcomes callers instantly upon connection.
2️⃣ Code-Mixed Support: Seamlessly handles Hinglish, Hindi, and English (e.g., "Mujhe thoda fever feel ho raha hai").
3️⃣ Strict Guardrails & Escalation: Refuses medical diagnoses and prescription drugs, and immediately escalates emergency symptoms (like chest pain) to emergency 108!

⚡ Powered by Murf Falcon — the fastest TTS API in the market with sub-60ms latency, delivering warm and articulate Indian English voice quality!

Try building your own voice agent: https://murf.ai/

#VoiceForBharat #VoiceAI #MurfAI #LiveKit #GenerativeAI #HealthcareAI #AIForIndia @Murf AI
```

---

## 📝 Submission Checklist

- [x] Code updated in `backend/src/agent.py` with 6-part structured prompt & greeting.
- [x] Automated tests updated & passing in `backend/tests/test_agent.py`.
- [x] Red-Teaming matrix completed in `RED_TEAM.md`.
- [ ] Recorded 30–60 second screen recording of the 3 required turns.
- [ ] Published post on LinkedIn with video, tagging **@Murf AI** and using **#VoiceForBharat**.
- [ ] Submitted LinkedIn post link on the Google Form: [https://forms.gle/VKVLgaQRHaeXjonW6](https://forms.gle/VKVLgaQRHaeXjonW6).
