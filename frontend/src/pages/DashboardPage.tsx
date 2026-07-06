import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../api/client';
import { useNavigate } from 'react-router-dom';
import { Building2, FileText, ShoppingCart, Receipt, AlertTriangle } from 'lucide-react';
import type { Supplier, PurchaseRequisition, PurchaseOrder, Invoice } from '../api/types';

export default function DashboardPage() {
  const navigate = useNavigate();

  const { data: suppliers } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => apiGet<Supplier[]>('/api/v1/suppliers'),
  });

  const { data: prs } = useQuery({
    queryKey: ['prs'],
    queryFn: () => apiGet<PurchaseRequisition[]>('/api/v1/purchase-requisitions'),
  });

  const { data: pos } = useQuery({
    queryKey: ['pos'],
    queryFn: () => apiGet<PurchaseOrder[]>('/api/v1/purchase-orders'),
  });

  const { data: invoices } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => apiGet<Invoice[]>('/api/v1/invoices'),
  });

  const stats = [
    { label: 'Suppliers', value: suppliers?.length ?? 0, icon: Building2, color: 'bg-blue-500', path: '/suppliers' },
    { label: 'Requisitions', value: prs?.length ?? 0, icon: FileText, color: 'bg-violet-500', path: '/procurement/prs' },
    { label: 'Purchase Orders', value: pos?.length ?? 0, icon: ShoppingCart, color: 'bg-emerald-500', path: '/procurement/pos' },
    { label: 'Invoices', value: invoices?.length ?? 0, icon: Receipt, color: 'bg-amber-500', path: '/invoices' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Overview of your procurement operations</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <button
            key={s.label}
            onClick={() => navigate(s.path)}
            className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition text-left"
          >
            <div className={`${s.color} w-10 h-10 rounded-lg flex items-center justify-center mb-3`}>
              <s.icon className="h-5 w-5 text-white" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{s.value}</p>
            <p className="text-sm text-gray-500">{s.label}</p>
          </button>
        ))}
      </div>

      {/* Alerts section */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-500" />
          Attention Required
        </h2>
        <p className="text-gray-500 text-sm">
          {invoices?.filter((i) => i.match_status === 'EXCEPTION').length ?? 0} invoices with matching exceptions.
          {' '}
          {prs?.filter((p) => p.status === 'SUBMITTED').length ?? 0} requisitions pending approval.
        </p>
      </div>
    </div>
  );
}
