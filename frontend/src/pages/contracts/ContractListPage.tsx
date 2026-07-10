import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiGet } from '../../api/client';
import type { Contract } from '../../api/types';
import { Plus, Search, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import { useState, useMemo } from 'react';

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-600',
  ACTIVE: 'bg-green-100 text-green-700',
  EXPIRED: 'bg-red-100 text-red-600',
  RENEWED: 'bg-blue-100 text-blue-600',
  TERMINATED: 'bg-gray-200 text-gray-500',
};

export default function ContractListPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');

  const { data: contracts, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['contracts'],
    queryFn: () => apiGet<Contract[]>('/api/v1/contracts'),
  });

  const filtered = useMemo(() => {
    if (!contracts) return [];
    if (!search) return contracts;
    const q = search.toLowerCase();
    return contracts.filter((c) =>
      (c.contract_number ?? '').toLowerCase().includes(q) ||
      (c.description ?? '').toLowerCase().includes(q)
    );
  }, [contracts, search]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Contracts</h1>
          <p className="text-gray-500 mt-1">{filtered.length} of {contracts?.length ?? 0} contracts</p>
        </div>
        <button
          onClick={() => navigate('/contracts')}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50"
          disabled
          title="Create contract form coming soon"
        >
          <Plus className="h-4 w-4" /> New Contract
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search contracts…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
        />
      </div>

      {/* Table */}
      {/* Loading state */}
      {isLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
            <p className="text-gray-500 text-sm">Loading contracts…</p>
          </div>
        </div>
      )}

      {/* Error state */}
      {isError && !isLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-red-200 p-12">
          <div className="flex flex-col items-center gap-3">
            <AlertCircle className="h-8 w-8 text-red-400" />
            <p className="text-red-600 text-sm font-medium">Unable to load contracts</p>
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

      {/* Contracts Table */}
      {!isLoading && !isError && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Contract #</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Value</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Start Date</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">End Date</th>
                <th className="text-left px-6 py-3 font-medium text-gray-600">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtered.map((c) => (
                <tr
                  key={c.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/contracts/${c.id}`)}
                >
                  <td className="px-6 py-4 font-medium text-gray-900">{c.contract_number ?? '—'}</td>
                  <td className="px-6 py-4 text-gray-900 font-medium">
                    ${Number(c.contract_value ?? 0).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-gray-500">{c.start_date ?? '—'}</td>
                  <td className="px-6 py-4 text-gray-500">{c.end_date ?? '—'}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[c.status ?? 'DRAFT'] ?? 'bg-gray-100 text-gray-600'}`}>
                      {c.status ?? 'DRAFT'}
                    </span>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <p className="text-gray-400 text-sm">No contracts found.</p>
                      <p className="text-gray-300 text-xs">Contracts will appear here once created from suppliers.</p>
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
