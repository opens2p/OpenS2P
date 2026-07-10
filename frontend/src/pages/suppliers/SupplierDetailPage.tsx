import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import type { Supplier, Contract, PurchaseOrder } from '../../api/types';
import { ArrowLeft, ShieldCheck, ShieldAlert, FileText, ShoppingCart, Trash2, Upload } from 'lucide-react';
import { ActivityTimeline } from '../../components/audit/ActivityTimeline';
import { useState } from 'react';
import { useToast } from '../../components/Toast';

type Tab = 'overview' | 'contracts' | 'purchase-history' | 'activity';

export default function SupplierDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  const { data: supplier, isLoading } = useQuery({
    queryKey: ['supplier', id],
    queryFn: () => apiGet<Supplier>(`/api/v1/suppliers/${id}`),
    enabled: !!id,
  });

  const { data: contracts } = useQuery({
    queryKey: ['supplier-contracts', id],
    queryFn: () => apiGet<Contract[]>(`/api/v1/suppliers/${id}/contracts`),
    enabled: !!id,
  });

  const { data: purchaseOrders } = useQuery({
    queryKey: ['supplier-pos', id],
    queryFn: () => apiGet<PurchaseOrder[]>(`/api/v1/suppliers/${id}/purchase-orders`),
    enabled: !!id,
  });

  const approveMutation = useMutation({
    mutationFn: () => apiPost<Supplier>(`/api/v1/suppliers/${id}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['supplier', id] }),
  });

  const blockMutation = useMutation({
    mutationFn: () => apiPost<Supplier>(`/api/v1/suppliers/${id}/block`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['supplier', id] }),
  });

  const deleteMutation = useMutation({
    mutationFn: () => apiPost(`/api/v1/suppliers/${id}/delete`),
    onSuccess: () => navigate('/suppliers'),
  });

  if (isLoading) return <div className="text-gray-500 p-8">Loading…</div>;
  if (!supplier) return <div className="text-red-500 p-8">Supplier not found</div>;

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: 'overview', label: 'Overview', icon: ShieldCheck },
    { key: 'contracts', label: 'Contracts', icon: FileText },
    { key: 'purchase-history', label: 'Purchase History', icon: ShoppingCart },
    { key: 'activity', label: 'Activity', icon: ArrowLeft },
  ];

  return (
    <div className="space-y-6">
      <button onClick={() => navigate('/suppliers')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Suppliers
      </button>

      {/* Supplier header card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="h-14 w-14 rounded-xl bg-indigo-50 flex items-center justify-center text-xl font-bold text-indigo-600">
              {supplier.supplier_name?.charAt(0).toUpperCase()}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{supplier.supplier_name}</h1>
              <p className="text-gray-500 text-sm">{supplier.supplier_number ?? 'No number'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${
              supplier.status === 'APPROVED' ? 'bg-green-100 text-green-700' :
              supplier.status === 'BLOCKED' ? 'bg-red-100 text-red-600' :
              'bg-gray-100 text-gray-600'
            }`}>
              {supplier.status}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6 mt-6 text-sm">
          <div>
            <span className="text-gray-500">Risk Score</span>
            <p className="font-medium text-gray-900 mt-0.5">
              {supplier.risk_score != null ? (
                <span className={`${
                  supplier.risk_score >= 7 ? 'text-red-600' : supplier.risk_score >= 4 ? 'text-amber-600' : 'text-green-600'
                }`}>{supplier.risk_score}/10</span>
              ) : 'Not assessed'}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Contracts</span>
            <p className="font-medium text-gray-900 mt-0.5">{contracts?.length ?? 0}</p>
          </div>
          <div>
            <span className="text-gray-500">Purchase Orders</span>
            <p className="font-medium text-gray-900 mt-0.5">{purchaseOrders?.length ?? 0}</p>
          </div>
        </div>

        {supplier.description && (
          <p className="text-sm text-gray-600 mt-4 pt-4 border-t border-gray-100">{supplier.description}</p>
        )}

        <div className="flex gap-3 mt-6 pt-4 border-t border-gray-100">
          {(supplier.status === 'DRAFT' || supplier.status === 'INVITED') && (
            <button onClick={() => approveMutation.mutate()}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700">
              <ShieldCheck className="h-4 w-4" /> Approve
            </button>
          )}
          {supplier.status === 'APPROVED' && (
            <button onClick={() => blockMutation.mutate()}
              className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700">
              <ShieldAlert className="h-4 w-4" /> Block
            </button>
          )}
          <button onClick={() => deleteMutation.mutate()}
            className="flex items-center gap-2 text-red-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-50">
            <Trash2 className="h-4 w-4" /> Delete
          </button>
        </div>

        {/* Documents */}
        <div className="mt-6 pt-4 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Documents</p>
          <div className="flex flex-wrap gap-2">
            {['Certificate', 'W9', 'Insurance'].map((doc) => (
              <button
                key={doc}
                onClick={() => toast('info', `Upload ${doc} — coming in v0.8`)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition"
              >
                <Upload className="h-3.5 w-3.5" /> Upload {doc}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-6">
          {tabs.map((tab) => {
            const active = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                  active ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <span className="flex items-center gap-2">
                  <tab.icon className="h-4 w-4" /> {tab.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === 'overview' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">Supplier Details</h3>
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div><dt className="text-gray-500">Name</dt><dd className="font-medium text-gray-900">{supplier.supplier_name}</dd></div>
            <div><dt className="text-gray-500">Number</dt><dd className="font-medium text-gray-900">{supplier.supplier_number ?? '—'}</dd></div>
            <div><dt className="text-gray-500">Status</dt><dd className="font-medium text-gray-900">{supplier.status}</dd></div>
            <div><dt className="text-gray-500">Risk Score</dt><dd className="font-medium text-gray-900">{supplier.risk_score ?? '—'}</dd></div>
            <div><dt className="text-gray-500">Created</dt><dd className="font-medium text-gray-900">{supplier.created_at ? new Date(supplier.created_at).toLocaleDateString() : '—'}</dd></div>
            <div><dt className="text-gray-500">Active</dt><dd className="font-medium text-gray-900">{supplier.is_active ? 'Yes' : 'No'}</dd></div>
          </dl>
        </div>
      )}

      {activeTab === 'contracts' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {contracts && contracts.length > 0 ? (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-6 py-3 font-medium text-gray-600">Contract #</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-600">Value</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-600">Start</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-600">End</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {contracts.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/contracts/${c.id}`)}>
                    <td className="px-6 py-4 font-medium text-gray-900">{c.contract_number ?? '—'}</td>
                    <td className="px-6 py-4 text-gray-900">${Number(c.contract_value ?? 0).toLocaleString()}</td>
                    <td className="px-6 py-4 text-gray-500">{c.start_date ?? '—'}</td>
                    <td className="px-6 py-4 text-gray-500">{c.end_date ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-sm text-gray-400 p-6">No contracts for this supplier.</p>
          )}
        </div>
      )}

      {activeTab === 'purchase-history' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {purchaseOrders && purchaseOrders.length > 0 ? (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-6 py-3 font-medium text-gray-600">PO #</th>
                  <th className="text-left px-6 py-3 font-medium text-gray-600">Status</th>
                  <th className="text-right px-6 py-3 font-medium text-gray-600">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {purchaseOrders.map((po) => (
                  <tr key={po.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/procurement/pos`)}>
                    <td className="px-6 py-4 font-medium text-gray-900">{po.po_number ?? '—'}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">{po.status}</span>
                    </td>
                    <td className="px-6 py-4 text-right text-gray-900">
                      ${(po.items ?? []).reduce((sum, item) => sum + (item.price ?? 0) * (item.quantity ?? 0), 0).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-sm text-gray-400 p-6">No purchase orders for this supplier.</p>
          )}
        </div>
      )}

      {activeTab === 'activity' && id && (
        <ActivityTimeline entityType="supplier" entityId={id} />
      )}
    </div>
  );
}
