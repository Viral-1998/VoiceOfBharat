'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import { useAgent, useSessionContext, useSessionMessages } from '@livekit/components-react';
import { Brain, Microphone, ShieldCheck, SpeakerHigh, SpinnerGap } from '@phosphor-icons/react';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { Shimmer } from '@/components/ai-elements/shimmer';
import { MicPermissionModal } from '@/components/app/mic-permission-modal';
import { cn } from '@/lib/shadcn/utils';
import { TileLayout } from './tile-view';

const MotionMessage = motion.create(Shimmer);

const BOTTOM_VIEW_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      translateY: '0%',
    },
    hidden: {
      opacity: 0,
      translateY: '100%',
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.3,
    delay: 0.5,
    ease: 'easeOut',
  },
};

const CHAT_MOTION_PROPS: MotionProps = {
  variants: {
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeOut',
        duration: 0.3,
      },
    },
    visible: {
      opacity: 1,
      transition: {
        delay: 0.2,
        ease: 'easeOut',
        duration: 0.3,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

const SHIMMER_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0.8,
      },
    },
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

interface FadeProps {
  top?: boolean;
  bottom?: boolean;
  className?: string;
}

export function Fade({ top = false, bottom = false, className }: FadeProps) {
  return (
    <div
      className={cn(
        'from-background pointer-events-none h-4 bg-linear-to-b to-transparent',
        top && 'bg-linear-to-b',
        bottom && 'bg-linear-to-t',
        className
      )}
    />
  );
}

export interface AgentSessionView_01Props {
  preConnectMessage?: string;
  supportsChatInput?: boolean;
  supportsVideoInput?: boolean;
  supportsScreenShare?: boolean;
  isPreConnectBufferEnabled?: boolean;
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;
  className?: string;
}

export function AgentSessionView_01({
  preConnectMessage = 'Arogya Seva is listening, ask your health query...',
  supportsChatInput = true,
  supportsVideoInput = false,
  supportsScreenShare = false,
  isPreConnectBufferEnabled = true,

  audioVisualizerType = 'aura',
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,
  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const [chatOpen, setChatOpen] = useState(true); // Open live transcript by default for Day 3 live transcript requirement
  const [micErrorOpen, setMicErrorOpen] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { state: agentState } = useAgent();

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  useEffect(() => {
    const lastMessage = messages.at(-1);
    const lastMessageIsLocal = lastMessage?.from?.isLocal === true;

    if (scrollAreaRef.current && lastMessageIsLocal) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  // Check microphone permissions / device errors
  const handleRetryMic = async () => {
    setMicErrorOpen(false);
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setMicErrorOpen(true);
    }
  };

  // Agent State Text & Icon Mapping for Step 2 & Step 3 Requirements
  const renderStateBadge = () => {
    if (!session.isConnected) {
      return (
        <div className="flex animate-pulse items-center gap-2 rounded-full border border-blue-500/40 bg-blue-950/80 px-4 py-1.5 font-mono text-xs font-bold text-blue-300 shadow-lg shadow-blue-500/20">
          <SpinnerGap size={16} className="animate-spin text-blue-400" />
          <span>CONNECTING TO AROGYA SEVA... PLEASE WAIT</span>
        </div>
      );
    }

    switch (agentState) {
      case 'listening':
        return (
          <div className="flex items-center gap-2 rounded-full border border-emerald-500/50 bg-emerald-950/90 px-4 py-1.5 font-mono text-xs font-bold text-emerald-300 shadow-lg shadow-emerald-500/20">
            <span className="relative flex size-2.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex size-2.5 rounded-full bg-emerald-500" />
            </span>
            <Microphone size={16} weight="fill" className="text-emerald-400" />
            <span>LISTENING TO YOU...</span>
          </div>
        );
      case 'speaking':
        return (
          <div className="flex items-center gap-2 rounded-full border border-cyan-500/50 bg-cyan-950/90 px-4 py-1.5 font-mono text-xs font-bold text-cyan-300 shadow-lg shadow-cyan-500/20">
            <SpeakerHigh size={18} weight="fill" className="animate-bounce text-cyan-400" />
            <span>AROGYA SEVA IS SPEAKING (MURF FALCON)</span>
          </div>
        );
      case 'thinking':
        return (
          <div className="flex items-center gap-2 rounded-full border border-violet-500/50 bg-violet-950/90 px-4 py-1.5 font-mono text-xs font-bold text-violet-300 shadow-lg shadow-violet-500/20">
            <Brain size={16} weight="fill" className="animate-pulse text-violet-400" />
            <span>THINKING &amp; PROCESSING...</span>
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900/90 px-4 py-1.5 font-mono text-xs font-bold text-slate-300">
            <ShieldCheck size={16} className="text-emerald-400" />
            <span>AROGYA SEVA CONNECTED</span>
          </div>
        );
    }
  };

  return (
    <section
      ref={ref}
      className={cn('bg-background relative z-10 h-full w-full overflow-hidden', className)}
      {...props}
    >
      {/* Top Banner with Day 3 Agent State Display */}
      <div className="pointer-events-none absolute inset-x-0 top-3 z-[60] flex flex-col items-center justify-center gap-2 px-4">
        <div className="pointer-events-auto flex items-center gap-2 rounded-full backdrop-blur-md">
          {renderStateBadge()}
        </div>
      </div>

      <Fade top className="absolute inset-x-4 top-0 z-10 h-32" />

      {/* Live Transcript Display */}
      <div className="absolute top-0 bottom-[135px] flex w-full flex-col md:bottom-[170px]">
        <AnimatePresence>
          {chatOpen && (
            <motion.div
              {...CHAT_MOTION_PROPS}
              className="flex h-full w-full flex-col gap-4 space-y-3 transition-opacity duration-300 ease-out"
            >
              <AgentChatTranscript
                agentState={agentState}
                messages={messages}
                className="mx-auto w-full max-w-2xl [&_.is-user>div]:rounded-[22px] [&>div>div]:px-4 [&>div>div]:pt-36 md:[&>div>div]:px-6 md:[&>div>div]:pt-44"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Tile layout with Audio Visualizer */}
      <TileLayout
        chatOpen={chatOpen}
        audioVisualizerType={audioVisualizerType}
        audioVisualizerColor={audioVisualizerColor}
        audioVisualizerColorShift={audioVisualizerColorShift}
        audioVisualizerBarCount={audioVisualizerBarCount}
        audioVisualizerRadialBarCount={audioVisualizerRadialBarCount}
        audioVisualizerRadialRadius={audioVisualizerRadialRadius}
        audioVisualizerGridRowCount={audioVisualizerGridRowCount}
        audioVisualizerGridColumnCount={audioVisualizerGridColumnCount}
        audioVisualizerWaveLineWidth={audioVisualizerWaveLineWidth}
      />

      {/* Microphone Permission Modal */}
      <MicPermissionModal
        isOpen={micErrorOpen}
        onRetry={handleRetryMic}
        onClose={() => setMicErrorOpen(false)}
      />

      {/* Bottom Controls */}
      <motion.div
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="absolute inset-x-3 bottom-0 z-50 md:inset-x-12"
      >
        {/* Pre-connect message */}
        {isPreConnectBufferEnabled && (
          <AnimatePresence>
            {messages.length === 0 && (
              <MotionMessage
                key="pre-connect-message"
                duration={2}
                aria-hidden={messages.length > 0}
                {...SHIMMER_MOTION_PROPS}
                className="pointer-events-none mx-auto block w-full max-w-2xl pb-4 text-center text-sm font-semibold text-emerald-300"
              >
                {preConnectMessage}
              </MotionMessage>
            )}
          </AnimatePresence>
        )}
        <div className="bg-background relative mx-auto max-w-2xl pb-3 md:pb-12">
          <Fade bottom className="absolute inset-x-0 top-0 h-4 -translate-y-full" />
          <AgentControlBar
            variant="livekit"
            controls={controls}
            isChatOpen={chatOpen}
            isConnected={session.isConnected}
            onDisconnect={session.end}
            onIsChatOpenChange={setChatOpen}
          />
        </div>
      </motion.div>
    </section>
  );
}
