import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import { Plus, CheckCircle } from 'lucide-react';
import type { PurchaseRequisition, PRCreatePayload } from '../../api/types';

const statusColors: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-600',
  SUBMITTED: 'bg-blue-100 text-blue-600',
  APPROVED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-600',
};

export default function PRListPage() {
  const [showForm, setShowForm] = useState(false);
  const queryClient = useQueryClient();

  const { data: prs } = useQuery({
    queryKey: ['prs'],
    queryFn: () => apiGet<PurchaseRequisition[]>('/api/v1/purchase-requisitions'),
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/purchase-requisitions/${id}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['prs'] }),
  });

  const createMutation = useMutation({
    mutationFn: (data: PRCreatePayload) =>
      apiPost<PurchaseRequisition>('/api/v1/purchase-requisitions', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prs'] });
      setShowForm(false);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Purchase Requisitions</h1>
          <p className="text-gray-500 mt-1">{prs?.length ?? 0} requisitions</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" /> New Requisition
        </button>
      </div>

      {showForm && (
        <CreatePRForm
          onSubmit={(data) => createMutation.mutate(data)}
          onCancel={() => setShowForm(false)}
          loading={createMutation.isPending}
        />
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="text-left px-6 py-3 font-medium text-gray-600">PR Number</th>
              <th className="text-left px-6 py-3 font-medium text-gray-600">Description</th>
              <th className="text-left px-6 py-3 font-medium text-gray-600">Status</th>
              <th className="text-right px-6 py-3 font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {prs?.map((pr) => (
              <tr key={pr.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 font-medium text-gray-900">{pr.pr_number ?? '—'}</td>
                <td className="px-6 py-4 text-gray-500 max-w-xs truncate">{pr.description ?? '—'}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[pr.status] ?? ''}`}>
                    {pr.status}
                  </span>
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
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CreatePRForm({ onSubmit, onCancel, loading }: {
  onSubmit: (data: PRCreatePayload) => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const [desc, setDesc] = useState('');
  const [items, setItems] = useState([{ description: '', quantity: 1, unit_price: 0 }]);

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">New Requisition</h2>
      <textarea
        placeholder="Description"
        value={desc}
        onChange={(e) => setDesc(e.target.value)}
        rows={2}
        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
      />
      {items.map((item, i) => (
        <div key={i} className="flex gap-3">
          <input
            placeholder="Item description"
            value={item.description}
            onChange={(e) => {
              const next = [...items];
              next[i] = { ...next[i], description: e.target.value };
              setItems(next);
            }}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
          />
          <input
            type="number"
            placeholder="Qty"
            value={item.quantity}
            onChange={(e) => {
              const next = [...items];
              next[i] = { ...next[i], quantity: Number(e.target.value) };
              setItems(next);
            }}
            className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
          />
          <input
            type="number"
            placeholder="Price"
            value={item.unit_price}
            onChange={(e) => {
              const next = [...items];
              next[i] = { ...next[i], unit_price: Number(e.target.value) };
              setItems(next);
            }}
            className="w-28 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
          />
        </div>
      ))}
      <button
        onClick={() => setItems([...items, { description: '', quantity: 1, unit_price: 0 }])}
        className="text-sm text-indigo-600 hover:text-indigo-800"
      >
        + Add item
      </button>
      <div className="flex gap-3 justify-end pt-2">
        <button onClick={onCancel} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
        <button
          onClick={() => onSubmit({ description: desc, items })}
          disabled={loading}
          className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Creating…' : 'Submit'}
        </button>
      </div>
    </div>
  );
}
