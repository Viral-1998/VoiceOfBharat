'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  ArrowClockwise,
  CheckCircle,
  Clock,
  Funnel,
  Lightning,
  LockKey,
  PhoneCall,
  PhoneDisconnect,
  PhoneIncoming,
  PhoneOutgoing,
  ShieldCheck,
  TrendUp,
  UserCheck,
  Warning,
  X,
} from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';

interface CallLog {
  call_id: string;
  channel: string;
  phone_number: string;
  start_time: string;
  duration_seconds: number;
  status: string;
  failure_category: string;
  outcome_summary: string;
  triage_level: string;
  escalation_created: number;
  first_response_latency_ms: number;
  created_at: string;
}

interface AnalyticsSummary {
  definition_of_success: string;
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate_percent: number;
  avg_latency_ms: number;
  total_escalations: number;
  failure_breakdown: Record<string, number>;
  recent_calls: CallLog[];
}

interface AnalyticsDashboardProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AnalyticsDashboard({ isOpen, onClose }: AnalyticsDashboardProps) {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const [channelFilter, setChannelFilter] = useState<'all' | 'browser' | 'sip_outbound'>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  const fetchAnalytics = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/analytics?channel=${channelFilter}`, { cache: 'no-store' });
      const data = await res.json();
      if (data.success && data.summary) {
        setAnalytics(data.summary);
        setLastUpdated(new Date().toLocaleTimeString());
      }
    } catch (error) {
      console.error('Failed to fetch call analytics:', error);
    } finally {
      setIsLoading(false);
    }
  }, [channelFilter]);

  useEffect(() => {
    if (isOpen) {
      fetchAnalytics();
    }
  }, [isOpen, fetchAnalytics]);

  useEffect(() => {
    if (!isOpen || !autoRefresh) return;
    const interval = setInterval(() => {
      fetchAnalytics();
    }, 3000);
    return () => clearInterval(interval);
  }, [isOpen, autoRefresh, fetchAnalytics]);

  const handleSimulateCall = async (
    status: 'successful' | 'failed',
    failureCategory?: string,
    outcomeSummary?: string
  ) => {
    setIsSimulating(true);
    try {
      const payload = {
        status,
        failure_category: failureCategory || (status === 'failed' ? 'user_hangup' : 'none'),
        outcome_summary:
          outcomeSummary ||
          (status === 'successful'
            ? 'Simulated symptom triage completed: GREEN (Home Care)'
            : 'Simulated caller disconnected immediately (< 5s)'),
        channel: channelFilter === 'all' ? 'browser' : channelFilter,
        duration_seconds: status === 'successful' ? 45 : 4,
        latency_ms: status === 'successful' ? 415.5 : 0.0,
      };

      await fetch('/api/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      await fetchAnalytics();
    } catch (error) {
      console.error('Failed to run simulation test:', error);
    } finally {
      setIsSimulating(false);
    }
  };

  if (!isOpen) return null;

  const totalCalls = analytics?.total_calls || 0;
  const successfulCalls = analytics?.successful_calls || 0;
  const failedCalls = analytics?.failed_calls || 0;
  const successRate = analytics?.success_rate_percent || 0.0;
  const avgLatency = analytics?.avg_latency_ms || 0.0;
  const escalations = analytics?.total_escalations || 0;
  const recentCalls = analytics?.recent_calls || [];
  const failureBreakdown = analytics?.failure_breakdown || {};

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-3 font-sans backdrop-blur-md">
      <div className="cyber-card relative flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-emerald-500/30 bg-slate-950/95 text-slate-100 shadow-2xl">
        {/* HUD Top Bar Header */}
        <div className="flex items-center justify-between border-b border-emerald-500/20 bg-slate-900/60 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-400">
              <TrendUp size={22} weight="bold" />
            </div>
            <div>
              <div className="flex items-center gap-2 font-mono text-xs text-emerald-400">
                <span className="size-2 animate-ping rounded-full bg-emerald-400" />
                <span>#VoiceForBharat · DAY 08</span>
                <span className="text-slate-500">|</span>
                <span className="text-slate-400">Refreshed: {lastUpdated || 'Now'}</span>
              </div>
              <h2 className="text-xl font-bold tracking-tight text-white">
                Call Analytics & Performance Dashboard
              </h2>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fetchAnalytics()}
              disabled={isLoading}
              className="gap-1.5 border-emerald-500/30 bg-slate-900 font-mono text-xs text-emerald-300 hover:bg-emerald-500/20"
            >
              <ArrowClockwise size={14} className={isLoading ? 'animate-spin' : ''} />
              <span>Sync Data</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="rounded-full text-slate-400 hover:bg-slate-800 hover:text-white"
            >
              <X size={20} />
            </Button>
          </div>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto p-6">
          {/* Definition of Success Banner */}
          <div className="rounded-2xl border border-emerald-500/30 bg-gradient-to-r from-emerald-950/40 via-slate-900/80 to-teal-950/40 p-4">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 rounded-lg bg-emerald-500/20 p-2 text-emerald-300">
                <ShieldCheck size={20} weight="fill" />
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 font-mono text-xs font-bold text-emerald-300 uppercase">
                  <span>Definition of Call Success</span>
                  <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] text-emerald-400">
                    Health Access Track
                  </span>
                </div>
                <p className="font-mono text-xs leading-relaxed text-slate-300">
                  {analytics?.definition_of_success ||
                    'A call is marked SUCCESSFUL when the caller receives safe health guidance, completes a symptom triage assessment, looks up health facilities, creates a human escalation request, or manages caller memory/opt-out preferences.'}
                </p>
              </div>
            </div>
          </div>

          {/* Test Path Control & Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-900/50 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="mr-2 flex items-center gap-1.5 font-mono text-xs font-semibold text-slate-400 uppercase">
                <Funnel size={14} className="text-emerald-400" /> Filter Channel:
              </span>
              {(['all', 'browser', 'sip_outbound'] as const).map((ch) => (
                <button
                  key={ch}
                  onClick={() => setChannelFilter(ch)}
                  className={`rounded-lg px-3 py-1.5 font-mono text-xs font-semibold transition-all ${
                    channelFilter === ch
                      ? 'border border-emerald-500/40 bg-emerald-500/20 text-emerald-300 shadow-sm'
                      : 'border border-slate-800 bg-slate-950 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {ch === 'all'
                    ? 'All Calls'
                    : ch === 'browser'
                      ? '🌐 Browser Voice'
                      : '📞 Outbound SIP'}
                </button>
              ))}
            </div>

            {/* Test Path Buttons (Step 5 Requirement) */}
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                onClick={() => handleSimulateCall('successful')}
                disabled={isSimulating}
                className="gap-1.5 bg-emerald-600 font-mono text-xs font-bold text-slate-950 shadow-md shadow-emerald-900/40 hover:bg-emerald-500"
              >
                <CheckCircle size={15} weight="bold" />
                <span>Test Success Path</span>
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleSimulateCall('failed', 'user_hangup')}
                disabled={isSimulating}
                className="gap-1.5 border-rose-500/40 bg-rose-950/30 font-mono text-xs font-bold text-rose-300 hover:bg-rose-900/50"
              >
                <PhoneDisconnect size={15} weight="bold" />
                <span>Test Failure Path</span>
              </Button>
              <label className="ml-1 flex cursor-pointer items-center gap-2 border-l border-slate-800 pl-3 font-mono text-xs text-slate-400">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-emerald-500 focus:ring-emerald-500/40"
                />
                <span>Auto Refresh (3s)</span>
              </label>
            </div>
          </div>

          {/* 3 Core Required Numbers & Metrics Grid */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
            {/* KPI 1: Total Calls */}
            <div className="rounded-2xl border border-cyan-500/30 bg-cyan-950/20 p-4 shadow-lg">
              <div className="flex items-center justify-between font-mono text-[10px] font-bold text-cyan-400 uppercase">
                <span>Total Calls</span>
                <PhoneCall size={16} />
              </div>
              <div className="mt-2 font-mono text-3xl font-black tracking-tight text-cyan-200">
                {totalCalls}
              </div>
              <div className="mt-1 font-mono text-[11px] text-cyan-400/80">Logged in DB</div>
            </div>

            {/* KPI 2: Successful Calls */}
            <div className="rounded-2xl border border-emerald-500/40 bg-emerald-950/25 p-4 shadow-lg shadow-emerald-950/50">
              <div className="flex items-center justify-between font-mono text-[10px] font-bold text-emerald-400 uppercase">
                <span>Successful Calls</span>
                <CheckCircle size={16} weight="fill" />
              </div>
              <div className="mt-2 font-mono text-3xl font-black tracking-tight text-emerald-300">
                {successfulCalls}
              </div>
              <div className="mt-1 font-mono text-[11px] font-semibold text-emerald-400/90">
                Objectives Achieved
              </div>
            </div>

            {/* KPI 3: Failed Calls */}
            <div className="rounded-2xl border border-rose-500/40 bg-rose-950/25 p-4 shadow-lg shadow-rose-950/50">
              <div className="flex items-center justify-between font-mono text-[10px] font-bold text-rose-400 uppercase">
                <span>Failed Calls</span>
                <PhoneDisconnect size={16} weight="fill" />
              </div>
              <div className="mt-2 font-mono text-3xl font-black tracking-tight text-rose-300">
                {failedCalls}
              </div>
              <div className="mt-1 font-mono text-[11px] font-semibold text-rose-400/90">
                Hangup / Unresolved
              </div>
            </div>

            {/* KPI 4: Success Rate % */}
            <div className="rounded-2xl border border-teal-500/30 bg-slate-900/60 p-4">
              <div className="flex items-center justify-between font-mono text-[10px] font-bold text-teal-400 uppercase">
                <span>Success Rate</span>
                <TrendUp size={16} />
              </div>
              <div className="mt-2 font-mono text-3xl font-black tracking-tight text-teal-200">
                {successRate}%
              </div>
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-400"
                  style={{ width: `${Math.min(successRate, 100)}%` }}
                />
              </div>
            </div>

            {/* KPI 5: Speech Latency (ms) */}
            <div className="rounded-2xl border border-amber-500/30 bg-slate-900/60 p-4">
              <div className="flex items-center justify-between font-mono text-[10px] font-bold text-amber-400 uppercase">
                <span>Avg Speech Latency</span>
                <Lightning size={16} weight="fill" />
              </div>
              <div className="mt-2 font-mono text-3xl font-black tracking-tight text-amber-300">
                {avgLatency > 0 ? `${avgLatency} ms` : 'N/A'}
              </div>
              <div className="mt-1 font-mono text-[11px] text-amber-400/80">Murf Falcon TTS</div>
            </div>

            {/* KPI 6: Escalations Created */}
            <div className="rounded-2xl border border-purple-500/30 bg-slate-900/60 p-4">
              <div className="flex items-center justify-between font-mono text-[10px] font-bold text-purple-400 uppercase">
                <span>Human Escalations</span>
                <UserCheck size={16} />
              </div>
              <div className="mt-2 font-mono text-3xl font-black tracking-tight text-purple-300">
                {escalations}
              </div>
              <div className="mt-1 font-mono text-[11px] text-purple-400/80">Step 4 Consent</div>
            </div>
          </div>

          {/* Failure Categories Visual Breakdown */}
          {failedCalls > 0 && (
            <div className="space-y-3 rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="flex items-center gap-1.5 font-mono text-xs font-bold text-rose-300 uppercase">
                  <Warning size={15} className="text-rose-400" /> Failure Categories Breakdown
                </span>
                <span className="font-mono text-[11px] text-slate-400">
                  {failedCalls} total failures logged
                </span>
              </div>
              <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
                {Object.entries(failureBreakdown).map(([cat, count]) => {
                  const pct = Math.round((count / failedCalls) * 100);
                  const labelMap: Record<string, string> = {
                    user_hangup: 'Caller Hangup (<5s)',
                    incomplete_task: 'Incomplete Task',
                    tool_failure: 'Tool / Data Error',
                    api_error: 'Service Offline',
                  };
                  return (
                    <div
                      key={cat}
                      className="rounded-xl border border-rose-500/20 bg-rose-950/15 p-3 font-mono"
                    >
                      <div className="mb-1 flex justify-between text-xs font-semibold text-rose-300">
                        <span>{labelMap[cat] || cat}</span>
                        <span>
                          {count} ({pct}%)
                        </span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-rose-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Call History Table (Step 6 Privacy Protected) */}
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <Clock size={16} className="text-emerald-400" />
                <h3 className="font-mono text-xs font-bold tracking-wider text-slate-200 uppercase">
                  Recent Call History Log (Real Live Data)
                </h3>
              </div>
              <div className="flex items-center gap-1.5 rounded-md border border-emerald-500/30 bg-emerald-950/30 px-2.5 py-1 font-mono text-[10px] text-emerald-300">
                <LockKey size={13} weight="fill" />
                <span>Step 6 Protected: Zero OTPs, PINs, bank accounts, or raw transcripts</span>
              </div>
            </div>

            {recentCalls.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-8 text-center font-mono text-xs text-slate-400">
                No calls recorded yet. Click{' '}
                <span className="font-semibold text-emerald-400">
                  &quot;Test Success Path&quot;
                </span>{' '}
                above or place a browser/outbound call to log metrics.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/50">
                <table className="w-full text-left font-mono text-xs">
                  <thead className="border-b border-slate-800 bg-slate-950/80 text-[10px] text-slate-400 uppercase">
                    <tr>
                      <th className="px-4 py-3">Call ID</th>
                      <th className="px-4 py-3">Channel</th>
                      <th className="px-4 py-3">Duration</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Outcome Summary (Sanitized)</th>
                      <th className="px-4 py-3 text-right">Latency</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {recentCalls.map((call) => {
                      const isSuccess = call.status === 'successful';
                      return (
                        <tr key={call.call_id} className="transition-colors hover:bg-slate-800/40">
                          <td className="px-4 py-3 font-semibold text-slate-200">{call.call_id}</td>
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-semibold ${
                                call.channel === 'sip_outbound'
                                  ? 'border border-purple-500/30 bg-purple-500/10 text-purple-300'
                                  : 'border border-cyan-500/30 bg-cyan-500/10 text-cyan-300'
                              }`}
                            >
                              {call.channel === 'sip_outbound' ? (
                                <PhoneOutgoing size={12} />
                              ) : (
                                <PhoneIncoming size={12} />
                              )}
                              {call.channel}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-400">{call.duration_seconds}s</td>
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${
                                isSuccess
                                  ? 'border border-emerald-500/40 bg-emerald-500/20 text-emerald-300'
                                  : 'border border-rose-500/40 bg-rose-500/20 text-rose-300'
                              }`}
                            >
                              {isSuccess ? (
                                <CheckCircle size={12} weight="bold" />
                              ) : (
                                <PhoneDisconnect size={12} weight="bold" />
                              )}
                              {call.status}
                            </span>
                          </td>
                          <td className="max-w-md truncate px-4 py-3 text-slate-200">
                            {call.outcome_summary || 'Consultation processed'}
                          </td>
                          <td className="px-4 py-3 text-right text-amber-300">
                            {call.first_response_latency_ms > 0
                              ? `${call.first_response_latency_ms} ms`
                              : '-'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
