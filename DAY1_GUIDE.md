# 🎙️ Day 1: Get Your Voice Agent Talking — #VoiceForBharat Edition

Welcome to **Day 1** of **10 Days of Voice Agents — #VoiceForBharat Edition**! 

---

## 🎯 Day 1 Overview & Setup Summary

| Requirement | Implementation Detail |
| :--- | :--- |
| **Track Picked** | **Health Access** (Arogya Seva Telehealth & Rural Health Assistant) |
| **Voice Model** | **Murf Falcon TTS** (`55ms` model latency, streaming speech) |
| **Voice Selected** | **Anisha (`en-IN`)** — Indian English Voice |
| **Voice Justification** | *"Anisha's calm, articulate, and warm Indian English tone instils medical trust, clarity, and reassurance essential for rural telehealth guidance."* |
| **Latency Tracking** | Built-in logging in Python backend (`[LATENCY LOG] End-of-user-speech to first audio output`) |
| **Tech Stack** | Python (LiveKit Agents + Murf Falcon TTS + Deepgram STT + Gemini LLM) & Next.js HTML/CSS/JS Frontend |

---

## 🔑 Step 1: Add Your API Keys

Copy your API keys into `backend/.env.local` and `frontend/.env.local`:

### 1. `backend/.env.local`
```env
LIVEKIT_URL=wss://<your-project>.livekit.cloud
LIVEKIT_API_KEY=<your-livekit-api-key>
LIVEKIT_API_SECRET=<your-livekit-api-secret>
MURF_API_KEY=<your-murf-api-key>
DEEPGRAM_API_KEY=<your-deepgram-api-key>
GOOGLE_API_KEY=<your-gemini-api-key>
```

### 2. `frontend/.env.local`
```env
LIVEKIT_URL=wss://<your-project>.livekit.cloud
LIVEKIT_API_KEY=<your-livekit-api-key>
LIVEKIT_API_SECRET=<your-livekit-api-secret>
AGENT_NAME=my-agent
```

> 🔗 **Where to get keys:**
> - **Murf API Key**: [murf.ai/api/dashboard](https://murf.ai/api/dashboard)
> - **LiveKit Credentials**: [cloud.livekit.io](https://cloud.livekit.io/)
> - **Deepgram Key**: [deepgram.com](https://deepgram.com)
> - **Google Gemini Key**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

## 🚀 Step 2: How to Run the App

You can run the entire app using PowerShell or separate terminals:

### Option A: All-in-One Launch (PowerShell)
```powershell
.\start_app.ps1
```

### Option B: Run in Separate Terminals
```bash
# Terminal 1 — Backend Python Agent
cd backend
uv run python src/agent.py dev

# Terminal 2 — Frontend UI
cd frontend
pnpm dev
```

Then open **`http://localhost:3000`** in your browser.

---

## 🎙️ Step 3: Test & Record Your Conversation

1. Open `http://localhost:3000`.
2. Click **Start Talking** and allow microphone access.
3. **Say out loud in your video**: *"I am building for the **Health Access** track in 10 Days of Voice Agents!"*
4. Ask a sample question like:
   - *"Hello Arogya Seva, what should I do if someone has a mild fever?"*
5. Listen to **Anisha's** fast, warm Indian English voice powered by **Murf Falcon TTS**.
6. Check your Python terminal log for the latency metric:
   `⚡ [LATENCY LOG] End-of-user-speech to first audio output: 142.50 ms`

---

## 📲 Step 4: Share on LinkedIn & Submit

### 📢 LinkedIn Post Template
> **Day 1 of 10 Days of Voice Agents — #VoiceForBharat Edition! 🚀**
>
> Today I built **Arogya Seva**, a rural telehealth voice agent for the **Health Access** track! 🏥✨
>
> 🎙️ **Voice Choice**: Powered by @Murf AI's fastest TTS API — **Murf Falcon** using the **Anisha (en-IN)** voice. Its calm, articulate Indian English tone builds immediate medical trust and clarity for callers.
> 
> ⚡ **Performance**: Ultra-low end-to-end latency (~140ms time-to-first-audio)!
>
> #VoiceForBharat #VoiceAI #MurfAI #MurfFalcon #AI #Healthcare #BuildInPublic

### 📝 Submission Checklist
- [x] Repo set to **Public** on GitHub.
- [ ] Recorded short video talking to agent (saying track out loud).
- [ ] Posted on LinkedIn tagging **@Murf AI** with `#VoiceForBharat`.
- [ ] Submitted LinkedIn post link on the submission form on Discord.
