import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../../api/client';
import type { SpendCategory, SpendDashboard, SpendLeakageResponse } from '../../api/types';
import {
  AlertTriangle,
  BarChart3,
  Bot,
  DollarSign,
  SearchCheck,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from 'lucide-react';

const barColors = [
  'bg-indigo-500', 'bg-blue-500', 'bg-emerald-500', 'bg-amber-500',
  'bg-violet-500', 'bg-rose-500', 'bg-cyan-500', 'bg-orange-500',
];

export default function SpendAnalytics() {
  const { data: categories } = useQuery({
    queryKey: ['spend-categories'],
    queryFn: () => apiGet<SpendCategory[]>('/api/v1/analytics/spend/categories'),
  });

  const { data: spendDashboard } = useQuery({
    queryKey: ['spend-dashboard'],
    queryFn: () => apiGet<SpendDashboard>('/api/v1/analytics/spend'),
  });

  const { data: leakage } = useQuery({
    queryKey: ['spend-leakage'],
    queryFn: () => apiGet<SpendLeakageResponse>('/api/v1/analytics/spend/leakage'),
  });

  const trend = spendDashboard?.trend ?? [];
  const totalSpend = categories?.reduce((sum, c) => sum + c.total, 0) ?? 0;
  const monthlyAvg = trend && trend.length > 0
    ? trend.reduce((sum, t) => sum + t.total, 0) / trend.length
    : 0;
  const leakageSummary = leakage?.summary;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <DollarSign className="h-6 w-6 text-emerald-500" /> Spend Analytics
        </h1>
        <p className="text-gray-500 mt-1">Detailed breakdown of procurement spend</p>
      </div>

      {/* AI Spend Leakage Detective */}
      <div className="bg-slate-950 rounded-xl border border-slate-800 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-white/10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">
          <div>
            <div className="flex items-center gap-2 text-cyan-300 text-sm font-medium mb-1">
              <SearchCheck className="h-4 w-4" />
              AI Spend Leakage Detective
            </div>
            <h2 className="text-xl font-bold text-white">Savings opportunities hidden in procurement activity</h2>
            <p className="text-sm text-slate-400 mt-1 max-w-3xl">
              Scans suppliers, contracts, invoices, and purchase orders for fragmented spend,
              off-contract buying, price variance, and risk exposure.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3 min-w-full sm:min-w-[420px]">
            <DetectorMetric
              label="Detected"
              value={`$${Number(leakageSummary?.total_detected_savings ?? 0).toLocaleString()}`}
            />
            <DetectorMetric
              label="Findings"
              value={String(leakageSummary?.opportunity_count ?? 0)}
            />
            <DetectorMetric
              label="Invoices"
              value={String(leakageSummary?.scan_scope.invoices ?? 0)}
            />
          </div>
        </div>

        <div className="p-6">
          {leakage?.opportunities && leakage.opportunities.length > 0 ? (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
              {leakage.opportunities.map((opp) => (
                <div key={opp.id} className="rounded-lg bg-white/[0.04] border border-white/10 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <SeverityBadge severity={opp.severity} />
                        <span className="text-[10px] uppercase tracking-wider text-slate-500">
                          {opp.leakage_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <h3 className="text-sm font-semibold text-white">{opp.title}</h3>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-[10px] uppercase tracking-wider text-slate-500">Savings</p>
                      <p className="text-lg font-bold text-emerald-300">
                        ${Number(opp.estimated_savings).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 rounded-lg bg-cyan-400/10 border border-cyan-300/20 p-3">
                    <p className="text-[10px] uppercase tracking-wider text-cyan-200 mb-1 flex items-center gap-1.5">
                      <Sparkles className="h-3.5 w-3.5" /> AI brief
                    </p>
                    <p className="text-sm text-slate-100 leading-relaxed">{opp.ai_brief}</p>
                  </div>

                  <div className="mt-4 space-y-2">
                    {opp.evidence.map((item) => (
                      <p key={item} className="text-xs text-slate-300 flex gap-2">
                        <ShieldCheck className="h-3.5 w-3.5 text-emerald-300 shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </p>
                    ))}
                  </div>

                  <div className="mt-4 border-t border-white/10 pt-3">
                    <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">
                      Recommended action
                    </p>
                    <p className="text-sm text-slate-100">{opp.recommended_action}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg bg-white/[0.04] border border-white/10 p-8 text-center">
              <Bot className="h-8 w-8 text-cyan-300 mx-auto mb-3" />
              <p className="text-sm text-slate-300">No leakage opportunities detected yet.</p>
            </div>
          )}
        </div>
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

function DetectorMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white/[0.06] border border-white/10 px-3 py-2">
      <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className="text-lg font-bold text-white mt-0.5 truncate">{value}</p>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const normalized = severity.toUpperCase();
  const classes = normalized === 'HIGH'
    ? 'bg-rose-400/15 text-rose-200 border-rose-300/20'
    : normalized === 'MEDIUM'
      ? 'bg-amber-400/15 text-amber-200 border-amber-300/20'
      : 'bg-emerald-400/15 text-emerald-200 border-emerald-300/20';
  const Icon = normalized === 'HIGH' ? AlertTriangle : ShieldCheck;

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${classes}`}>
      <Icon className="h-3 w-3" />
      {normalized}
    </span>
  );
}
