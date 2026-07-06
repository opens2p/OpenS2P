import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../api/client';
import { Clock, ShieldCheck, ShieldAlert, FileText, DollarSign, Package } from 'lucide-react';

const eventIcons: Record<string, typeof Clock> = {
  SUPPLIER_CREATED: ShieldCheck,
  SUPPLIER_APPROVED: ShieldCheck,
  SUPPLIER_BLOCKED: ShieldAlert,
  CONTRACT_CREATED: FileText,
  CONTRACT_RENEWED: FileText,
  PR_SUBMITTED: FileText,
  PR_APPROVED: ShieldCheck,
  PO_CREATED: Package,
  PO_SENT: Package,
  PO_CLOSED: Package,
  INVOICE_SUBMITTED: DollarSign,
  INVOICE_MATCHED: DollarSign,
};

const eventColors: Record<string, string> = {
  SUPPLIER_CREATED: 'text-blue-500',
  SUPPLIER_APPROVED: 'text-green-500',
  SUPPLIER_BLOCKED: 'text-red-500',
  CONTRACT_CREATED: 'text-violet-500',
  PR_SUBMITTED: 'text-gray-500',
  PR_APPROVED: 'text-green-500',
  PO_CREATED: 'text-emerald-500',
  PO_SENT: 'text-blue-500',
  INVOICE_SUBMITTED: 'text-amber-500',
  INVOICE_MATCHED: 'text-green-500',
};

export function ActivityTimeline({ entityType, entityId }: { entityType: string; entityId: string }) {
  const { data: events } = useQuery({
    queryKey: ['audit', entityType, entityId],
    queryFn: () =>
      apiGet<Array<{
        id: string; event_type: string; created_at: string | null;
        old_values?: unknown; new_values?: unknown;
      }>>(`/api/v1/audit/${entityType}/${entityId}`),
  });

  if (!events || events.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Activity Timeline</h3>
        <p className="text-sm text-gray-400">No activity recorded yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Clock className="h-4 w-4" /> Activity Timeline
      </h3>
      <div className="space-y-0">
        {events.map((event, i) => {
          const Icon = eventIcons[event.event_type] || Clock;
          const color = eventColors[event.event_type] || 'text-gray-400';
          return (
            <div key={event.id} className="flex gap-3 pb-3 last:pb-0">
              <div className="flex flex-col items-center">
                <div className={`${color} p-1 rounded-full bg-gray-50`}>
                  <Icon className="h-4 w-4" />
                </div>
                {i < events.length - 1 && <div className="w-px flex-1 bg-gray-200 my-1" />}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700">{event.event_type.replace(/_/g, ' ')}</p>
                <p className="text-xs text-gray-400">
                  {event.created_at ? new Date(event.created_at).toLocaleString() : ''}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function GlobalActivityFeed({ limit = 10 }: { limit?: number }) {
  const { data: events } = useQuery({
    queryKey: ['audit-timeline'],
    queryFn: () => apiGet<{ id: string; event_type: string; entity_type: string; created_at: string | null }[]>(
      `/api/v1/audit/timeline?limit=${limit}`,
    ),
  });

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Clock className="h-4 w-4" /> Recent Activity
      </h3>
      {!events || events.length === 0 ? (
        <p className="text-sm text-gray-400">No recent activity.</p>
      ) : (
        <div className="space-y-3">
          {events.map((e) => {
            const Icon = eventIcons[e.event_type] || Clock;
            const color = eventColors[e.event_type] || 'text-gray-400';
            return (
              <div key={e.id} className="flex items-center gap-3 text-sm">
                <Icon className={`h-4 w-4 ${color}`} />
                <span className="text-gray-600 flex-1">{e.event_type.replace(/_/g, ' ')}</span>
                <span className="text-gray-400 text-xs">{e.entity_type}</span>
                <span className="text-gray-400 text-xs">
                  {e.created_at ? new Date(e.created_at).toLocaleString() : ''}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
