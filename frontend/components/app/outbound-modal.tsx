'use client';

import { useState } from 'react';
import { ArrowClockwise, CheckCircle, PhoneOutgoing, X } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';

interface OutboundModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDispatchOutbound: (token: string, roomName: string, serverUrl: string) => void;
}

export function OutboundModal({ isOpen, onClose, onDispatchOutbound }: OutboundModalProps) {
  const [patientName, setPatientName] = useState('Ramesh Kumar');
  const [phoneNumber, setPhoneNumber] = useState('+91 98765 43210');
  const [reminderType, setReminderType] = useState('Medication & Vaccination Follow-up');
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDispatch = async () => {
    setLoading(true);
    setStatusMsg('Initiating outbound call dispatch via LiveKit SIP...');
    try {
      const res = await fetch('/api/outbound', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: phoneNumber,
          patient_name: patientName,
          reminder_type: reminderType,
        }),
      });

      const data = await res.json();
      if (!res.ok || data.error) {
        throw new Error(data.error || 'Failed to dispatch call');
      }

      setStatusMsg('✅ Call Dispatched! Connecting agent session...');
      setTimeout(() => {
        onDispatchOutbound(data.participant_token, data.room_name, data.server_url);
        onClose();
      }, 800);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Outbound call dispatch failed.';
      setStatusMsg(`⚠️ Error: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-md">
      <div className="cyber-card relative w-full max-w-lg rounded-3xl border border-emerald-500/30 bg-slate-900/95 p-6 font-mono text-slate-200 shadow-2xl md:p-8">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between border-b border-emerald-500/20 pb-3">
          <div className="flex items-center gap-2 text-emerald-400">
            <PhoneOutgoing size={24} weight="bold" />
            <span className="text-sm font-bold tracking-wider uppercase">
              DAY 06 // OUTBOUND CALL DISPATCH
            </span>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200"
          >
            <X size={20} />
          </button>
        </div>

        {/* Info Banner */}
        <div className="mb-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-[11px] leading-relaxed text-emerald-300">
          <div className="mb-1 flex items-center gap-1.5 font-bold uppercase">
            <CheckCircle size={15} weight="fill" /> STEP 4 COMPLIANCE GUARDRAIL ENFORCED
          </div>
          Agent opening states: <strong>(1) Who is calling & why</strong>, and{' '}
          <strong>(2) How to opt out</strong> within first 2 sentences. Native Devanagari script
          used for Hindi.
        </div>

        {/* Inputs */}
        <div className="space-y-4 text-xs">
          <div>
            <label className="mb-1 block font-semibold text-slate-300">
              PATIENT / RECIPIENT NAME
            </label>
            <input
              type="text"
              value={patientName}
              onChange={(e) => setPatientName(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-slate-100 focus:border-emerald-400 focus:outline-none"
              placeholder="e.g. Ramesh Kumar"
            />
          </div>

          <div>
            <label className="mb-1 block font-semibold text-slate-300">
              PHONE NUMBER / SIP TARGET
            </label>
            <input
              type="text"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-slate-100 focus:border-emerald-400 focus:outline-none"
              placeholder="+91 98765 43210"
            />
          </div>

          <div>
            <label className="mb-1 block font-semibold text-slate-300">
              OUTBOUND CALL REASON / REMINDER
            </label>
            <select
              value={reminderType}
              onChange={(e) => setReminderType(e.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-slate-100 focus:border-emerald-400 focus:outline-none"
            >
              <option value="Medication & Vaccination Follow-up">
                Medication Adherence & Vaccination Follow-up
              </option>
              <option value="Urgent Post-Triage Health Check">
                Urgent Post-Triage Consultation Follow-up
              </option>
              <option value="Polio & Routine Immunization Nudge">
                Polio & Primary Healthcare Immunization Reminder
              </option>
            </select>
          </div>

          {/* Outcome Retry Rules Matrix */}
          <div className="space-y-1 rounded-xl border border-slate-800 bg-slate-950/80 p-3 text-[10px] text-slate-400">
            <div className="mb-1 font-bold text-slate-300 uppercase">OUTCOME RETRY RULES:</div>
            <div className="flex justify-between">
              <span>No Answer:</span>
              <span className="text-amber-400">Retry in 15m (Max 3)</span>
            </div>
            <div className="flex justify-between">
              <span>Busy:</span>
              <span className="text-amber-400">Retry in 5m (Max 3)</span>
            </div>
            <div className="flex justify-between">
              <span>Voicemail:</span>
              <span className="text-teal-400">Leave message (Complete)</span>
            </div>
            <div className="flex justify-between">
              <span>Opt-out (&quot;stop calling&quot;):</span>
              <span className="text-emerald-400">Saved to Opt-out Registry (Stopped)</span>
            </div>
          </div>
        </div>

        {statusMsg && (
          <div className="mt-4 rounded-xl border border-teal-500/40 bg-teal-500/10 p-2.5 text-center text-xs font-semibold text-teal-300">
            {statusMsg}
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-6 flex gap-3">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={loading}
            className="w-1/3 rounded-xl border-slate-700 py-5 text-slate-300 hover:bg-slate-800"
          >
            CANCEL
          </Button>
          <Button
            onClick={handleDispatch}
            disabled={loading}
            className="w-2/3 rounded-xl bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 py-5 font-bold text-slate-950 shadow-lg hover:shadow-emerald-500/40"
          >
            {loading ? (
              <span className="flex items-center gap-1.5">
                <ArrowClockwise size={16} className="animate-spin" /> DISPATCHING...
              </span>
            ) : (
              <span className="flex items-center gap-1.5">
                <PhoneOutgoing size={18} weight="bold" /> DISPATCH CALL NOW
              </span>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
