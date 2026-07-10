import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiGet, apiPost } from '../../api/client';
import type { PurchaseOrder, Supplier } from '../../api/types';
import { Send, XCircle, Plus, Search, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { useState, useMemo } from 'react';

const statusColors: Record<string, string> = {
  CREATED: 'bg-gray-100 text-gray-600',
  APPROVED: 'bg-indigo-100 text-indigo-700',
  SENT: 'bg-blue-100 text-blue-600',
  ACKNOWLEDGED: 'bg-cyan-100 text-cyan-700',
  PARTIALLY_RECEIVED: 'bg-amber-100 text-amber-700',
  RECEIVED: 'bg-green-100 text-green-700',
  CLOSED: 'bg-gray-200 text-gray-500',
  CANCELLED: 'bg-red-100 text-red-600',
};

export default function POListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');

  const { data: pos, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['pos'],
    queryFn: () => apiGet<PurchaseOrder[]>('/api/v1/purchase-orders'),
  });

  const { data: suppliers } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => apiGet<Supplier[]>('/api/v1/suppliers'),
  });

  const supplierMap = useMemo(() => {
    const map = new Map<string, string>();
    suppliers?.forEach((s) => map.set(s.id, s.supplier_name));
    return map;
  }, [suppliers]);

  const sendMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/purchase-orders/${id}/send`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pos'] }),
  });

  const closeMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/purchase-orders/${id}/close`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['pos'] }),
  });

  const filtered = useMemo(() => {
    if (!pos) return [];
    if (!search) return pos;
    const q = search.toLowerCase();
    return pos.filter((po) => {
      const poMatch = (po.po_number ?? '').toLowerCase().includes(q);
      const supplierMatch = (supplierMap.get(po.supplier_id) ?? '').toLowerCase().includes(q);
      return poMatch || supplierMatch;
    });
  }, [pos, search, supplierMap]);

  const totalValue = (po: PurchaseOrder) =>
    (po.items ?? []).reduce((sum, item) => sum + (item.price ?? 0) * (item.quantity ?? 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Purchase Orders</h1>
          <p className="text-gray-500 mt-1">{filtered.length} of {pos?.length ?? 0} orders</p>
        </div>
        <button
          onClick={() => navigate('/procurement/create-po')}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" /> Create PO
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search POs…"
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
            <p className="text-gray-500 text-sm">Loading purchase orders…</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {isError && !isLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-red-200 p-12">
          <div className="flex flex-col items-center gap-3">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <p className="text-red-600 text-sm font-medium">Unable to load purchase orders</p>
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

      {/* PO Table */}
      {!isLoading && !isError && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-3 font-medium text-gray-600">PO Number</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Supplier</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Status</th>
                <th className="text-right px-6 py-3 font-medium text-gray-600">Total</th>
                <th className="text-right px-6 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((po) => (
                <tr key={po.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{po.po_number ?? '—'}</td>
                  <td className="px-6 py-4 text-gray-600">{supplierMap.get(po.supplier_id) ?? 'Unknown Supplier'}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[po.status] ?? ''}`}>
                      {po.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right text-gray-900 font-medium">
                    ${totalValue(po).toLocaleString()}
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
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <p className="text-gray-400 text-sm">No purchase orders found.</p>
                      <p className="text-gray-300 text-xs">Create a purchase order or adjust your search.</p>
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
