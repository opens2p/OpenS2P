import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../../api/client';
import type { SpendCategory, SpendTrend } from '../../api/types';
import { DollarSign, TrendingUp, BarChart3 } from 'lucide-react';

const barColors = [
  'bg-indigo-500', 'bg-blue-500', 'bg-emerald-500', 'bg-amber-500',
  'bg-violet-500', 'bg-rose-500', 'bg-cyan-500', 'bg-orange-500',
];

export default function SpendAnalytics() {
  const { data: categories } = useQuery({
    queryKey: ['spend-categories'],
    queryFn: () => apiGet<SpendCategory[]>('/api/v1/analytics/spend/categories'),
  });

  const { data: trend } = useQuery({
    queryKey: ['spend-trend'],
    queryFn: () => apiGet<SpendTrend[]>('/api/v1/analytics/spend'),
  });

  const totalSpend = categories?.reduce((sum, c) => sum + c.total, 0) ?? 0;
  const monthlyAvg = trend && trend.length > 0
    ? trend.reduce((sum, t) => sum + t.total, 0) / trend.length
    : 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <DollarSign className="h-6 w-6 text-emerald-500" /> Spend Analytics
        </h1>
        <p className="text-gray-500 mt-1">Detailed breakdown of procurement spend</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Total Spend</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">${totalSpend.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Categories</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{categories?.length ?? 0}</p>
        </div>
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Monthly Average</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">${Math.round(monthlyAvg).toLocaleString()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Spend by Category */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-indigo-500" /> Spend by Category
          </h2>
          {categories && categories.length > 0 ? (
            <div className="space-y-4">
              {categories.map((cat, idx) => {
                const pct = totalSpend > 0 ? ((cat.total / totalSpend) * 100).toFixed(1) : 0;
                return (
                  <div key={cat.category} className="space-y-1.5">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-700 font-medium capitalize">{cat.category}</span>
                      <span className="text-gray-500">${Number(cat.total).toLocaleString()}</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                      <div
                        className={`h-2.5 rounded-full ${barColors[idx % barColors.length]} transition-all duration-500`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-400 text-right">{pct}%</p>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-400 py-8 text-center">No category data available.</p>
          )}
        </div>

        {/* Monthly Spend Trend */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-emerald-500" /> Monthly Spend Trend
          </h2>
          {trend && trend.length > 0 ? (
            <div className="space-y-2">
              {trend.map((item) => {
                const max = Math.max(...trend.map((t) => t.total), 1);
                const height = (item.total / max) * 100;
                return (
                  <div key={item.month} className="flex items-center gap-3">
                    <span className="text-sm text-gray-500 w-20 text-right">{item.month}</span>
                    <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                      <div
                        className="h-5 rounded-full bg-emerald-400 flex items-center justify-end pr-2 transition-all"
                        style={{ width: `${Math.max(height, 2)}%` }}
                      >
                        {height > 15 && (
                          <span className="text-xs text-white font-medium">
                            ${(item.total / 1000).toFixed(0)}k
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-400 py-8 text-center">No trend data available.</p>
          )}
        </div>
      </div>
    </div>
  );
}
