import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import type { PurchaseOrder } from '../../api/types';
import { PackageCheck, PackageX, Calendar, Hash, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { useToast } from '../../components/Toast';

interface Receipt {
  id: string;
  receipt_number?: string | null;
  po_id: string;
  status: string | null;
  received_date?: string | null;
}

export default function ReceivingPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [selectedPO, setSelectedPO] = useState('');
  const [receiveQty, setReceiveQty] = useState<number>(0);
  const [rejectQty, setRejectQty] = useState<number>(0);
  const [status, setStatus] = useState('completed');
  const [receiptDate, setReceiptDate] = useState(new Date().toISOString().split('T')[0]);

  const { data: pos } = useQuery({
    queryKey: ['pos'],
    queryFn: () => apiGet<PurchaseOrder[]>('/api/v1/purchase-orders'),
  });

  const { data: recentReceipts } = useQuery({
    queryKey: ['receipts'],
    queryFn: () => apiGet<Receipt[]>('/api/v1/receiving/receipts'),
  });

  const receiveMutation = useMutation({
    mutationFn: (data: { po_id: string; status: string }) =>
      apiPost('/api/v1/receiving/receipts', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['receipts'] });
      queryClient.invalidateQueries({ queryKey: ['pos'] });
      toast('success', 'Goods receipt recorded successfully');
      setSelectedPO('');
      setReceiveQty(0);
      setRejectQty(0);
      setStatus('completed');
    },
    onError: () => {
      toast('error', 'Failed to record receipt. Please try again.');
    },
  });

  const openPOs = pos?.filter(p => p.status === 'CONFIRMED' || p.status === 'SENT');
  const selectedPOData = pos?.find(p => p.id === selectedPO);
  const poTotalQty = (selectedPOData?.items ?? []).reduce((sum, it) => sum + (it.quantity ?? 0), 0);

  const handleReceive = () => {
    if (!selectedPO) return;
    if (status === 'completed' && poTotalQty > 0 && receiveQty <= 0 && rejectQty <= 0) {
      toast('error', 'Enter receive or reject quantity');
      return;
    }
    receiveMutation.mutate({ po_id: selectedPO, status });
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Receive Goods</h1>
        <p className="text-gray-500 mt-1">Record goods receipt against a purchase order</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Receive form */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
          <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <PackageCheck className="h-5 w-5 text-emerald-500" /> New Receipt
          </h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Order</label>
            <select value={selectedPO} onChange={(e) => setSelectedPO(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white">
              <option value="">Select PO to receive…</option>
              {openPOs?.map((po) => (
                <option key={po.id} value={po.id}>
                  {po.po_number ?? po.id.slice(0, 8)} — {po.status}
                  {po.items ? ` (${po.items.length} items)` : ''}
                </option>
              ))}
            </select>
            {(!openPOs || openPOs.length === 0) && (
              <p className="text-sm text-gray-400 mt-2">No open POs ready for receiving.</p>
            )}
          </div>

          {/* Line items from PO */}
          {selectedPOData && selectedPOData.items && selectedPOData.items.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Line Items</label>
              <div className="hidden sm:grid grid-cols-[1fr_80px_100px] gap-2 px-1 mb-1">
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Item</span>
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wider text-right">Ordered</span>
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wider text-right">Receive</span>
              </div>
              <div className="space-y-2">
                {selectedPOData.items.map((item, idx) => (
                  <div key={item.id ?? idx} className="grid grid-cols-[1fr_80px_100px] gap-2 items-center">
                    <span className="text-sm text-gray-700 truncate">{item.description ?? `Item ${idx + 1}`}</span>
                    <span className="text-sm text-gray-500 text-right">{item.quantity ?? 0}</span>
                    <input
                      type="number" min="0" max={item.quantity ?? 0}
                      defaultValue={item.quantity ?? 0}
                      className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm text-right focus:ring-2 focus:ring-indigo-500 outline-none"
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Receipt date */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Receipt Date</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="date"
                value={receiptDate}
                onChange={(e) => setReceiptDate(e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Receipt Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white">
              <option value="completed">Received in full</option>
              <option value="partial">Partially received</option>
              <option value="pending">Pending inspection</option>
            </select>
          </div>

          <button
            onClick={handleReceive}
            disabled={!selectedPO || receiveMutation.isPending}
            className="w-full flex items-center justify-center gap-2 bg-emerald-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition"
          >
            {receiveMutation.isPending ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Recording…</>
            ) : (
              <><PackageCheck className="h-4 w-4" /> Record Receipt</>
            )}
          </button>
        </div>

        {/* Recent receipts */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Hash className="h-5 w-5 text-gray-400" /> Recent Receipts
          </h2>
          {!recentReceipts || recentReceipts.length === 0 ? (
            <div className="text-center py-8">
              <PackageCheck className="h-8 w-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-400">No receipts recorded yet.</p>
              <p className="text-xs text-gray-300 mt-1">Receive goods against a PO to see them here.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentReceipts.map((r) => (
                <div key={r.id} className="flex items-center justify-between py-2.5 border-b border-gray-100 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-700">
                      {r.receipt_number ?? `Receipt ${r.id.slice(0, 8)}`}
                    </p>
                    <p className="text-xs text-gray-400">
                      PO: {r.po_id.slice(0, 8)}… · {r.received_date ?? '—'}
                    </p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    r.status === 'completed' ? 'bg-green-100 text-green-700' :
                    r.status === 'partial' ? 'bg-amber-100 text-amber-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {r.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
