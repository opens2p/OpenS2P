import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import type { Supplier } from '../../api/types';
import { ArrowLeft, ShieldCheck, ShieldAlert } from 'lucide-react';
import { ActivityTimeline } from '../../components/audit/ActivityTimeline';

export default function SupplierDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: supplier, isLoading } = useQuery({
    queryKey: ['supplier', id],
    queryFn: () => apiGet<Supplier>(`/api/v1/suppliers/${id}`),
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

  if (isLoading) return <div className="text-gray-500 p-8">Loading…</div>;
  if (!supplier) return <div className="text-red-500 p-8">Supplier not found</div>;

  return (
    <div className="max-w-2xl space-y-6">
      <button onClick={() => navigate('/suppliers')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Suppliers
      </button>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{supplier.supplier_name}</h1>
            <p className="text-gray-500 text-sm mt-1">{supplier.supplier_number ?? 'No number'}</p>
          </div>
          <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${
            supplier.status === 'APPROVED' ? 'bg-green-100 text-green-700' :
            supplier.status === 'BLOCKED' ? 'bg-red-100 text-red-600' :
            'bg-gray-100 text-gray-600'
          }`}>
            {supplier.status}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Risk Score</span>
            <p className="font-medium text-gray-900">{supplier.risk_score ?? 'Not assessed'}</p>
          </div>
          <div>
            <span className="text-gray-500">Status</span>
            <p className="font-medium text-gray-900">{supplier.status}</p>
          </div>
        </div>

        {supplier.description && (
          <div>
            <span className="text-sm text-gray-500">Description</span>
            <p className="text-gray-900 mt-1">{supplier.description}</p>
          </div>
        )}

        <div className="flex gap-3 pt-4 border-t border-gray-100">
          {(supplier.status === 'DRAFT' || supplier.status === 'INVITED') && (
            <button
              onClick={() => approveMutation.mutate()}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700"
            >
              <ShieldCheck className="h-4 w-4" /> Approve Supplier
            </button>
          )}
          {supplier.status === 'APPROVED' && (
            <button
              onClick={() => blockMutation.mutate()}
              className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700"
            >
              <ShieldAlert className="h-4 w-4" /> Block Supplier
            </button>
          )}
        </div>
      </div>

      {id && <ActivityTimeline entityType="supplier" entityId={id} />}
    </div>
  );
}
