import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiGet, apiPost } from '../../api/client';
import type { Invoice } from '../../api/types';
import { CheckCircle, AlertTriangle, Search, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { useState, useMemo } from 'react';

const matchColors: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-700',
  MATCHED: 'bg-green-100 text-green-700',
  EXCEPTION: 'bg-red-100 text-red-600',
};

export default function InvoiceListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<string>('');
  const [search, setSearch] = useState('');

  const { data: invoices, isLoading, isError, error, refetch } = useQuery({
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

  const filtered = useMemo(() => {
    if (!invoices) return [];
    return invoices.filter((inv) => {
      if (filter && inv.match_status !== filter) return false;
      if (search) {
        const q = search.toLowerCase();
        return (inv.invoice_number ?? '').toLowerCase().includes(q);
      }
      return true;
    });
  }, [invoices, filter, search]);

  const counts = {
    total: invoices?.length ?? 0,
    pending: invoices?.filter((i) => i.match_status === 'PENDING').length ?? 0,
    matched: invoices?.filter((i) => i.match_status === 'MATCHED').length ?? 0,
    exceptions: invoices?.filter((i) => i.match_status === 'EXCEPTION').length ?? 0,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
          <p className="text-gray-500 mt-1">{filtered.length} of {invoices?.length ?? 0} invoices</p>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        <button onClick={() => setFilter('')}
          className={`bg-white rounded-xl p-4 shadow-sm border text-left transition ${!filter ? 'ring-2 ring-indigo-500' : 'border-gray-200 hover:shadow-md'}`}>
          <p className="text-2xl font-bold text-gray-900">{counts.total}</p>
          <p className="text-sm text-gray-500">All Invoices</p>
        </button>
        <button onClick={() => setFilter('PENDING')}
          className={`bg-white rounded-xl p-4 shadow-sm border text-left transition ${filter === 'PENDING' ? 'ring-2 ring-yellow-500' : 'border-gray-200 hover:shadow-md'}`}>
          <p className="text-2xl font-bold text-yellow-600">{counts.pending}</p>
          <p className="text-sm text-gray-500">Pending Match</p>
        </button>
        <button onClick={() => setFilter('MATCHED')}
          className={`bg-white rounded-xl p-4 shadow-sm border text-left transition ${filter === 'MATCHED' ? 'ring-2 ring-green-500' : 'border-gray-200 hover:shadow-md'}`}>
          <p className="text-2xl font-bold text-green-600">{counts.matched}</p>
          <p className="text-sm text-gray-500">Matched</p>
        </button>
        <button onClick={() => setFilter('EXCEPTION')}
          className={`bg-white rounded-xl p-4 shadow-sm border text-left transition ${filter === 'EXCEPTION' ? 'ring-2 ring-red-500' : 'border-gray-200 hover:shadow-md'}`}>
          <p className="text-2xl font-bold text-red-600">{counts.exceptions}</p>
          <p className="text-sm text-gray-500">Exceptions</p>
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search invoices…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
        />
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
            <p className="text-gray-500 text-sm">Loading invoices…</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {isError && !isLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-red-200 p-12">
          <div className="flex flex-col items-center gap-3">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <p className="text-red-600 text-sm font-medium">Unable to load invoices</p>
            <p className="text-gray-400 text-xs">{error instanceof Error ? error.message : 'API unavailable'}</p>
            <button
              onClick={() => refetch()}
              className="flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-800 font-medium mt-1"
            >
              <RefreshCw className="h-4 w-4" /> Try again
            </button>
          </div>
        </div>
      )}

      {/* Invoice Table */}
      {!isLoading && !isError && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Invoice</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">PO</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Amount</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Match Status</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Due Date</th>
                <th className="text-right px-6 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((inv) => (
                <tr key={inv.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/invoices/${inv.id}`)}>
                  <td className="px-6 py-4 font-medium text-gray-900">{inv.invoice_number ?? '—'}</td>
                  <td className="px-6 py-4 text-gray-500 text-xs">{inv.po_id.slice(0, 8)}…</td>
                  <td className="px-6 py-4 text-gray-900 font-medium">${Number(inv.amount).toFixed(2)}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${matchColors[inv.match_status] ?? ''}`}>
                      {inv.match_status === 'EXCEPTION' && <AlertTriangle className="h-3 w-3" />}
                      {inv.match_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-500 text-sm">{inv.due_date ?? '—'}</td>
                  <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
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
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <p className="text-gray-400 text-sm">No invoices found.</p>
                      <p className="text-gray-300 text-xs">Invoices will appear here once created from purchase orders.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
