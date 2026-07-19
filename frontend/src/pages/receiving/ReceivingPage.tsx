import { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import type { PurchaseOrder } from '../../api/types';
import { PackageCheck, Calendar, Hash, Loader2, AlertCircle } from 'lucide-react';
import { useToast } from '../../components/Toast';

interface Receipt {
  id: string;
  receipt_number?: string | null;
  po_id: string;
  status: string | null;
  received_date?: string | null;
  quantity_received?: number | null;
  amount_received?: number | null;
}

const receivableStatuses = new Set([
  'SENT', 'ACKNOWLEDGED', 'APPROVED', 'PARTIALLY_RECEIVED',
]);

function poQty(po?: PurchaseOrder | null): number {
  return (po?.items ?? []).reduce((sum, it) => sum + Number(it.quantity ?? 0), 0);
}

function poAmount(po?: PurchaseOrder | null): number {
  return (po?.items ?? []).reduce(
    (sum, it) => sum + Number(it.quantity ?? 0) * Number(it.price ?? 0),
    0,
  );
}

export default function ReceivingPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [selectedPO, setSelectedPO] = useState('');
  const [acceptQty, setAcceptQty] = useState('');
  const [rejectQty, setRejectQty] = useState('0');
  const [status, setStatus] = useState('completed');
  const [receiptDate, setReceiptDate] = useState(new Date().toISOString().split('T')[0]);

  const { data: pos, isLoading: posLoading } = useQuery({
    queryKey: ['pos', { limit: 200 }],
    queryFn: () => apiGet<PurchaseOrder[]>('/api/v1/purchase-orders?limit=200'),
  });

  const { data: selectedPoDetail, isLoading: detailLoading } = useQuery({
    queryKey: ['po', selectedPO],
    queryFn: () => apiGet<PurchaseOrder>(`/api/v1/purchase-orders/${selectedPO}`),
    enabled: !!selectedPO,
  });

  const { data: recentReceipts, isError: receiptsError } = useQuery({
    queryKey: ['receipts'],
    queryFn: () => apiGet<Receipt[]>('/api/v1/receiving/receipts'),
  });

  const openPOs = useMemo(
    () => (pos ?? []).filter((p) => receivableStatuses.has(String(p.status))),
    [pos],
  );

  const activePo = selectedPoDetail ?? pos?.find((p) => p.id === selectedPO);
  const orderedQty = poQty(activePo);
  const orderedAmount = poAmount(activePo);

  useEffect(() => {
    if (!activePo) return;
    const qty = poQty(activePo);
    if (qty > 0) {
      setAcceptQty(String(qty));
      setRejectQty('0');
      setStatus('completed');
    }
  }, [activePo?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const receiveMutation = useMutation({
    mutationFn: (data: {
      po_id: string;
      status: string;
      quantity_received?: number;
      amount_received?: number;
      received_date?: string;
    }) => apiPost('/api/v1/receiving/receipts', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['receipts'] });
      queryClient.invalidateQueries({ queryKey: ['pos'] });
      queryClient.invalidateQueries({ queryKey: ['po'] });
      toast('success', 'Goods receipt recorded');
      setSelectedPO('');
      setAcceptQty('');
      setRejectQty('0');
      setStatus('completed');
    },
    onError: (err: Error) => {
      toast('error', err.message || 'Failed to record receipt');
    },
  });

  const handleReceive = () => {
    if (!selectedPO) {
      toast('error', 'Select a purchase order');
      return;
    }
    const accepted = Number(acceptQty);
    const rejected = Number(rejectQty || 0);
    if (!Number.isFinite(accepted) || accepted < 0) {
      toast('error', 'Enter a valid accept quantity');
      return;
    }
    if (!Number.isFinite(rejected) || rejected < 0) {
      toast('error', 'Enter a valid reject quantity');
      return;
    }
    if (accepted <= 0 && rejected <= 0) {
      toast('error', 'Enter accept or reject quantity');
      return;
    }
    if (orderedQty > 0 && accepted + rejected > orderedQty) {
      toast('error', `Accept + reject cannot exceed ordered qty (${orderedQty})`);
      return;
    }

    const unitPrice = orderedQty > 0 ? orderedAmount / orderedQty : 0;
    const amountReceived = Number((accepted * unitPrice).toFixed(2));
    const nextStatus =
      status === 'pending'
        ? 'pending'
        : orderedQty > 0 && accepted < orderedQty
          ? 'partial'
          : status;

    receiveMutation.mutate({
      po_id: selectedPO,
      status: nextStatus,
      quantity_received: accepted,
      amount_received: amountReceived,
      received_date: receiptDate,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Receiving</h1>
        <p className="text-gray-500 mt-1">
          Record goods receipt against a PO — enter accept quantity for 3-way match
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
          <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <PackageCheck className="h-5 w-5 text-emerald-500" /> New Receipt
          </h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Purchase Order</label>
            <select
              value={selectedPO}
              onChange={(e) => setSelectedPO(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
            >
              <option value="">Select PO to receive…</option>
              {openPOs.map((po) => (
                <option key={po.id} value={po.id}>
                  {po.po_number ?? po.id.slice(0, 8)} — {po.status}
                  {po.items?.length ? ` · ${po.items.length} lines · $${poAmount(po).toFixed(2)}` : ''}
                </option>
              ))}
            </select>
            {posLoading && <p className="text-sm text-gray-400 mt-2">Loading POs…</p>}
            {!posLoading && openPOs.length === 0 && (
              <p className="text-sm text-gray-400 mt-2">No open POs ready for receiving. Send a PO first.</p>
            )}
          </div>

          {selectedPO && (
            <div className="rounded-lg border border-gray-100 bg-gray-50 p-4 space-y-3">
              {detailLoading && !activePo?.items?.length ? (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Loader2 className="h-4 w-4 animate-spin" /> Loading PO lines…
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-gray-500">Ordered qty</p>
                      <p className="font-semibold text-gray-900">{orderedQty}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">PO value</p>
                      <p className="font-semibold text-gray-900">${orderedAmount.toFixed(2)}</p>
                    </div>
                  </div>

                  {(activePo?.items ?? []).length > 0 && (
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Line items</p>
                      {(activePo?.items ?? []).map((item, idx) => (
                        <div
                          key={item.id ?? idx}
                          className="flex items-center justify-between text-sm border-b border-gray-100 last:border-0 pb-1.5"
                        >
                          <span className="text-gray-700 truncate pr-3">
                            {item.description ?? `Item ${idx + 1}`}
                          </span>
                          <span className="text-gray-500 shrink-0">
                            {Number(item.quantity ?? 0)} × ${Number(item.price ?? 0).toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Accept qty</label>
              <input
                type="number"
                min="0"
                step="1"
                value={acceptQty}
                onChange={(e) => setAcceptQty(e.target.value)}
                placeholder="Qty accepted"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Reject qty</label>
              <input
                type="number"
                min="0"
                step="1"
                value={rejectQty}
                onChange={(e) => setRejectQty(e.target.value)}
                placeholder="Qty rejected"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Receipt Date</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="date"
                value={receiptDate}
                onChange={(e) => setReceiptDate(e.target.value)}
                className="w-full pl-9 pr-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Receipt Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
            >
              <option value="completed">Received in full</option>
              <option value="partial">Partially received</option>
              <option value="pending">Pending inspection</option>
            </select>
          </div>

          <button
            type="button"
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

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-base font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Hash className="h-5 w-5 text-gray-400" /> Recent Receipts
          </h2>
          {receiptsError && (
            <div className="flex items-center gap-2 text-sm text-rose-600 mb-4">
              <AlertCircle className="h-4 w-4" /> Unable to load receipts
            </div>
          )}
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
                      PO: {r.po_id.slice(0, 8)}… · Qty accepted: {r.quantity_received ?? '—'}
                      {r.amount_received != null ? ` · $${Number(r.amount_received).toFixed(2)}` : ''}
                      {' · '}{r.received_date ?? '—'}
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
