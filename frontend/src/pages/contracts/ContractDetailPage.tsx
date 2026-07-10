import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import type { Contract } from '../../api/types';
import { ArrowLeft, FileText, CheckCircle, RefreshCw, DollarSign, Calendar, Upload } from 'lucide-react';
import { ActivityTimeline } from '../../components/audit/ActivityTimeline';
import { useToast } from '../../components/Toast';

const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-600',
  ACTIVE: 'bg-green-100 text-green-700',
  EXPIRED: 'bg-red-100 text-red-600',
  RENEWED: 'bg-blue-100 text-blue-600',
  TERMINATED: 'bg-gray-200 text-gray-500',
};

export default function ContractDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // If id is not a valid UUID (e.g. "new"), show a useful message
  if (id && !UUID_REGEX.test(id)) {
    return (
      <div className="p-8">
        <button onClick={() => navigate('/contracts')} className="text-indigo-600 hover:text-indigo-800 flex items-center gap-1 mb-4">
          <ArrowLeft className="h-4 w-4" /> Back to Contracts
        </button>
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <h2 className="text-lg font-medium text-gray-600">Contract not found</h2>
          <p className="text-sm text-gray-400 mt-1">The contract ID "{id}" is not valid.</p>
        </div>
      </div>
    );
  }

  const { data: contract, isLoading } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => apiGet<Contract>(`/api/v1/contracts/${id}`),
    enabled: !!id,
  });

  const activateMutation = useMutation({
    mutationFn: () => apiPost(`/api/v1/contracts/${id}/activate`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contract', id] }),
  });

  const renewMutation = useMutation({
    mutationFn: () => apiPost(`/api/v1/contracts/${id}/renew`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['contract', id] }),
  });

  if (isLoading) return <div className="text-gray-500 p-8">Loading…</div>;
  if (!contract) return <div className="text-red-500 p-8">Contract not found</div>;

  return (
    <div className="max-w-3xl space-y-6">
      <button onClick={() => navigate('/contracts')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Contracts
      </button>

      {/* Contract info card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-violet-100 rounded-lg">
              <FileText className="h-5 w-5 text-violet-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{contract.contract_number ?? 'Untitled Contract'}</h1>
              <p className="text-sm text-gray-500">ID: {id?.slice(0, 8)}…</p>
            </div>
          </div>
          <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${statusColors[contract.status ?? 'DRAFT'] ?? 'bg-gray-100 text-gray-600'}`}>
            {contract.status ?? 'DRAFT'}
          </span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
              <DollarSign className="h-4 w-4" /> Value
            </div>
            <p className="text-xl font-bold text-gray-900">${Number(contract.contract_value ?? 0).toLocaleString()}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
              <Calendar className="h-4 w-4" /> Start
            </div>
            <p className="font-semibold text-gray-900">{contract.start_date ?? '—'}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
              <Calendar className="h-4 w-4" /> End
            </div>
            <p className="font-semibold text-gray-900">{contract.end_date ?? '—'}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-gray-500 text-sm mb-1">
              <FileText className="h-4 w-4" /> Status
            </div>
            <p className="font-semibold text-gray-900">{contract.status ?? 'DRAFT'}</p>
          </div>
        </div>

        {contract.description && (
          <div className="pt-2">
            <span className="text-sm text-gray-500">Description</span>
            <p className="text-gray-900 mt-1">{contract.description}</p>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3 pt-4 border-t border-gray-100">
          {(contract.status === 'DRAFT') && (
            <button
              onClick={() => activateMutation.mutate()}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700"
            >
              <CheckCircle className="h-4 w-4" /> Activate Contract
            </button>
          )}
          {(contract.status === 'ACTIVE' || contract.status === 'EXPIRED') && (
            <button
              onClick={() => renewMutation.mutate()}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
            >
              <RefreshCw className="h-4 w-4" /> Renew Contract
            </button>
          )}
          <button
            onClick={() => toast('info', 'Upload agreement document — coming in v0.8')}
            className="flex items-center gap-2 text-gray-600 px-4 py-2 rounded-lg text-sm font-medium border border-gray-300 hover:bg-gray-50 transition"
          >
            <Upload className="h-4 w-4" /> Upload Agreement
          </button>
        </div>
      </div>

      {/* Timeline */}
      {id && <ActivityTimeline entityType="contract" entityId={id} />}
    </div>
  );
}
