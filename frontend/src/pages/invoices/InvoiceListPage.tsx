import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiGet, apiPost } from '../../api/client';
import type { AutoResolveResponse, Invoice, InvoiceCreatePayload, PurchaseOrder } from '../../api/types';
import {
  CheckCircle, AlertTriangle, Search, AlertCircle, RefreshCw, Loader2,
  Bot, FileCheck, Plus, Send, X,
} from 'lucide-react';
import { useState, useMemo, useEffect, type FormEvent } from 'react';
import { useToast } from '../../components/Toast';

const matchColors: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-700',
  MATCHED: 'bg-green-100 text-green-700',
  EXCEPTION: 'bg-red-100 text-red-600',
};

const invoiceableStatuses = new Set([
  'SENT', 'ACKNOWLEDGED', 'PARTIALLY_RECEIVED', 'RECEIVED', 'APPROVED', 'CREATED',
]);

function exceptionReason(inv: Invoice): string | null {
  const issues = inv.extras?.match_result?.issues;
  if (issues && issues.length > 0) return issues[0].message;
  const code = inv.extras?.match_result?.primary_issue;
  return code ? String(code) : null;
}

function poTotal(po: PurchaseOrder): number {
  return (po.items ?? []).reduce(
    (sum, item) => sum + Number(item.price ?? 0) * Number(item.quantity ?? 0),
    0,
  );
}

function paymentLabel(inv: Invoice): string {
  if (inv.extras?.payment_status === 'SENT_TO_PAYMENT') return 'Sent to Payment';
  if (inv.match_status === 'MATCHED') return 'Ready for Payment';
  return '—';
}

export default function InvoiceListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [filter, setFilter] = useState<string>('');
  const [search, setSearch] = useState('');
  const [manualNote, setManualNote] = useState('');
  const [manualForId, setManualForId] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [poId, setPoId] = useState('');
  const [amount, setAmount] = useState('');
  const [invoiceNumber, setInvoiceNumber] = useState('');
  const [invoiceDate, setInvoiceDate] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [runMatchAfterCreate, setRunMatchAfterCreate] = useState(true);

  const { data: invoices, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['invoices', { limit: 200 }],
    queryFn: () => apiGet<Invoice[]>('/api/v1/invoices?limit=200'),
  });

  const { data: pos } = useQuery({
    queryKey: ['pos'],
    queryFn: () => apiGet<PurchaseOrder[]>('/api/v1/purchase-orders?limit=200'),
    enabled: showCreate,
  });

  const { data: selectedPo } = useQuery({
    queryKey: ['po', poId],
    queryFn: () => apiGet<PurchaseOrder>(`/api/v1/purchase-orders/${poId}`),
    enabled: showCreate && !!poId,
  });

  const selectablePos = useMemo(() => {
    if (!pos) return [];
    return pos.filter((po) => invoiceableStatuses.has(String(po.status)));
  }, [pos]);

  useEffect(() => {
    if (!selectedPo) return;
    const total = poTotal(selectedPo);
    if (total > 0) setAmount(total.toFixed(2));
    const base = selectedPo.po_number ?? selectedPo.id.slice(0, 8);
    setInvoiceNumber(`INV-${base}`);
  }, [selectedPo]);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['invoices'] });
    queryClient.invalidateQueries({ queryKey: ['match-context'] });
  };

  const createMutation = useMutation({
    mutationFn: async (payload: InvoiceCreatePayload) => {
      const created = await apiPost<Invoice>('/api/v1/invoices', payload);
      if (runMatchAfterCreate) {
        return apiPost<Invoice>(`/api/v1/invoices/${created.id}/match`);
      }
      return created;
    },
    onSuccess: (inv) => {
      invalidate();
      setShowCreate(false);
      setPoId('');
      setAmount('');
      setInvoiceNumber('');
      setInvoiceDate('');
      setDueDate('');
      toast(
        'success',
        inv.match_status === 'EXCEPTION'
          ? 'Invoice created — exception needs review'
          : inv.match_status === 'MATCHED'
            ? 'Invoice created and matched — ready for payment'
            : 'Invoice created',
      );
      navigate(`/invoices/${inv.id}`);
    },
    onError: (err: Error) => toast('error', err.message || 'Create failed'),
  });

  const matchMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/invoices/${id}/match`),
    onSuccess: () => {
      invalidate();
      toast('success', 'Match completed');
    },
    onError: (err: Error) => toast('error', err.message || 'Match failed'),
  });

  const autoResolveMutation = useMutation({
    mutationFn: (id: string) =>
      apiPost<AutoResolveResponse>(`/api/v1/ai/invoice/${id}/resolve-exception`),
    onSuccess: (data) => {
      invalidate();
      if (data.success) toast('success', data.explanation || 'Exception auto-resolved — ready for payment');
      else toast('error', data.error || 'Could not auto-resolve');
    },
    onError: (err: Error) => toast('error', err.message || 'Auto-resolve failed'),
  });

  const manualResolveMutation = useMutation({
    mutationFn: ({ id, note }: { id: string; note: string }) =>
      apiPost(`/api/v1/invoices/${id}/resolve-exception`, { mode: 'manual', note }),
    onSuccess: () => {
      invalidate();
      setManualForId(null);
      setManualNote('');
      toast('success', 'Exception cleared — invoice ready for payment');
    },
    onError: (err: Error) => toast('error', err.message || 'Manual resolve failed'),
  });

  const sendToPaymentMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/invoices/${id}/pay`),
    onSuccess: () => {
      invalidate();
      toast('success', 'Invoice sent to payment');
    },
    onError: (err: Error) => toast('error', err.message || 'Send to payment failed'),
  });

  const filtered = useMemo(() => {
    if (!invoices) return [];
    return invoices.filter((inv) => {
      if (filter === 'READY') {
        if (inv.match_status !== 'MATCHED' || inv.extras?.payment_status === 'SENT_TO_PAYMENT') {
          return false;
        }
      } else if (filter === 'SENT') {
        if (inv.extras?.payment_status !== 'SENT_TO_PAYMENT') return false;
      } else if (filter && inv.match_status !== filter) {
        return false;
      }
      if (search) {
        const q = search.toLowerCase();
        return (inv.invoice_number ?? '').toLowerCase().includes(q)
          || inv.po_id.toLowerCase().includes(q);
      }
      return true;
    });
  }, [invoices, filter, search]);

  const counts = {
    total: invoices?.length ?? 0,
    pending: invoices?.filter((i) => i.match_status === 'PENDING').length ?? 0,
    matched: invoices?.filter((i) => i.match_status === 'MATCHED').length ?? 0,
    exceptions: invoices?.filter((i) => i.match_status === 'EXCEPTION').length ?? 0,
    ready: invoices?.filter(
      (i) => i.match_status === 'MATCHED' && i.extras?.payment_status !== 'SENT_TO_PAYMENT',
    ).length ?? 0,
  };

  const submitCreate = (e: FormEvent) => {
    e.preventDefault();
    if (!poId) {
      toast('error', 'Select a purchase order');
      return;
    }
    const amt = Number(amount);
    if (!Number.isFinite(amt) || amt < 0) {
      toast('error', 'Enter a valid amount');
      return;
    }
    const payload: InvoiceCreatePayload = {
      po_id: poId,
      amount: amt,
    };
    if (invoiceNumber.trim()) payload.invoice_number = invoiceNumber.trim();
    if (invoiceDate) payload.invoice_date = invoiceDate;
    if (dueDate) payload.due_date = dueDate;
    createMutation.mutate(payload);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Invoices</h1>
          <p className="text-gray-500 mt-1">
            Create from PO → match / resolve exceptions → send to payment
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowCreate((v) => !v)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700"
        >
          {showCreate ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
          {showCreate ? 'Close' : 'Create from PO'}
        </button>
      </div>

      {showCreate && (
        <form
          onSubmit={submitCreate}
          className="bg-white rounded-xl border border-indigo-100 shadow-sm p-5 space-y-4"
        >
          <div>
            <h2 className="text-sm font-semibold text-gray-900">Create invoice from purchase order</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Amount defaults to PO total. Run match after create to check PO + GRN.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="block text-sm">
              <span className="text-gray-600 font-medium">Purchase Order</span>
              <select
                value={poId}
                onChange={(e) => setPoId(e.target.value)}
                className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
                required
              >
                <option value="">Select PO…</option>
                {selectablePos.map((po) => {
                  const total = poTotal(selectedPo?.id === po.id ? selectedPo : po);
                  return (
                    <option key={po.id} value={po.id}>
                      {po.po_number ?? po.id.slice(0, 8)} · {String(po.status)}
                      {total > 0 ? ` · $${total.toFixed(2)}` : ''}
                    </option>
                  );
                })}
              </select>
            </label>
            <label className="block text-sm">
              <span className="text-gray-600 font-medium">Invoice number</span>
              <input
                value={invoiceNumber}
                onChange={(e) => setInvoiceNumber(e.target.value)}
                placeholder="INV-…"
                className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </label>
            <label className="block text-sm">
              <span className="text-gray-600 font-medium">Amount</span>
              <input
                type="number"
                min="0"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
                required
              />
            </label>
            <label className="block text-sm">
              <span className="text-gray-600 font-medium">Invoice date</span>
              <input
                type="date"
                value={invoiceDate}
                onChange={(e) => setInvoiceDate(e.target.value)}
                className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </label>
            <label className="block text-sm">
              <span className="text-gray-600 font-medium">Due date</span>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700 mt-6">
              <input
                type="checkbox"
                checked={runMatchAfterCreate}
                onChange={(e) => setRunMatchAfterCreate(e.target.checked)}
                className="rounded border-gray-300"
              />
              Run 3-way match after create
            </label>
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
            >
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
              Create Invoice
            </button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <button onClick={() => setFilter('')}
          className={`bg-white rounded-xl p-4 shadow-sm border text-left transition ${!filter ? 'ring-2 ring-indigo-500' : 'border-gray-200 hover:shadow-md'}`}>
          <p className="text-2xl font-bold text-gray-900">{counts.total}</p>
          <p className="text-sm text-gray-500">All</p>
        </button>
        <button onClick={() => setFilter('PENDING')}
          className={`bg-white rounded-xl p-4 shadow-sm border text-left transition ${filter === 'PENDING' ? 'ring-2 ring-yellow-500' : 'border-gray-200 hover:shadow-md'}`}>
          <p className="text-2xl font-bold text-yellow-600">{counts.pending}</p>
          <p className="text-sm text-gray-500">Pending Match</p>
        </button>
        <button onClick={() => setFilter('EXCEPTION')}
          className={`bg-white rounded-xl p-4 shadow-sm border text-left transition ${filter === 'EXCEPTION' ? 'ring-2 ring-red-500' : 'border-gray-200 hover:shadow-md'}`}>
          <p className="text-2xl font-bold text-red-600">{counts.exceptions}</p>
          <p className="text-sm text-gray-500">Exceptions</p>
        </button>
        <button onClick={() => setFilter('READY')}
          className={`bg-white rounded-xl p-4 shadow-sm border text-left transition ${filter === 'READY' ? 'ring-2 ring-emerald-500' : 'border-gray-200 hover:shadow-md'}`}>
          <p className="text-2xl font-bold text-emerald-600">{counts.ready}</p>
          <p className="text-sm text-gray-500">Ready for Payment</p>
        </button>
        <button onClick={() => setFilter('MATCHED')}
          className={`bg-white rounded-xl p-4 shadow-sm border text-left transition ${filter === 'MATCHED' ? 'ring-2 ring-green-500' : 'border-gray-200 hover:shadow-md'}`}>
          <p className="text-2xl font-bold text-green-600">{counts.matched}</p>
          <p className="text-sm text-gray-500">Matched</p>
        </button>
      </div>

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

      {isLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
            <p className="text-gray-500 text-sm">Loading invoices…</p>
          </div>
        </div>
      )}

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

      {!isLoading && !isError && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Invoice</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">PO</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Amount</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Match</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Payment</th>
                <th className="text-right px-6 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((inv) => {
                const sent = inv.extras?.payment_status === 'SENT_TO_PAYMENT';
                return (
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
                    <td className="px-6 py-4">
                      <span className={`text-xs font-medium ${
                        sent ? 'text-indigo-700' : inv.match_status === 'MATCHED' ? 'text-emerald-700' : 'text-gray-400'
                      }`}>
                        {paymentLabel(inv)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right" onClick={(e) => e.stopPropagation()}>
                      {inv.match_status === 'PENDING' && (
                        <button
                          onClick={() => matchMutation.mutate(inv.id)}
                          disabled={matchMutation.isPending}
                          className="inline-flex items-center gap-1 text-green-600 hover:text-green-800 text-xs font-medium disabled:opacity-50"
                        >
                          <CheckCircle className="h-4 w-4" /> Match
                        </button>
                      )}
                      {inv.match_status === 'EXCEPTION' && (
                        <div className="flex flex-col items-end gap-1.5 max-w-xs ml-auto">
                          {exceptionReason(inv) && (
                            <p className="text-[11px] text-rose-600 text-right leading-snug">
                              {exceptionReason(inv)}
                            </p>
                          )}
                          <div className="flex flex-wrap gap-2 justify-end">
                            <button
                              onClick={() => autoResolveMutation.mutate(inv.id)}
                              disabled={autoResolveMutation.isPending}
                              className="inline-flex items-center gap-1 text-cyan-700 hover:text-cyan-900 text-xs font-medium disabled:opacity-50"
                            >
                              <Bot className="h-4 w-4" /> Auto-Resolve
                            </button>
                            <button
                              onClick={() => {
                                setManualForId(inv.id);
                                setManualNote('');
                              }}
                              className="inline-flex items-center gap-1 text-amber-700 hover:text-amber-900 text-xs font-medium"
                            >
                              <FileCheck className="h-4 w-4" /> Manual
                            </button>
                            <button
                              onClick={() => navigate('/matching', { state: { invoiceId: inv.id } })}
                              className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 text-xs font-medium"
                            >
                              Open
                            </button>
                          </div>
                          {manualForId === inv.id && (
                            <div className="flex gap-1.5 w-full mt-1">
                              <input
                                autoFocus
                                value={manualNote}
                                onChange={(e) => setManualNote(e.target.value)}
                                placeholder="Resolution note (required)"
                                className="flex-1 px-2 py-1 border border-gray-300 rounded text-xs outline-none focus:ring-1 focus:ring-amber-500"
                              />
                              <button
                                onClick={() => {
                                  if (!manualNote.trim()) {
                                    toast('error', 'Enter a resolution note');
                                    return;
                                  }
                                  manualResolveMutation.mutate({ id: inv.id, note: manualNote.trim() });
                                }}
                                disabled={manualResolveMutation.isPending}
                                className="px-2 py-1 bg-amber-600 text-white rounded text-xs font-medium hover:bg-amber-700 disabled:opacity-50"
                              >
                                Clear
                              </button>
                              <button
                                onClick={() => setManualForId(null)}
                                className="px-2 py-1 text-gray-500 text-xs hover:text-gray-700"
                              >
                                Cancel
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                      {inv.match_status === 'MATCHED' && !sent && (
                        <button
                          onClick={() => sendToPaymentMutation.mutate(inv.id)}
                          disabled={sendToPaymentMutation.isPending}
                          className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 text-xs font-medium disabled:opacity-50"
                        >
                          <Send className="h-4 w-4" /> Send to Payment
                        </button>
                      )}
                      {sent && (
                        <span className="inline-flex items-center gap-1 text-xs text-indigo-600 font-medium">
                          <CheckCircle className="h-4 w-4" /> Sent
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <p className="text-gray-400 text-sm">No invoices found.</p>
                      <button
                        type="button"
                        onClick={() => setShowCreate(true)}
                        className="text-indigo-600 text-xs font-medium hover:text-indigo-800"
                      >
                        Create an invoice from a PO
                      </button>
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
