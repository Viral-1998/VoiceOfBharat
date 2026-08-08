'use client';

import React from 'react';
import { ArrowClockwise, LockKey, MicrophoneSlash, WarningCircle } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';

interface MicPermissionModalProps {
  isOpen: boolean;
  onRetry: () => void;
  onClose?: () => void;
}

export function MicPermissionModal({ isOpen, onRetry, onClose }: MicPermissionModalProps) {
  if (!isOpen) return null;

  return (
    <div className="animate-in fade-in fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-md duration-200">
      <div className="relative w-full max-w-md overflow-hidden rounded-3xl border border-red-500/30 bg-slate-900/95 p-6 text-slate-100 shadow-2xl shadow-red-500/10 md:p-8">
        {/* Glow Header */}
        <div className="mb-4 flex items-center gap-3">
          <div className="flex size-12 items-center justify-center rounded-2xl border border-red-500/30 bg-red-500/10 text-red-400">
            <MicrophoneSlash size={26} weight="bold" />
          </div>
          <div>
            <h3 className="font-mono text-lg font-bold text-red-400">Microphone Access Blocked</h3>
            <p className="font-mono text-xs text-slate-400">Action Required to Continue</p>
          </div>
        </div>

        <p className="mb-4 font-sans text-xs leading-relaxed text-slate-300">
          Arogya Seva needs access to your microphone to hear your health questions and provide
          real-time telehealth guidance.
        </p>

        {/* Step by step guide */}
        <div className="mb-6 space-y-2.5 rounded-xl border border-slate-800 bg-slate-950/70 p-3.5 font-mono text-xs">
          <div className="flex items-start gap-2 text-slate-300">
            <LockKey size={16} className="mt-0.5 shrink-0 text-cyan-400" />
            <span>
              1. Click the <strong>Lock / Settings</strong> icon in your browser address bar.
            </span>
          </div>
          <div className="flex items-start gap-2 text-slate-300">
            <WarningCircle size={16} className="mt-0.5 shrink-0 text-emerald-400" />
            <span>
              2. Find <strong>Microphone</strong> and switch permission to <strong>Allow</strong>.
            </span>
          </div>
          <div className="flex items-start gap-2 text-slate-300">
            <ArrowClockwise size={16} className="mt-0.5 shrink-0 text-violet-400" />
            <span>
              3. Click <strong>Try Again</strong> below to re-initialize your session.
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <Button
            onClick={onRetry}
            className="flex-1 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 py-5 font-mono text-xs font-bold text-slate-950 hover:brightness-110"
          >
            <ArrowClockwise size={16} weight="bold" className="mr-1.5" />
            TRY AGAIN
          </Button>
          {onClose && (
            <Button
              variant="outline"
              onClick={onClose}
              className="rounded-xl border-slate-700 bg-slate-800/50 text-slate-300 hover:bg-slate-800"
            >
              Dismiss
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
