import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../../api/client';
import type { Contract } from '../../api/types';
import { ArrowLeft, FileText } from 'lucide-react';
import { ActivityTimeline } from '../../components/audit/ActivityTimeline';

export default function ContractDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: contract, isLoading } = useQuery({
    queryKey: ['contract', id],
    queryFn: () => apiGet<Contract>(`/api/v1/contracts/${id}`),
    enabled: !!id,
  });

  if (isLoading) return <div className="text-gray-500 p-8">Loading…</div>;
  if (!contract) return <div className="text-red-500 p-8">Contract not found</div>;

  return (
    <div className="max-w-3xl space-y-6">
      <button onClick={() => navigate('/contracts')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Contracts
      </button>

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
        </div>

        <div className="grid grid-cols-2 gap-6 text-sm">
          <div>
            <span className="text-gray-500">Contract Value</span>
            <p className="font-medium text-gray-900 mt-0.5">${Number(contract.contract_value ?? 0).toLocaleString()}</p>
          </div>
          <div>
            <span className="text-gray-500">Start Date</span>
            <p className="font-medium text-gray-900 mt-0.5">{contract.start_date ?? 'Not set'}</p>
          </div>
          <div>
            <span className="text-gray-500">End Date</span>
            <p className="font-medium text-gray-900 mt-0.5">{contract.end_date ?? 'Not set'}</p>
          </div>
          <div>
            <span className="text-gray-500">Description</span>
            <p className="font-medium text-gray-900 mt-0.5">{contract.description ?? '—'}</p>
          </div>
        </div>
      </div>

      {id && <ActivityTimeline entityType="contract" entityId={id} />}
    </div>
  );
}
