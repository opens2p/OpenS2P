import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import { useNavigate } from 'react-router-dom';
import { Plus, ShieldCheck, ShieldX, Search, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { useState, useMemo } from 'react';
import type { Supplier, SupplierCreatePayload } from '../../api/types';

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-600',
  INVITED: 'bg-blue-100 text-blue-600',
  REGISTERED: 'bg-yellow-100 text-yellow-700',
  APPROVED: 'bg-green-100 text-green-700',
  BLOCKED: 'bg-red-100 text-red-600',
};

export function SupplierListPage() {
  const navigate = useNavigate();
  const [showForm, setShowForm] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const queryClient = useQueryClient();

  const { data: suppliers, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => apiGet<Supplier[]>('/api/v1/suppliers'),
  });

  const createMutation = useMutation({
    mutationFn: (data: SupplierCreatePayload) =>
      apiPost<Supplier>('/api/v1/suppliers', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
      setShowForm(false);
    },
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => apiPost<Supplier>(`/api/v1/suppliers/${id}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['suppliers'] }),
  });

  const filtered = useMemo(() => {
    if (!suppliers) return [];
    return suppliers.filter((s) => {
      if (search && !s.supplier_name.toLowerCase().includes(search.toLowerCase()) &&
          !(s.supplier_number ?? '').toLowerCase().includes(search.toLowerCase())) return false;
      if (statusFilter && s.status !== statusFilter) return false;
      return true;
    });
  }, [suppliers, search, statusFilter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Suppliers</h1>
          <p className="text-gray-500 mt-1">{filtered.length} of {suppliers?.length ?? 0} suppliers</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition"
        >
          <Plus className="h-4 w-4" /> Add Supplier
        </button>
      </div>

      {/* Search & Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search suppliers…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
        >
          <option value="">All Status</option>
          <option value="DRAFT">Draft</option>
          <option value="INVITED">Invited</option>
          <option value="REGISTERED">Registered</option>
          <option value="APPROVED">Approved</option>
          <option value="BLOCKED">Blocked</option>
        </select>
      </div>

      {/* Create form */}
      {showForm && (
        <CreateSupplierForm
          onSubmit={(data) => createMutation.mutate(data)}
          onCancel={() => setShowForm(false)}
          loading={createMutation.isPending}
        />
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
            <p className="text-gray-500 text-sm">Loading suppliers…</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {isError && !isLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-red-200 p-12">
          <div className="flex flex-col items-center gap-3">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <p className="text-red-600 text-sm font-medium">Unable to load suppliers</p>
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

      {/* Table */}
      {!isLoading && !isError && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Name</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Number</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Status</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Risk Score</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Created</th>
                <th className="text-right px-6 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((s) => (
                <tr
                  key={s.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/suppliers/${s.id}`)}
                >
                  <td className="px-6 py-4 font-medium text-gray-900">{s.supplier_name}</td>
                  <td className="px-6 py-4 text-gray-500">{s.supplier_number ?? '—'}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[s.status] ?? ''}`}>
                      {s.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {s.risk_score != null ? (
                      <span className={`text-xs font-medium ${
                        s.risk_score >= 7 ? 'text-red-600' : s.risk_score >= 4 ? 'text-amber-600' : 'text-green-600'
                      }`}>{s.risk_score}/10</span>
                    ) : <span className="text-gray-400">—</span>}
                  </td>
                  <td className="px-6 py-4 text-gray-400 text-xs">
                    {s.created_at ? new Date(s.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {s.status === 'DRAFT' || s.status === 'INVITED' ? (
                      <button
                        onClick={(e) => { e.stopPropagation(); approveMutation.mutate(s.id); }}
                        className="inline-flex items-center gap-1 text-green-600 hover:text-green-800 text-xs font-medium"
                      >
                        <ShieldCheck className="h-4 w-4" /> Approve
                      </button>
                    ) : s.status === 'APPROVED' ? (
                      <span className="inline-flex items-center gap-1 text-green-600 text-xs font-medium">
                        <ShieldCheck className="h-4 w-4" /> Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-red-400 text-xs">
                        <ShieldX className="h-4 w-4" /> {s.status}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <p className="text-gray-400 text-sm">No suppliers found.</p>
                      <p className="text-gray-300 text-xs">Add a supplier or adjust your search filters.</p>
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

function CreateSupplierForm({
  onSubmit,
  onCancel,
  loading,
}: {
  onSubmit: (data: SupplierCreatePayload) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const [name, setName] = useState('');
  const [number, setNumber] = useState('');
  const [description, setDescription] = useState('');

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">New Supplier</h2>
      <div className="space-y-4">
        <input
          placeholder="Supplier name *"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
        />
        <input
          placeholder="Supplier number"
          value={number}
          onChange={(e) => setNumber(e.target.value)}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
        />
        <textarea
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
        />
        <div className="flex gap-3 justify-end">
          <button onClick={onCancel} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
          <button
            onClick={() => onSubmit({ supplier_name: name, supplier_number: number, description })}
            disabled={!name || loading}
            className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? 'Creating…' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  );
}
