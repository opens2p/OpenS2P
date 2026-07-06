import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import type { PurchaseOrder } from '../../api/types';
import { PackageCheck } from 'lucide-react';

export default function ReceivingPage() {
  const queryClient = useQueryClient();
  const [selectedPO, setSelectedPO] = useState('');
  const [status, setStatus] = useState('completed');

  const { data: pos } = useQuery({
    queryKey: ['pos'],
    queryFn: () => apiGet<PurchaseOrder[]>('/api/v1/purchase-orders'),
  });

  const receiveMutation = useMutation({
    mutationFn: (data: { po_id: string; status: string }) =>
      apiPost('/api/v1/receiving/receipts', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['receipts'] });
      alert('Receipt recorded successfully');
    },
  });

  const openPOs = pos?.filter(p => p.status === 'CONFIRMED' || p.status === 'SENT');

  return (
    <div className="max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Receive Goods</h1>
        <p className="text-gray-500 mt-1">Record receipt against a purchase order</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Order</label>
          <select value={selectedPO} onChange={(e) => setSelectedPO(e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white">
            <option value="">Select PO to receive…</option>
            {openPOs?.map((po) => (
              <option key={po.id} value={po.id}>{po.po_number ?? po.id.slice(0, 8)} — {po.status}</option>
            ))}
          </select>
          {(!openPOs || openPOs.length === 0) && (
            <p className="text-sm text-gray-400 mt-2">No open POs ready for receiving.</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select value={status} onChange={(e) => setStatus(e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white">
            <option value="completed">Received in full</option>
            <option value="partial">Partially received</option>
          </select>
        </div>

        <button
          onClick={() => receiveMutation.mutate({ po_id: selectedPO, status })}
          disabled={!selectedPO || receiveMutation.isPending}
          className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
        >
          <PackageCheck className="h-4 w-4" />
          {receiveMutation.isPending ? 'Recording…' : 'Record Receipt'}
        </button>
      </div>

      {/* Recent receipts */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Recent Receipts</h2>
        <ReceiptList />
      </div>
    </div>
  );
}

function ReceiptList() {
  const { data: receipts } = useQuery({
    queryKey: ['receipts'],
    queryFn: () => apiGet<{id: string; po_id: string; status: string}[]>('/api/v1/receiving/receipts'),
  });

  if (!receipts || receipts.length === 0) {
    return <p className="text-sm text-gray-400">No receipts recorded yet.</p>;
  }

  return (
    <div className="space-y-2">
      {receipts.map((r) => (
        <div key={r.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
          <span className="text-sm text-gray-600">PO: {r.po_id.slice(0, 8)}…</span>
          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{r.status}</span>
        </div>
      ))}
    </div>
  );
}
