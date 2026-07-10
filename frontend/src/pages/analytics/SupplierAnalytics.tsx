import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../../api/client';
import type { SupplierScorecard } from '../../api/types';
import { Building2, TrendingUp, DollarSign, ShieldCheck } from 'lucide-react';

export default function SupplierAnalytics() {
  const { data: scorecard } = useQuery({
    queryKey: ['supplier-scorecard'],
    queryFn: () => apiGet<Record<string, unknown>>('/api/v1/analytics/suppliers/scorecard'),
  });

  const { data: suppliers } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => apiGet<any[]>('/api/v1/suppliers'),
  });

  // Try to parse scorecard data - it may come in different formats
  const scores: SupplierScorecard[] = (scorecard as any)?.suppliers
    ?? (scorecard as any)?.scorecards
    ?? (scorecard as any)?.data
    ?? [];

  const topSuppliers = Array.isArray(scores) ? scores.slice(0, 10) : [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Building2 className="h-6 w-6 text-blue-500" /> Supplier Analytics
        </h1>
        <p className="text-gray-500 mt-1">Supplier performance scorecards and metrics</p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Total Suppliers</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{suppliers?.length ?? 0}</p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Approved</p>
          <p className="text-3xl font-bold text-green-600 mt-1">
            {suppliers?.filter((s) => s.status === 'APPROVED').length ?? 0}
          </p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">High Risk</p>
          <p className="text-3xl font-bold text-red-600 mt-1">
            {suppliers?.filter((s) => (s.risk_score ?? 0) >= 7).length ?? 0}
          </p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Draft / Pending</p>
          <p className="text-3xl font-bold text-amber-600 mt-1">
            {suppliers?.filter((s) => s.status === 'DRAFT' || s.status === 'INVITED').length ?? 0}
          </p>
        </div>
      </div>

      {/* Supplier Scorecards */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-indigo-500" /> Supplier Performance
          </h2>
        </div>
        {topSuppliers.length > 0 ? (
          <div className="divide-y divide-gray-100">
            {topSuppliers.map((s, idx) => (
              <div key={s.supplier_id ?? idx} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-indigo-50 flex items-center justify-center text-sm font-medium text-indigo-600">
                    {s.supplier_name?.charAt(0)?.toUpperCase() ?? '?'}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{s.supplier_name ?? 'Unknown'}</p>
                    <p className="text-xs text-gray-400">
                      {s.total_spend != null ? `$${Number(s.total_spend).toLocaleString()} spend` : 'No spend data'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  {s.on_time_rate != null && (
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">{s.on_time_rate}%</p>
                      <p className="text-xs text-gray-400">On-time</p>
                    </div>
                  )}
                  {s.quality_score != null && (
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">{s.quality_score}/10</p>
                      <p className="text-xs text-gray-400">Quality</p>
                    </div>
                  )}
                  {s.risk_score != null && (
                    <div className="text-right">
                      <p className={`text-sm font-medium ${s.risk_score >= 7 ? 'text-red-600' : s.risk_score >= 4 ? 'text-amber-600' : 'text-green-600'}`}>
                        {s.risk_score}/10
                      </p>
                      <p className="text-xs text-gray-400">Risk</p>
                    </div>
                  )}
                  <div className="flex items-center gap-1 text-xs text-gray-400">
                    <DollarSign className="h-3 w-3" />
                    {s.invoice_count ?? 0} invoices
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6">
            <p className="text-sm text-gray-400">No supplier scorecard data available yet. Process invoices and orders to generate performance metrics.</p>
          </div>
        )}
      </div>

      {/* Supplier Risk Distribution */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-amber-500" /> Supplier Risk Distribution
        </h2>
        {suppliers && suppliers.length > 0 ? (
          <div className="space-y-3">
            {['HIGH', 'MEDIUM', 'LOW'].map((level) => {
              const count = level === 'HIGH'
                ? suppliers.filter((s) => (s.risk_score ?? 0) >= 7).length
                : level === 'MEDIUM'
                ? suppliers.filter((s) => (s.risk_score ?? 0) >= 4 && (s.risk_score ?? 0) < 7).length
                : suppliers.filter((s) => (s.risk_score ?? 0) < 4 || s.risk_score == null).length;
              const total = suppliers.length;
              const pct = total > 0 ? ((count / total) * 100).toFixed(0) : 0;
              const color = level === 'HIGH' ? 'bg-red-500' : level === 'MEDIUM' ? 'bg-amber-500' : 'bg-green-500';
              return (
                <div key={level} className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-600 w-16">{level}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                    <div className={`h-4 rounded-full ${color}`} style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-sm text-gray-500 w-24 text-right">{count} suppliers ({pct}%)</span>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No supplier data available.</p>
        )}
      </div>
    </div>
  );
}
