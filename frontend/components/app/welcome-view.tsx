import { useState } from 'react';
import {
  Heartbeat,
  PhoneDisconnect,
  PhoneOutgoing,
  ShieldCheck,
  Translate,
} from '@phosphor-icons/react';
import { OutboundModal } from '@/components/app/outbound-modal';
import { Button } from '@/components/ui/button';

function CyberOrbIcon({ isCallEnded }: { isCallEnded?: boolean }) {
  return (
    <div className="relative my-4 flex size-28 items-center justify-center">
      {/* Outer rotating ring */}
      <div
        className={`absolute inset-0 rounded-full border border-dashed ${
          isCallEnded
            ? 'animate-spin-slow border-amber-500/40'
            : 'animate-spin-slow border-emerald-500/40'
        }`}
      />
      {/* Inner reverse rotating ring */}
      <div
        className={`absolute inset-2 rounded-full border border-dotted ${
          isCallEnded
            ? 'animate-spin-reverse border-red-500/50'
            : 'animate-spin-reverse border-teal-500/50'
        }`}
      />
      {/* Glowing pulsing core */}
      <div
        className={`relative flex size-16 items-center justify-center rounded-full text-slate-950 shadow-lg ${
          isCallEnded
            ? 'animate-pulse bg-gradient-to-tr from-amber-500 via-orange-400 to-red-500 shadow-[0_0_40px_rgba(245,158,11,0.6)]'
            : 'animate-pulse-glow bg-gradient-to-tr from-emerald-500 via-teal-400 to-cyan-500 shadow-[0_0_40px_rgba(16,185,129,0.6)]'
        }`}
      >
        {isCallEnded ? (
          <PhoneDisconnect size={30} weight="bold" className="text-slate-950" />
        ) : (
          <Heartbeat size={32} weight="bold" className="text-slate-950" />
        )}
      </div>
    </div>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  onDispatchOutboundCall?: (token: string, roomName: string, serverUrl: string) => void;
  isCallEnded?: boolean;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  onDispatchOutboundCall,
  isCallEnded = false,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const [isOutboundModalOpen, setIsOutboundModalOpen] = useState(false);

  return (
    <div ref={ref} className="relative z-10 mx-auto w-full max-w-2xl px-4 py-6 font-sans">
      {/* Outer Health Access Container */}
      <section className="cyber-card relative flex flex-col items-center justify-center rounded-3xl p-8 text-center shadow-2xl transition-all duration-300 md:p-10">
        {/* HUD Top Bar */}
        <div className="mb-6 flex w-full items-center justify-between border-b border-emerald-500/20 pb-3 font-mono text-[10px] text-emerald-400/90">
          <div className="flex items-center gap-1.5">
            <span
              className={`size-2 rounded-full ${
                isCallEnded ? 'bg-amber-400' : 'animate-ping bg-emerald-400'
              }`}
            />
            <span>
              SYS.STATUS // {isCallEnded ? 'CALL ENDED (DISCONNECTED)' : 'READY (ONLINE)'}
            </span>
          </div>
          <div>#VoiceForBharat · DAY 06</div>
          <div className="flex items-center gap-1 text-teal-300">
            <ShieldCheck size={14} weight="fill" />
            <span>MURF FALCON TTS</span>
          </div>
        </div>

        {/* Track & Multilingual Badges */}
        <div className="mb-2 flex flex-wrap items-center justify-center gap-2">
          <span className="rounded-md border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 font-mono text-[11px] font-semibold tracking-wider text-emerald-300">
            TRACK: HEALTH ACCESS
          </span>
          <span className="rounded-md border border-teal-500/30 bg-teal-500/10 px-3 py-1 font-mono text-[11px] font-semibold tracking-wider text-teal-300">
            VOICE: ANISHA (MURF FALCON 2)
          </span>
          <span className="flex items-center gap-1 rounded-md border border-purple-500/30 bg-purple-500/10 px-2.5 py-1 font-mono text-[11px] font-semibold tracking-wider text-purple-300">
            <PhoneOutgoing size={14} /> DAY 06: OUTBOUND CALLS
          </span>
        </div>

        <CyberOrbIcon isCallEnded={isCallEnded} />

        {/* Hero Title & State Status */}
        {isCallEnded ? (
          <>
            <div className="mb-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-1.5 font-mono text-xs font-bold tracking-widest text-amber-300 uppercase">
              [ AGENT STATE: CALL ENDED ]
            </div>
            <h1 className="mb-2 bg-gradient-to-r from-amber-300 via-orange-300 to-red-400 bg-clip-text font-mono text-3xl font-black tracking-tight text-transparent uppercase md:text-4xl">
              Consultation Complete
            </h1>
            <p className="mb-6 max-w-md font-mono text-xs leading-relaxed text-slate-300 md:text-sm">
              Your health guidance session with Arogya Seva has ended. You can start a new
              consultation or trigger an outbound call.
            </p>
          </>
        ) : (
          <>
            <div className="mb-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-1.5 font-mono text-xs font-bold tracking-widest text-emerald-300 uppercase">
              [ AGENT STATE: READY ]
            </div>
            <h1 className="mb-2 bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text font-mono text-3xl font-black tracking-tight text-transparent uppercase md:text-4xl">
              Arogya Seva // Outbound AI
            </h1>
            <p className="mb-6 max-w-md font-mono text-xs leading-relaxed text-slate-300 md:text-sm">
              Empathetic telehealth & health follow-up voice assistant for Bharat powered by{' '}
              <span className="font-semibold text-emerald-300 underline decoration-emerald-500/50">
                Murf Falcon TTS
              </span>
              .
            </p>
          </>
        )}

        {/* Specs Matrix */}
        <div className="mb-6 grid w-full max-w-lg grid-cols-3 gap-2.5 text-left font-mono">
          <div className="rounded-lg border border-emerald-500/20 bg-slate-950/70 p-2.5">
            <div className="text-[10px] font-bold tracking-wider text-emerald-400 uppercase">
              SPEECH ENGINE
            </div>
            <div className="text-xs font-semibold text-slate-200">Murf Falcon 2</div>
          </div>
          <div className="rounded-lg border border-teal-500/20 bg-slate-950/70 p-2.5">
            <div className="text-[10px] font-bold tracking-wider text-teal-400 uppercase">
              OUTBOUND SIP
            </div>
            <div className="text-xs font-semibold text-teal-300">LiveKit / Twilio</div>
          </div>
          <div className="rounded-lg border border-cyan-500/20 bg-slate-950/70 p-2.5">
            <div className="text-[10px] font-bold tracking-wider text-cyan-400 uppercase">
              GUARDRAIL
            </div>
            <div className="text-xs font-semibold text-emerald-400">Step 4 Compliant</div>
          </div>
        </div>

        {/* Action Buttons: Inbound vs Outbound */}
        <div className="flex w-full max-w-lg flex-col gap-3 sm:flex-row">
          <Button
            size="lg"
            onClick={onStartCall}
            className={`flex-1 rounded-xl py-6 font-mono text-xs font-bold tracking-widest text-slate-950 uppercase shadow-lg transition-all duration-300 hover:scale-105 ${
              isCallEnded
                ? 'bg-gradient-to-r from-amber-400 via-emerald-400 to-teal-400 shadow-[0_0_30px_rgba(245,158,11,0.4)]'
                : 'bg-gradient-to-r from-emerald-400 via-teal-400 to-cyan-400 shadow-[0_0_30px_rgba(16,185,129,0.4)]'
            }`}
          >
            [ {isCallEnded ? 'INBOUND CALL' : startButtonText.toUpperCase()} ]
          </Button>

          <Button
            size="lg"
            variant="outline"
            onClick={() => setIsOutboundModalOpen(true)}
            className="flex-1 rounded-xl border border-teal-500/50 bg-slate-900/80 py-6 font-mono text-xs font-bold tracking-widest text-teal-300 uppercase shadow-lg transition-all duration-300 hover:scale-105 hover:bg-slate-800 hover:text-teal-200"
          >
            <span className="flex items-center justify-center gap-2">
              <PhoneOutgoing size={18} weight="bold" /> DISPATCH OUTBOUND CALL
            </span>
          </Button>
        </div>
      </section>

      {/* Outbound Dispatch Modal */}
      <OutboundModal
        isOpen={isOutboundModalOpen}
        onClose={() => setIsOutboundModalOpen(false)}
        onDispatchOutbound={(token, roomName, serverUrl) => {
          if (onDispatchOutboundCall) {
            onDispatchOutboundCall(token, roomName, serverUrl);
          } else {
            onStartCall();
          }
        }}
      />

      {/* Footer */}
      <div className="mt-4 flex w-full items-center justify-center font-mono">
        <p className="text-center text-[11px] text-slate-500">
          10 DAYS OF VOICE AGENTS — POWERED BY{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://murf.ai/api/docs/text-to-speech-models/falcon-2"
            className="font-bold text-emerald-400 underline hover:text-emerald-300"
          >
            MURF AI (FALCON 2)
          </a>
        </p>
      </div>
    </div>
  );
};
