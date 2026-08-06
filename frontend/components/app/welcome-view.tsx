import { Button } from '@/components/ui/button';

function CyberOrbIcon() {
  return (
    <div className="relative my-4 flex size-28 items-center justify-center">
      {/* Outer rotating neon ring */}
      <div className="animate-spin-slow absolute inset-0 rounded-full border border-dashed border-cyan-500/40" />
      {/* Inner reverse rotating ring */}
      <div className="animate-spin-reverse absolute inset-2 rounded-full border border-dotted border-violet-500/50" />
      {/* Glowing pulsing core */}
      <div className="animate-pulse-glow relative flex size-16 items-center justify-center rounded-full bg-gradient-to-tr from-cyan-500 via-teal-400 to-indigo-500 text-slate-950 shadow-[0_0_40px_rgba(6,182,212,0.6)]">
        <svg
          width="32"
          height="32"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" y1="19" x2="12" y2="22" />
        </svg>
      </div>
    </div>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="relative z-10 mx-auto w-full max-w-2xl px-4 py-6 font-sans">
      {/* Outer Cyber Grid Container */}
      <section className="cyber-card relative flex flex-col items-center justify-center rounded-3xl p-8 text-center shadow-2xl transition-all duration-300 md:p-10">
        {/* HUD Top Bar */}
        <div className="mb-6 flex w-full items-center justify-between border-b border-cyan-500/20 pb-3 font-mono text-[10px] text-cyan-400/80">
          <div className="flex items-center gap-1.5">
            <span className="size-2 animate-ping rounded-full bg-cyan-400" />
            <span>SYS.STATUS // ONLINE</span>
          </div>
          <div>#VoiceForBharat · DAY 01</div>
          <div>LATENCY: 55MS</div>
        </div>

        {/* Track & Badge */}
        <div className="mb-2 flex flex-wrap items-center justify-center gap-2">
          <span className="rounded-md border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 font-mono text-[11px] font-semibold tracking-wider text-cyan-300">
            TRACK: HEALTH ACCESS
          </span>
          <span className="rounded-md border border-violet-500/30 bg-violet-500/10 px-3 py-1 font-mono text-[11px] font-semibold tracking-wider text-violet-300">
            MODEL: MURF FALCON 2
          </span>
        </div>

        <CyberOrbIcon />

        {/* Cyber Hero Title */}
        <h1 className="mb-2 bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400 bg-clip-text font-mono text-3xl font-black tracking-tight text-transparent uppercase md:text-4xl">
          Arogya Seva // Voice AI
        </h1>

        <p className="mb-6 max-w-md font-mono text-xs leading-relaxed text-slate-400 md:text-sm">
          Empathetic rural telehealth assistant powered by{' '}
          <span className="font-semibold text-cyan-300 underline decoration-cyan-500/50">
            Murf Falcon TTS
          </span>{' '}
          with real-time streaming audio pipeline.
        </p>

        {/* HUD Specs Matrix */}
        <div className="mb-6 grid w-full max-w-lg grid-cols-3 gap-2.5 text-left font-mono">
          <div className="rounded-lg border border-cyan-500/20 bg-slate-950/70 p-2.5">
            <div className="text-[10px] font-bold tracking-wider text-cyan-400 uppercase">
              VOICE ENGINE
            </div>
            <div className="text-xs font-semibold text-slate-200">Murf Falcon 2</div>
          </div>
          <div className="rounded-lg border border-violet-500/20 bg-slate-950/70 p-2.5">
            <div className="text-[10px] font-bold tracking-wider text-violet-400 uppercase">
              INDIAN VOICE
            </div>
            <div className="text-xs font-semibold text-slate-200">Anisha (en-IN)</div>
          </div>
          <div className="rounded-lg border border-teal-500/20 bg-slate-950/70 p-2.5">
            <div className="text-[10px] font-bold tracking-wider text-teal-400 uppercase">
              METRICS
            </div>
            <div className="text-xs font-semibold text-slate-200">Logged (E2E)</div>
          </div>
        </div>

        {/* Terminal Window - Voice Justification */}
        <div className="mb-6 w-full max-w-lg rounded-xl border border-cyan-500/30 bg-slate-950/90 p-3.5 text-left font-mono text-xs shadow-inner">
          <div className="mb-2 flex items-center gap-1.5 border-b border-slate-800 pb-1.5 text-[11px] text-cyan-400">
            <span className="size-2 rounded-full bg-red-500/80" />
            <span className="size-2 rounded-full bg-yellow-500/80" />
            <span className="size-2 rounded-full bg-green-500/80" />
            <span className="ml-1 text-slate-400">terminal@voiceforbharat:~$ rationale.log</span>
          </div>
          <p className="text-[11px] leading-relaxed text-cyan-300">
            <span className="text-slate-500">
              &gt; sys.select_voice(&quot;Anisha&quot;, locale=&quot;en-IN&quot;)
            </span>
            <br />
            <span className="text-slate-300">
              &gt; RATIONALE: &quot;Anisha&apos;s calm, articulate Indian English voice instils
              medical trust, clarity, and reassurance for rural callers.&quot;
            </span>
          </p>
        </div>

        {/* Sample Prompt Chips */}
        <div className="mb-6 w-full max-w-lg text-left">
          <div className="mb-2 font-mono text-[10px] font-bold tracking-widest text-cyan-400 uppercase">
            {/* TRY ASKING AROGYA SEVA: */}
            &#47;&#47; TRY ASKING AROGYA SEVA:
          </div>

          <div className="flex flex-wrap gap-2 font-mono text-xs">
            <span className="rounded-md border border-cyan-500/30 bg-slate-900/80 px-3 py-1.5 text-slate-300">
              &quot;What should I do for a mild fever?&quot;
            </span>
            <span className="rounded-md border border-cyan-500/30 bg-slate-900/80 px-3 py-1.5 text-slate-300">
              &quot;When should I visit the nearest PHC?&quot;
            </span>
          </div>
        </div>

        {/* Futuristic Cyber Start Button */}
        <Button
          size="lg"
          onClick={onStartCall}
          className="w-full rounded-xl bg-gradient-to-r from-cyan-500 via-teal-400 to-indigo-500 py-6 font-mono text-xs font-bold tracking-widest text-slate-950 uppercase shadow-[0_0_30px_rgba(6,182,212,0.4)] transition-all duration-300 hover:scale-105 hover:shadow-[0_0_45px_rgba(6,182,212,0.7)] md:w-80"
        >
          [ {startButtonText.toUpperCase()} ]
        </Button>
      </section>

      {/* Footer */}
      <div className="mt-4 flex w-full items-center justify-center font-mono">
        <p className="text-center text-[11px] text-slate-500">
          10 DAYS OF VOICE AGENTS — POWERED BY{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://murf.ai/api/docs/text-to-speech-models/falcon-2"
            className="font-bold text-cyan-400 underline hover:text-cyan-300"
          >
            MURF AI (FALCON 2)
          </a>
        </p>
      </div>
    </div>
  );
};
