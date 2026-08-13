import { useCallback, useEffect, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Filter,
  LifeBuoy,
  PhoneCall,
  RefreshCw,
  ShieldAlert,
  UserCheck,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface EscalationRequest {
  id: string;
  user_id: string;
  caller_name: string;
  phone_number: string;
  reason: string;
  summary: string;
  urgency: 'emergency' | 'high' | 'medium' | 'low';
  caller_language: string;
  preferred_followup: string;
  status: 'open' | 'in_progress' | 'resolved' | 'updated';
  permission_granted: number;
  created_at: string;
  updated_at: string;
}

interface EscalationDashboardProps {
  isOpen: boolean;
  onClose: () => void;
}

export function EscalationDashboard({ isOpen, onClose }: EscalationDashboardProps) {
  const [requests, setRequests] = useState<EscalationRequest[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filterUrgency, setFilterUrgency] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [isCreatingDemo, setIsCreatingDemo] = useState(false);

  const fetchRequests = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/escalations');
      const data = await res.json();
      if (data.success && Array.isArray(data.requests)) {
        setRequests(data.requests);
      }
    } catch (err) {
      console.error('Failed to fetch escalation requests:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchRequests();
      const interval = setInterval(fetchRequests, 5000);
      return () => clearInterval(interval);
    }
  }, [isOpen, fetchRequests]);

  const handleUpdateStatus = async (id: string, newStatus: string) => {
    try {
      const res = await fetch('/api/escalations', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, status: newStatus }),
      });
      const data = await res.json();
      if (data.success) {
        fetchRequests();
      }
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  if (!isOpen) return null;

  const filteredRequests = requests.filter((r) => {
    if (filterUrgency !== 'all' && r.urgency !== filterUrgency) return false;
    if (filterStatus !== 'all' && r.status !== filterStatus) return false;
    return true;
  });

  const totalCount = requests.length;
  const openCount = requests.filter((r) => r.status === 'open').length;
  const emergencyCount = requests.filter((r) => r.urgency === 'emergency').length;
  const resolvedCount = requests.filter((r) => r.status === 'resolved').length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-md">
      <div className="cyber-card relative flex max-h-[90vh] w-full max-w-4xl flex-col rounded-3xl border border-emerald-500/30 bg-slate-900/95 p-6 font-sans shadow-2xl md:p-8">
        {/* Header HUD */}
        <div className="mb-4 flex items-center justify-between border-b border-emerald-500/20 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-red-500/20 text-red-400">
              <LifeBuoy size={24} className="animate-spin-slow" />
            </div>
            <div>
              <div className="font-mono text-[10px] font-bold tracking-widest text-emerald-400 uppercase">
                #VoiceForBharat · DAY 07
              </div>
              <h2 className="font-mono text-xl font-bold tracking-tight text-slate-100 uppercase md:text-2xl">
                Human Assistance Queue // Escalation Dashboard
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-200"
          >
            <X size={20} />
          </button>
        </div>

        {/* Stats Matrix */}
        <div className="mb-6 grid grid-cols-2 gap-3 font-mono sm:grid-cols-4">
          <div className="rounded-xl border border-slate-700/50 bg-slate-950/60 p-3">
            <div className="text-[10px] font-bold text-slate-400 uppercase">Total Requests</div>
            <div className="text-2xl font-bold text-slate-200">{totalCount}</div>
          </div>
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
            <div className="text-[10px] font-bold text-amber-400 uppercase">Open Queue</div>
            <div className="text-2xl font-bold text-amber-300">{openCount}</div>
          </div>
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3">
            <div className="text-[10px] font-bold text-red-400 uppercase">Emergency Level</div>
            <div className="text-2xl font-bold text-red-400">{emergencyCount}</div>
          </div>
          <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3">
            <div className="text-[10px] font-bold text-emerald-400 uppercase">Resolved</div>
            <div className="text-2xl font-bold text-emerald-300">{resolvedCount}</div>
          </div>
        </div>

        {/* Toolbar & Filters */}
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 font-mono text-xs">
          <div className="flex items-center gap-2">
            <Filter size={14} className="text-emerald-400" />
            <span className="text-slate-400">Urgency:</span>
            <select
              value={filterUrgency}
              onChange={(e) => setFilterUrgency(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="all">All Urgencies</option>
              <option value="emergency">Emergency 🚨</option>
              <option value="high">High Urgency ⚠️</option>
              <option value="medium">Medium 🟡</option>
              <option value="low">Low 🔵</option>
            </select>

            <span className="ml-2 text-slate-400">Status:</span>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={fetchRequests}
              disabled={isLoading}
              className="border-emerald-500/40 bg-slate-950 text-xs text-emerald-300 hover:bg-slate-800"
            >
              <RefreshCw size={14} className={`mr-1 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Requests List Table */}
        <div className="flex-1 overflow-y-auto pr-1">
          {filteredRequests.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-800 p-12 text-center font-mono">
              <UserCheck size={36} className="mb-2 text-emerald-400/60" />
              <p className="text-sm font-semibold text-slate-300">No Escalation Requests Found</p>
              <p className="text-xs text-slate-500">
                When callers require human assistance, requests will appear here in real-time.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {filteredRequests.map((req) => (
                <div
                  key={req.id}
                  className={`rounded-2xl border p-4 transition-all duration-200 ${
                    req.urgency === 'emergency'
                      ? 'border-red-500/40 bg-red-950/20 shadow-[0_0_15px_rgba(239,68,68,0.15)]'
                      : req.urgency === 'high'
                        ? 'border-amber-500/30 bg-amber-950/20'
                        : 'border-slate-800 bg-slate-950/70'
                  }`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-2 border-b border-slate-800 pb-2.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-black tracking-wider text-emerald-300">
                        {req.id}
                      </span>

                      {/* Urgency Badge */}
                      {req.urgency === 'emergency' && (
                        <span className="flex items-center gap-1 rounded-md bg-red-500/20 px-2 py-0.5 font-mono text-[10px] font-bold tracking-wider text-red-300">
                          <ShieldAlert size={12} /> EMERGENCY 🚨
                        </span>
                      )}
                      {req.urgency === 'high' && (
                        <span className="flex items-center gap-1 rounded-md bg-amber-500/20 px-2 py-0.5 font-mono text-[10px] font-bold tracking-wider text-amber-300">
                          <AlertCircle size={12} /> HIGH URGENCY ⚠️
                        </span>
                      )}
                      {req.urgency === 'medium' && (
                        <span className="rounded-md bg-yellow-500/20 px-2 py-0.5 font-mono text-[10px] font-bold tracking-wider text-yellow-300">
                          MEDIUM URGENCY 🟡
                        </span>
                      )}
                      {req.urgency === 'low' && (
                        <span className="rounded-md bg-blue-500/20 px-2 py-0.5 font-mono text-[10px] font-bold tracking-wider text-blue-300">
                          LOW URGENCY 🔵
                        </span>
                      )}

                      {/* Status Badge */}
                      {req.status === 'open' && (
                        <span className="animate-pulse rounded-md border border-amber-500/40 bg-amber-500/20 px-2 py-0.5 font-mono text-[10px] font-bold text-amber-300">
                          STATUS: OPEN
                        </span>
                      )}
                      {req.status === 'in_progress' && (
                        <span className="rounded-md border border-blue-500/40 bg-blue-500/20 px-2 py-0.5 font-mono text-[10px] font-bold text-blue-300">
                          STATUS: IN PROGRESS
                        </span>
                      )}
                      {req.status === 'resolved' && (
                        <span className="rounded-md border border-emerald-500/40 bg-emerald-500/20 px-2 py-0.5 font-mono text-[10px] font-bold text-emerald-300">
                          STATUS: RESOLVED
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 font-mono text-[11px] text-slate-400">
                      <Clock size={12} />
                      <span>{new Date(req.created_at).toLocaleTimeString()}</span>
                    </div>
                  </div>

                  {/* Summary & Useful Details */}
                  <div className="my-3 font-mono text-xs">
                    <div className="mb-1 text-slate-200">
                      <span className="font-semibold text-teal-400">Caller:</span> {req.caller_name}{' '}
                      ({req.phone_number}) · <span className="text-purple-300">Language:</span>{' '}
                      {req.caller_language} · <span className="text-cyan-300">Followup:</span>{' '}
                      {req.preferred_followup}
                    </div>
                    <div className="mb-1 text-slate-300">
                      <span className="font-semibold text-amber-400">Escalation Reason:</span>{' '}
                      {req.reason}
                    </div>
                    <div className="rounded-lg border border-slate-800 bg-slate-900/90 p-2.5 text-slate-300">
                      <span className="font-semibold text-emerald-400">Summary:</span> {req.summary}
                    </div>
                  </div>

                  {/* Action Controls */}
                  <div className="flex items-center justify-between pt-1 font-mono text-xs">
                    <span className="text-[10px] text-emerald-400/80">
                      Permission Granted: YES (Explicit Consent)
                    </span>
                    <div className="flex items-center gap-2">
                      {req.status === 'open' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleUpdateStatus(req.id, 'in_progress')}
                          className="h-7 border-blue-500/40 bg-blue-500/10 text-[11px] font-bold text-blue-300 hover:bg-blue-500/20"
                        >
                          <PhoneCall size={12} className="mr-1" /> Mark In Progress
                        </Button>
                      )}
                      {req.status !== 'resolved' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleUpdateStatus(req.id, 'resolved')}
                          className="h-7 border-emerald-500/40 bg-emerald-500/10 text-[11px] font-bold text-emerald-300 hover:bg-emerald-500/20"
                        >
                          <CheckCircle2 size={12} className="mr-1" /> Mark Resolved
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
