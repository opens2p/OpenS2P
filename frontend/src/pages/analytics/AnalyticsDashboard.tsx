import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiGet } from '../../api/client';
import type { DashboardData } from '../../api/types';
import {
  BarChart3, TrendingUp, DollarSign, Building2, FileText,
  Clock, ArrowRight,
} from 'lucide-react';

export default function AnalyticsDashboard() {
  const navigate = useNavigate();

  const { data: dashboard } = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: () => apiGet<DashboardData>('/api/v1/analytics/dashboard'),
  });

  const { data: contractData } = useQuery({
    queryKey: ['analytics-contracts'],
    queryFn: () => apiGet<Record<string, unknown>>('/api/v1/analytics/contracts'),
  });

  const { data: workflowData } = useQuery({
    queryKey: ['analytics-workflows'],
    queryFn: () => apiGet<Record<string, unknown>>('/api/v1/analytics/workflows'),
  });

  const spend = dashboard?.spend ?? {};
  const supplierData = dashboard?.suppliers ?? {};

  const cards = [
    {
      label: 'Total Spend',
      value: `$${Number(spend.total ?? 0).toLocaleString()}`,
      icon: DollarSign,
      color: 'bg-indigo-500',
      path: '/analytics/spend',
    },
    {
      label: 'Active Suppliers',
      value: String(supplierData.active_suppliers ?? 0),
      icon: Building2,
      color: 'bg-blue-500',
      path: '/analytics/suppliers',
    },
    {
      label: 'Active Contracts',
      value: String(contractData ? (contractData as any).active ?? 0 : 0),
      icon: FileText,
      color: 'bg-violet-500',
      path: '/contracts',
    },
    {
      label: 'Avg Cycle Time',
      value: workflowData ? `${(workflowData as any).cycle_times?.avg_days ?? '—'}d` : '—',
      icon: Clock,
      color: 'bg-amber-500',
      path: '/workflows',
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-indigo-500" /> Analytics
        </h1>
        <p className="text-gray-500 mt-1">Performance metrics and operational insights</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => (
          <button
            key={card.label}
            onClick={() => navigate(card.path)}
            className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 hover:shadow-md transition text-left group"
          >
            <div className={`${card.color} w-10 h-10 rounded-lg flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}>
              <card.icon className="h-5 w-5 text-white" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{card.value}</p>
            <p className="text-sm text-gray-500">{card.label}</p>
          </button>
        ))}
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div
          onClick={() => navigate('/analytics/spend')}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md cursor-pointer transition group"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Spend Analytics</h3>
            <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-indigo-500 transition" />
          </div>
          <p className="text-sm text-gray-500">Analyze spend by category, department, and time period. Identify cost-saving opportunities.</p>
          <div className="mt-4 flex items-center gap-2 text-sm text-indigo-600 font-medium">
            <TrendingUp className="h-4 w-4" /> View spend breakdown
          </div>
        </div>

        <div
          onClick={() => navigate('/analytics/suppliers')}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md cursor-pointer transition group"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Supplier Analytics</h3>
            <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-indigo-500 transition" />
          </div>
          <p className="text-sm text-gray-500">Supplier scorecards, performance metrics, risk assessment, and spend concentration.</p>
          <div className="mt-4 flex items-center gap-2 text-sm text-indigo-600 font-medium">
            <Building2 className="h-4 w-4" /> View supplier metrics
          </div>
        </div>

        <div
          onClick={() => navigate('/workflows')}
          className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md cursor-pointer transition group"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Workflow Analytics</h3>
            <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-indigo-500 transition" />
          </div>
          <p className="text-sm text-gray-500">Approval cycle times, bottlenecks, invoice match rates, and process efficiency.</p>
          <div className="mt-4 flex items-center gap-2 text-sm text-indigo-600 font-medium">
            <Clock className="h-4 w-4" /> View cycle times
          </div>
        </div>
      </div>
    </div>
  );
}
