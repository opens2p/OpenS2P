import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiGet, apiPost } from '../../api/client';
import type { Invoice } from '../../api/types';
import { CheckCircle, AlertTriangle } from 'lucide-react';

const matchColors: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-700',
  MATCHED: 'bg-green-100 text-green-700',
  EXCEPTION: 'bg-red-100 text-red-600',
};

export default function InvoiceListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: invoices } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => apiGet<Invoice[]>('/api/v1/invoices'),
  });

  const matchMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/invoices/${id}/match`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['invoices'] }),
  });

  const approvePaymentMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/invoices/${id}/approve`, { approved: true }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['invoices'] }),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
        <p className="text-gray-500 mt-1">{invoices?.length ?? 0} invoices</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <p className="text-2xl font-bold text-gray-900">{invoices?.filter((i) => i.match_status === 'PENDING').length ?? 0}</p>
          <p className="text-sm text-gray-500">Pending Match</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <p className="text-2xl font-bold text-green-600">{invoices?.filter((i) => i.match_status === 'MATCHED').length ?? 0}</p>
          <p className="text-sm text-gray-500">Matched</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <p className="text-2xl font-bold text-red-600">{invoices?.filter((i) => i.match_status === 'EXCEPTION').length ?? 0}</p>
          <p className="text-sm text-gray-500">Exceptions</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-6 py-3 font-medium text-gray-600">Invoice</th>
              <th className="text-left px-6 py-3 font-medium text-gray-600">Amount</th>
              <th className="text-left px-6 py-3 font-medium text-gray-600">Match Status</th>
              <th className="text-right px-6 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {invoices?.map((inv) => (
              <tr key={inv.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/invoices/${inv.id}`)}>
                <td className="px-6 py-4 font-medium text-gray-900">{inv.invoice_number ?? '—'}</td>
                <td className="px-6 py-4 text-gray-900">${Number(inv.amount).toFixed(2)}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${matchColors[inv.match_status] ?? ''}`}>
                    {inv.match_status === 'EXCEPTION' && <AlertTriangle className="h-3 w-3" />}
                    {inv.match_status}
                  </span>
                </td>
                <td className="px-6 py-4 text-right space-x-2" onClick={(e) => e.stopPropagation()}>
                  {inv.match_status === 'PENDING' && (
                    <button
                      onClick={() => matchMutation.mutate(inv.id)}
                      className="inline-flex items-center gap-1 text-green-600 hover:text-green-800 text-xs font-medium"
                    >
                      <CheckCircle className="h-4 w-4" /> Match
                    </button>
                  )}
                  {inv.match_status === 'MATCHED' && (
                    <button
                      onClick={() => approvePaymentMutation.mutate(inv.id)}
                      className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 text-xs font-medium"
                    >
                      <CheckCircle className="h-4 w-4" /> Approve Payment
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
