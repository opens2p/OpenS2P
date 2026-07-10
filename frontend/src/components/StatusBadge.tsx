// ---------------------------------------------------------------------------
// Reusable status badge with consistent colour mapping across the platform
// ---------------------------------------------------------------------------

const statusPalette: Record<string, string> = {
  // Shared
  DRAFT: 'bg-gray-100 text-gray-600',
  APPROVED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-600',
  CANCELLED: 'bg-red-100 text-red-600',
  CLOSED: 'bg-gray-200 text-gray-500',

  // Supplier
  INVITED: 'bg-blue-100 text-blue-600',
  REGISTERED: 'bg-yellow-100 text-yellow-700',
  BLOCKED: 'bg-red-100 text-red-600',

  // Contract
  REVIEW: 'bg-yellow-100 text-yellow-700',
  ACTIVE: 'bg-green-100 text-green-700',
  EXPIRED: 'bg-red-100 text-red-600',
  RENEWED: 'bg-blue-100 text-blue-600',
  TERMINATED: 'bg-gray-200 text-gray-500',

  // PR
  SUBMITTED: 'bg-blue-100 text-blue-600',
  ORDERED: 'bg-violet-100 text-violet-700',

  // PO
  CREATED: 'bg-gray-100 text-gray-600',
  PO_APPROVED: 'bg-indigo-100 text-indigo-700',
  SENT: 'bg-blue-100 text-blue-600',
  ACKNOWLEDGED: 'bg-cyan-100 text-cyan-700',
  PARTIALLY_RECEIVED: 'bg-amber-100 text-amber-700',
  RECEIVED: 'bg-green-100 text-green-700',

  // Invoice match status
  PENDING: 'bg-yellow-100 text-yellow-700',
  MATCHED: 'bg-green-100 text-green-700',
  EXCEPTION: 'bg-red-100 text-red-600',
  PAYMENT_APPROVED: 'bg-blue-100 text-blue-600',
  PAID: 'bg-emerald-100 text-emerald-700',
};

interface StatusBadgeProps {
  status: string;
  label?: string;
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  // Map "APPROVED" to PO_APPROVED for PO context if needed — but for now
  // both share the same green badge; PO approval uses PO_APPROVED key.
  const key = status === 'APPROVED' ? 'APPROVED' : status;
  const color = statusPalette[key] ?? 'bg-gray-100 text-gray-500';
  return (
    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label ?? status.replace(/_/g, ' ')}
    </span>
  );
}
