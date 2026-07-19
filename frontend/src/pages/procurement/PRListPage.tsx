import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPatch, apiPost } from '../../api/client';
import { Plus, CheckCircle, XCircle, Search, ShoppingCart, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import type { PurchaseRequisition, PRCreatePayload, Supplier } from '../../api/types';
import { useToast } from '../../components/Toast';

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-600',
  SUBMITTED: 'bg-blue-100 text-blue-600',
  APPROVED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-600',
  ORDERED: 'bg-purple-100 text-purple-700',
};

export default function PRListPage() {
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState('');
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: prs, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['prs'],
    queryFn: () => apiGet<PurchaseRequisition[]>('/api/v1/purchase-requisitions'),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/purchase-requisitions/${id}/approve`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prs'] });
      queryClient.invalidateQueries({ queryKey: ['pos'] });
    },
  });

  const createPOMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/purchase-requisitions/${id}/create-po`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prs'] });
      queryClient.invalidateQueries({ queryKey: ['pos'] });
    },
  });

  const assignSupplierMutation = useMutation({
    mutationFn: ({ id, supplier_id }: { id: string; supplier_id: string }) =>
      apiPatch(`/api/v1/purchase-requisitions/${id}`, { supplier_id }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['prs'] }),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/purchase-requisitions/${id}/reject`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['prs'] }),
  });

  const createMutation = useMutation({
    mutationFn: (data: PRCreatePayload) =>
      apiPost<PurchaseRequisition>('/api/v1/purchase-requisitions', data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['prs'] });
      setShowForm(false);
      toast('success', `Requisition ${data.pr_number ?? 'created'} submitted successfully`);
    },
    onError: () => {
      toast('error', 'Failed to create requisition. Please try again.');
    },
  });

  const filtered = prs?.filter((pr) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (pr.pr_number ?? '').toLowerCase().includes(q) ||
           (pr.description ?? '').toLowerCase().includes(q);
  });

  const { data: suppliers, isLoading: suppliersLoading } = useQuery({
    queryKey: ['suppliers', 'APPROVED'],
    queryFn: () => apiGet<Supplier[]>('/api/v1/suppliers?status=APPROVED&limit=200'),
    staleTime: 5 * 60 * 1000,
    retry: true,
  });

  const approvedSuppliers = suppliers ?? [];

  const counts = {
    total: prs?.length ?? 0,
    submitted: prs?.filter((p) => p.status === 'SUBMITTED').length ?? 0,
    approved: prs?.filter((p) => p.status === 'APPROVED').length ?? 0,
    rejected: prs?.filter((p) => p.status === 'REJECTED').length ?? 0,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Purchase Requisitions</h1>
          <p className="text-gray-500 mt-1">{filtered?.length ?? 0} of {prs?.length ?? 0} requisitions</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" /> New Requisition
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <p className="text-2xl font-bold text-gray-900">{counts.total}</p>
          <p className="text-sm text-gray-500">Total</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <p className="text-2xl font-bold text-blue-600">{counts.submitted}</p>
          <p className="text-sm text-gray-500">Pending</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <p className="text-2xl font-bold text-green-600">{counts.approved}</p>
          <p className="text-sm text-gray-500">Approved</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <p className="text-2xl font-bold text-red-600">{counts.rejected}</p>
          <p className="text-sm text-gray-500">Rejected</p>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search requisitions…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
        />
      </div>

      {showForm && (
        <CreatePRForm
          suppliers={approvedSuppliers}
          onSubmit={(data) => createMutation.mutate(data)}
          onCancel={() => setShowForm(false)}
          loading={createMutation.isPending}
          suppliersLoading={suppliersLoading}
        />
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
            <p className="text-gray-500 text-sm">Loading requisitions…</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {isError && !isLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-red-200 p-12">
          <div className="flex flex-col items-center gap-3">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <p className="text-red-600 text-sm font-medium">Unable to load requisitions</p>
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

      {/* PR Table */}
      {!isLoading && !isError && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-3 font-medium text-gray-600">PR Number</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Description</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Status</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Created</th>
                <th className="text-right px-6 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered?.map((pr) => (
                <tr key={pr.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-medium text-gray-900">{pr.pr_number ?? '—'}</td>
                  <td className="px-6 py-4 text-gray-500 max-w-xs truncate">{pr.description ?? '—'}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[pr.status] ?? ''}`}>
                      {pr.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-400 text-xs">
                    {pr.created_at ? new Date(pr.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {pr.status === 'SUBMITTED' && (
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={() => approveMutation.mutate(pr.id)}
                          className="inline-flex items-center gap-1 text-green-600 hover:text-green-800 text-xs font-medium"
                        >
                          <CheckCircle className="h-4 w-4" /> Approve
                        </button>
                        <button
                          onClick={() => rejectMutation.mutate(pr.id)}
                          className="inline-flex items-center gap-1 text-red-600 hover:text-red-800 text-xs font-medium"
                        >
                          <XCircle className="h-4 w-4" /> Reject
                        </button>
                      </div>
                    )}
                    {pr.status === 'APPROVED' && (
                      <div className="flex items-center gap-2 justify-end">
                        {!pr.supplier_id && (
                          <select
                            defaultValue=""
                            onChange={(e) => {
                              if (e.target.value) {
                                assignSupplierMutation.mutate({ id: pr.id, supplier_id: e.target.value });
                              }
                            }}
                            className="px-2 py-1 border border-gray-300 rounded text-xs bg-white"
                          >
                            <option value="">Assign supplier…</option>
                            {approvedSuppliers.map((s) => (
                              <option key={s.id} value={s.id}>{s.supplier_name}</option>
                            ))}
                          </select>
                        )}
                        <button
                          onClick={() => createPOMutation.mutate(pr.id)}
                          disabled={!pr.supplier_id || createPOMutation.isPending}
                          className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 text-xs font-medium disabled:opacity-50"
                        >
                          <ShoppingCart className="h-4 w-4" /> Create PO
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
              {(!filtered || filtered.length === 0) && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <p className="text-gray-400 text-sm">No requisitions found.</p>
                      <p className="text-gray-300 text-xs">Create a new requisition or adjust your search.</p>
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

function CreatePRForm({ suppliers, onSubmit, onCancel, loading, suppliersLoading }: {
  suppliers: Supplier[];
  onSubmit: (data: PRCreatePayload) => void;
  onCancel: () => void;
  loading: boolean;
  suppliersLoading?: boolean;
}) {
  const [desc, setDesc] = useState('');
  const [supplierId, setSupplierId] = useState('');
  const [items, setItems] = useState([{ description: '', quantity: 1, unit_price: 0 }]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const subtotal = items.reduce((sum, it) => sum + (it.quantity || 0) * (it.unit_price || 0), 0);
  const tax = subtotal * 0.08; // 8% estimated tax
  const total = subtotal + tax;

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!supplierId) errs.supplier = 'Supplier is required';
    if (!desc.trim()) errs.description = 'Description is required';
    const validItems = items.filter(it => it.description.trim());
    if (validItems.length === 0) errs.items = 'At least one item with a description is required';
    if (validItems.some(it => (it.unit_price ?? 0) <= 0)) errs.price = 'All item prices must be greater than zero';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    onSubmit({
      supplier_id: supplierId,
      description: desc,
      items: items.filter(it => it.description.trim()),
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 space-y-5">
      <h2 className="text-lg font-semibold text-gray-900">New Requisition</h2>

      {suppliersLoading ? (
        <div className="text-center py-8">
          <Loader2 className="h-6 w-6 text-indigo-500 animate-spin mx-auto mb-2" />
          <p className="text-gray-500 text-sm">Loading suppliers...</p>
        </div>
      ) : (
        <>

      {/* Supplier */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Supplier <span className="text-red-500">*</span>
        </label>
        <select
          value={supplierId}
          onChange={(e) => { setSupplierId(e.target.value); setErrors(prev => ({ ...prev, supplier: '' })); }}
          disabled={suppliersLoading}
          className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white ${errors.supplier ? 'border-red-300' : 'border-gray-300'} ${suppliersLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <option value="">{suppliersLoading ? 'Loading suppliers...' : suppliers.length === 0 ? 'No approved suppliers — approve one first' : 'Select a supplier…'}</option>
          {suppliers.map((s) => (
            <option key={s.id} value={s.id}>{s.supplier_name}</option>
          ))}
        </select>
        {errors.supplier && <p className="text-xs text-red-500 mt-1">{errors.supplier}</p>}
        {!suppliersLoading && suppliers.length === 0 && (
          <p className="text-xs text-amber-600 mt-1">
            Go to Suppliers, approve a supplier, then return here to create a requisition.
          </p>
        )}
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description <span className="text-red-500">*</span>
        </label>
        <textarea
          placeholder="Brief description of the requisition purpose"
          value={desc}
          onChange={(e) => { setDesc(e.target.value); setErrors(prev => ({ ...prev, description: '' })); }}
          rows={2}
          className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none ${errors.description ? 'border-red-300' : 'border-gray-300'}`}
        />
        {errors.description && <p className="text-xs text-red-500 mt-1">{errors.description}</p>}
      </div>

      {/* Line items */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Line Items <span className="text-red-500">*</span>
        </label>
        {errors.items && <p className="text-xs text-red-500 mb-2">{errors.items}</p>}
        {errors.price && <p className="text-xs text-red-500 mb-2">{errors.price}</p>}

        {/* Column headers */}
        <div className="hidden sm:grid grid-cols-[1fr_80px_100px_60px] gap-3 px-1 mb-1">
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Item Description</span>
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider text-right">Qty</span>
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider text-right">Unit Price</span>
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider text-right">Total</span>
        </div>

        {items.map((item, i) => (
          <div key={i} className="flex gap-2 mb-2 items-start">
            <input
              placeholder="Item description"
              value={item.description}
              onChange={(e) => {
                const next = [...items];
                next[i] = { ...next[i], description: e.target.value };
                setItems(next);
              }}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
            />
            <input
              type="number"
              min="1"
              placeholder="Qty"
              value={item.quantity || ''}
              onChange={(e) => {
                const next = [...items];
                next[i] = { ...next[i], quantity: Math.max(1, Number(e.target.value)) };
                setItems(next);
              }}
              className="w-16 px-2 py-2 border border-gray-300 rounded-lg text-sm text-right focus:ring-2 focus:ring-indigo-500 outline-none"
            />
            <div className="relative w-24">
              <span className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
              <input
                type="number"
                min="0"
                step="0.01"
                placeholder="0.00"
                value={item.unit_price || ''}
                onChange={(e) => {
                  const next = [...items];
                  next[i] = { ...next[i], unit_price: Number(e.target.value) };
                  setItems(next);
                }}
                className="w-full pl-6 pr-2 py-2 border border-gray-300 rounded-lg text-sm text-right focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
            <div className="w-16 py-2 text-sm text-gray-600 text-right">
              ${((item.quantity || 0) * (item.unit_price || 0)).toLocaleString()}
            </div>
            {items.length > 1 && (
              <button
                onClick={() => setItems(items.filter((_, idx) => idx !== i))}
                className="p-2 text-gray-400 hover:text-red-500"
                title="Remove item"
              >
                ✕
              </button>
            )}
          </div>
        ))}
        <button
          onClick={() => setItems([...items, { description: '', quantity: 1, unit_price: 0 }])}
          className="text-sm text-indigo-600 hover:text-indigo-800 font-medium mt-1"
        >
          + Add item
        </button>
      </div>

      {/* Totals */}
      <div className="border-t border-gray-100 pt-4">
        <div className="max-w-xs ml-auto space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Subtotal</span>
            <span className="text-gray-700 font-medium">${subtotal.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Tax (est. 8%)</span>
            <span className="text-gray-700">${tax.toLocaleString()}</span>
          </div>
          <div className="flex justify-between text-base font-semibold border-t border-gray-200 pt-1">
            <span className="text-gray-900">Total</span>
            <span className="text-gray-900">${total.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 justify-end pt-2 border-t border-gray-100">
        <button onClick={onCancel} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition">
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="px-5 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition font-medium"
        >
          {loading ? 'Creating…' : 'Submit Requisition'}
        </button>
      </div>
      </>
      )}
    </div>
  );
}
