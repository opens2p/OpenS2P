import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import type { PurchaseOrder } from '../../api/types';
import { Send, XCircle } from 'lucide-react';

const statusColors: Record<string, string> = {
  CREATED: 'bg-gray-100 text-gray-600',
  SENT: 'bg-blue-100 text-blue-600',
  CONFIRMED: 'bg-green-100 text-green-700',
  CLOSED: 'bg-gray-200 text-gray-500',
  CANCELLED: 'bg-red-100 text-red-600',
};

export default function POListPage() {
  const queryClient = useQueryClient();

  const { data: pos } = useQuery({
    queryKey: ['pos'],
    queryFn: () => apiGet<PurchaseOrder[]>('/api/v1/purchase-orders'),
  });

  const sendMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/purchase-orders/${id}/send`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pos'] }),
  });

  const closeMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/purchase-orders/${id}/close`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pos'] }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Purchase Orders</h1>
        <p className="text-gray-500 mt-1">{pos?.length ?? 0} orders</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-6 py-3 font-medium text-gray-600">PO Number</th>
              <th className="text-left px-6 py-3 font-medium text-gray-600">Status</th>
              <th className="text-right px-6 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {pos?.map((po) => (
              <tr key={po.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-gray-900">{po.po_number ?? '—'}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[po.status] ?? ''}`}>
                    {po.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  {po.status === 'CREATED' && (
                    <button
                      onClick={() => sendMutation.mutate(po.id)}
                      className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-xs font-medium"
                    >
                      <Send className="h-4 w-4" /> Send
                    </button>
                  )}
                  {po.status === 'CONFIRMED' && (
                    <button
                      onClick={() => closeMutation.mutate(po.id)}
                      className="inline-flex items-center gap-1 text-gray-600 hover:text-gray-800 text-xs font-medium"
                    >
                      <XCircle className="h-4 w-4" /> Close
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
