import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiGet } from '../../api/client';
import type { Contract } from '../../api/types';
import { FileText } from 'lucide-react';

export default function ContractListPage() {
  const navigate = useNavigate();

  const { data: contracts } = useQuery({
    queryKey: ['contracts'],
    queryFn: () => apiGet<Contract[]>('/api/v1/contracts'),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Contracts</h1>
        <p className="text-gray-500 mt-1">{contracts?.length ?? 0} contracts</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {contracts?.map((c) => (
          <button
            key={c.id}
            onClick={() => navigate(`/contracts/${c.id}`)}
            className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition text-left"
          >
            <div className="p-2 bg-violet-100 rounded-lg w-fit mb-3">
              <FileText className="h-5 w-5 text-violet-600" />
            </div>
            <h3 className="font-semibold text-gray-900">{c.contract_number ?? 'Untitled'}</h3>
            <p className="text-sm text-gray-500 mt-1">
              ${Number(c.contract_value ?? 0).toLocaleString()}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {c.start_date ?? '—'} → {c.end_date ?? '—'}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}
