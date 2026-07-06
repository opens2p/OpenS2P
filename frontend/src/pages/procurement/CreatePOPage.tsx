import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiGet, apiPost } from '../../api/client';
import type { Supplier, PurchaseOrder } from '../../api/types';
import { ArrowLeft, Plus } from 'lucide-react';

export default function CreatePOPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedSupplier, setSelectedSupplier] = useState('');
  const [items, setItems] = useState([{ description: '', quantity: 1, price: 0 }]);

  const { data: suppliers } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => apiGet<Supplier[]>('/api/v1/suppliers'),
  });

  const createMutation = useMutation({
    mutationFn: (data: { supplier_id: string; items: typeof items }) =>
      apiPost<PurchaseOrder>('/api/v1/purchase-orders', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pos'] });
      navigate('/procurement/pos');
    },
  });

  return (
    <div className="max-w-2xl space-y-6">
      <button onClick={() => navigate('/procurement/pos')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Purchase Orders
      </button>

      <h1 className="text-2xl font-bold text-gray-900">Create Purchase Order</h1>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Supplier</label>
          <select
            value={selectedSupplier}
            onChange={(e) => setSelectedSupplier(e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
          >
            <option value="">Select a supplier…</option>
            {suppliers?.filter(s => s.status === 'APPROVED').map((s) => (
              <option key={s.id} value={s.id}>{s.supplier_name}</option>
            ))}
          </select>
        </div>

        <div className="space-y-3">
          <label className="block text-sm font-medium text-gray-700">Line Items</label>
          {items.map((item, i) => (
            <div key={i} className="flex gap-3">
              <input
                placeholder="Item description"
                value={item.description}
                onChange={(e) => {
                  const next = [...items]; next[i] = { ...next[i], description: e.target.value }; setItems(next);
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
              />
              <input type="number" placeholder="Qty" value={item.quantity}
                onChange={(e) => { const next = [...items]; next[i] = { ...next[i], quantity: Number(e.target.value) }; setItems(next); }}
                className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
              <input type="number" placeholder="Price" value={item.price}
                onChange={(e) => { const next = [...items]; next[i] = { ...next[i], price: Number(e.target.value) }; setItems(next); }}
                className="w-28 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none" />
            </div>
          ))}
          <button onClick={() => setItems([...items, { description: '', quantity: 1, price: 0 }])}
            className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center gap-1">
            <Plus className="h-4 w-4" /> Add item
          </button>
        </div>

        <div className="flex gap-3 justify-end pt-2 border-t border-gray-100">
          <button onClick={() => navigate('/procurement/pos')}
            className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">Cancel</button>
          <button
            onClick={() => createMutation.mutate({ supplier_id: selectedSupplier, items })}
            disabled={!selectedSupplier || items.length === 0 || createMutation.isPending}
            className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creating…' : 'Create PO'}
          </button>
        </div>
      </div>
    </div>
  );
}
