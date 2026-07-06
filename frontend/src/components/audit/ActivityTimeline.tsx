import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../../api/client';
import {
  Clock, ShieldCheck, ShieldAlert, FileText, DollarSign,
  Package, UserPlus, Activity, AlertTriangle, CheckCircle,
} from 'lucide-react';

interface AuditEvent {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  actor: string | null;
  changes: Array<{ field: string; old: string | null; new: string | null }>;
  created_at: string | null;
}

const eventConfig: Record<string, { icon: typeof Clock; color: string; label: string }> = {
  SUPPLIER_CREATED:    { icon: UserPlus,    color: 'text-blue-500',  label: 'Supplier Created' },
  SUPPLIER_APPROVED:   { icon: ShieldCheck, color: 'text-green-500', label: 'Supplier Approved' },
  SUPPLIER_BLOCKED:    { icon: ShieldAlert, color: 'text-red-500',   label: 'Supplier Blocked' },
  CONTRACT_CREATED:    { icon: FileText,    color: 'text-violet-500',label: 'Contract Created' },
  CONTRACT_RENEWED:    { icon: FileText,    color: 'text-indigo-500',label: 'Contract Renewed' },
  CONTRACT_ACTIVATED:  { icon: CheckCircle, color: 'text-green-500', label: 'Contract Activated' },
  PR_SUBMITTED:        { icon: FileText,    color: 'text-blue-500',  label: 'PR Submitted' },
  PR_APPROVED:         { icon: ShieldCheck, color: 'text-green-500', label: 'PR Approved' },
  PR_REJECTED:         { icon: AlertTriangle,color: 'text-red-500',  label: 'PR Rejected' },
  PO_CREATED:          { icon: Package,     color: 'text-emerald-500',label: 'PO Created' },
  PO_SENT:             { icon: Package,     color: 'text-blue-500',  label: 'PO Sent' },
  PO_CLOSED:           { icon: Package,     color: 'text-gray-500',  label: 'PO Closed' },
  INVOICE_SUBMITTED:   { icon: DollarSign,  color: 'text-amber-500', label: 'Invoice Submitted' },
  INVOICE_MATCHED:     { icon: DollarSign,  color: 'text-green-500', label: 'Invoice Matched' },
  BID_SUBMITTED:       { icon: Activity,    color: 'text-purple-500',label: 'Bid Submitted' },
  WORKFLOW_STARTED:    { icon: Activity,    color: 'text-indigo-500',label: 'Workflow Started' },
};

function getConfig(eventType: string) {
  return eventConfig[eventType] || { icon: Clock, color: 'text-gray-400', label: eventType.replace(/_/g, ' ') };
}

export function ActivityTimeline({ entityType, entityId, title = 'Activity Timeline' }: {
  entityType: string; entityId: string; title?: string;
}) {
  const { data: events, isLoading } = useQuery({
    queryKey: ['audit', entityType, entityId],
    queryFn: () => apiGet<AuditEvent[]>(`/api/v1/audit/${entityType}/${entityId}`),
  });

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">{title}</h3>
        <p className="text-sm text-gray-400">Loading…</p>
      </div>
    );
  }

  if (!events || events.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">{title}</h3>
        <p className="text-sm text-gray-400">No activity recorded yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Clock className="h-4 w-4" /> {title}
      </h3>
      <div className="space-y-0">
        {events.map((event, i) => {
          const cfg = getConfig(event.event_type);
          const Icon = cfg.icon;
          return (
            <div key={event.id} className="flex gap-3 pb-4 last:pb-0">
              <div className="flex flex-col items-center">
                <div className={`${cfg.color} p-1.5 rounded-full bg-gray-50 ring-1 ring-gray-200`}>
                  <Icon className="h-4 w-4" />
                </div>
                {i < events.length - 1 && <div className="w-px flex-1 bg-gray-200 my-1" />}
              </div>
              <div className="flex-1 min-w-0 pt-0.5">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900">{cfg.label}</p>
                  <span className="text-xs text-gray-400">
                    {event.created_at ? new Date(event.created_at).toLocaleString() : ''}
                  </span>
                </div>
                {event.actor && (
                  <p className="text-xs text-gray-500 mt-0.5">by {event.actor}</p>
                )}
                {event.changes.length > 0 && (
                  <div className="mt-1.5 space-y-0.5">
                    {event.changes.map((c, ci) => (
                      <div key={ci} className="flex items-center gap-2 text-xs text-gray-500">
                        <span className="font-medium text-gray-600">{c.field}:</span>
                        <span className="line-through text-red-400">{String(c.old ?? '—')}</span>
                        <ArrowRight className="h-3 w-3 text-gray-300" />
                        <span className="text-green-600">{String(c.new ?? '—')}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ArrowRight({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M5 12h14M13 5l7 7-7 7" />
    </svg>
  );
}
