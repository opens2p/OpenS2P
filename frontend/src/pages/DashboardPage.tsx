import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../api/client';
import { useNavigate } from 'react-router-dom';
import {
  Building2, FileText, ShoppingCart, Receipt, AlertTriangle,
  DollarSign, TrendingUp, BarChart3, Plus, FileEdit, Send,
} from 'lucide-react';
import type { Supplier, PurchaseRequisition, PurchaseOrder, Invoice, DashboardData } from '../api/types';

function StatCard({ label, value, icon: Icon, color, path, subtitle }: {
  label: string; value: string | number; icon: React.ElementType;
  color: string; path: string; subtitle?: string;
}) {
  const navigate = useNavigate();
  return (
    <button
      onClick={() => navigate(path)}
      className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 hover:shadow-md hover:border-indigo-200 transition-all text-left group"
    >
      <div className="flex items-start justify-between">
        <div className={`${color} w-10 h-10 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform`}>
          <Icon className="h-5 w-5 text-white" />
        </div>
      </div>
      <p className="text-2xl font-bold text-gray-900 mt-3">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
      {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
    </button>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();

  const { data: dashboard } = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: () => apiGet<DashboardData>('/api/v1/analytics/dashboard'),
  });

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

  const spend = dashboard?.spend ?? {};
  const supplierData = dashboard?.suppliers ?? {};
  const contractData = dashboard?.contracts ?? {};
  const cycleData = dashboard?.cycle_times ?? {};

  const activeSuppliers = supplierData.active_count ?? suppliers?.filter(s => s.status === 'APPROVED').length ?? 0;
  const totalSpend = spend.total ?? 0;
  const pendingApprovals = prs?.filter(p => p.status === 'SUBMITTED').length ?? 0;
  const invoiceMatchRate = cycleData.invoice_match_rate != null
    ? (typeof cycleData.invoice_match_rate === 'object'
        ? (cycleData.invoice_match_rate as Record<string, number>)?.match_rate ?? 0
        : cycleData.invoice_match_rate as number)
    : invoices && invoices.length > 0
      ? Math.round((invoices.filter(i => i.match_status === 'MATCHED').length / invoices.length) * 100)
      : 0;

  const activeContracts = contractData.active ?? 0;

  const stats = [
    { label: 'Total Spend', value: `$${Number(totalSpend).toLocaleString()}`, icon: DollarSign, color: 'bg-indigo-500', path: '/analytics/spend', subtitle: 'YTD' },
    { label: 'Active Suppliers', value: String(activeSuppliers ?? 0), icon: Building2, color: 'bg-blue-500', path: '/suppliers' },
    { label: 'Active Contracts', value: String(activeContracts ?? 0), icon: FileText, color: 'bg-violet-500', path: '/contracts' },
    { label: 'Pending Approvals', value: String(pendingApprovals ?? 0), icon: AlertTriangle, color: 'bg-amber-500', path: '/workflows' },
    { label: 'Invoice Match Rate', value: `${invoiceMatchRate}%`, icon: TrendingUp, color: 'bg-emerald-500', path: '/invoices' },
  ];

  const exceptionCount = invoices?.filter((i) => i.match_status === 'EXCEPTION').length ?? 0;
  const submittedCount = prs?.filter((p) => p.status === 'SUBMITTED').length ?? 0;

  return (
    <div className="space-y-8">
      {/* Welcome section */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold text-gray-900">Executive Dashboard</h1>
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-700 uppercase tracking-wider">DEMO</span>
          </div>
          <p className="text-gray-500">Real-time overview of your Source-to-Pay operations</p>
        </div>
        <div className="hidden sm:flex items-center gap-2">
          <button
            onClick={() => navigate('/procurement/prs')}
            className="flex items-center gap-1.5 bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-indigo-700 transition"
          >
            <Plus className="h-4 w-4" /> New Requisition
          </button>
          <button
            onClick={() => navigate('/procurement/create-po')}
            className="flex items-center gap-1.5 bg-white text-gray-700 px-3 py-1.5 rounded-lg text-sm font-medium border border-gray-300 hover:bg-gray-50 transition"
          >
            <Plus className="h-4 w-4" /> New PO
          </button>
        </div>
      </div>

      {/* Quick action cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <button onClick={() => navigate('/suppliers')} className="flex items-center gap-3 bg-white rounded-lg px-4 py-3 border border-gray-200 hover:border-indigo-200 hover:shadow-sm transition-all text-left">
          <div className="p-2 bg-blue-50 rounded-lg"><Building2 className="h-4 w-4 text-blue-600" /></div>
          <span className="text-sm font-medium text-gray-700">Suppliers</span>
        </button>
        <button onClick={() => navigate('/procurement/prs')} className="flex items-center gap-3 bg-white rounded-lg px-4 py-3 border border-gray-200 hover:border-indigo-200 hover:shadow-sm transition-all text-left">
          <div className="p-2 bg-indigo-50 rounded-lg"><FileEdit className="h-4 w-4 text-indigo-600" /></div>
          <span className="text-sm font-medium text-gray-700">Requisitions</span>
        </button>
        <button onClick={() => navigate('/procurement/pos')} className="flex items-center gap-3 bg-white rounded-lg px-4 py-3 border border-gray-200 hover:border-indigo-200 hover:shadow-sm transition-all text-left">
          <div className="p-2 bg-emerald-50 rounded-lg"><Send className="h-4 w-4 text-emerald-600" /></div>
          <span className="text-sm font-medium text-gray-700">Purchase Orders</span>
        </button>
        <button onClick={() => navigate('/invoices')} className="flex items-center gap-3 bg-white rounded-lg px-4 py-3 border border-gray-200 hover:border-indigo-200 hover:shadow-sm transition-all text-left">
          <div className="p-2 bg-amber-50 rounded-lg"><Receipt className="h-4 w-4 text-amber-600" /></div>
          <span className="text-sm font-medium text-gray-700">Invoices</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {stats.map((s) => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Spend by Category */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-indigo-500" /> Spend by Category
            </h2>
            <button
              onClick={() => navigate('/analytics/spend')}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              View all
            </button>
          </div>
          <SpendByCategoryChart />
        </div>

        {/* Spend Trend */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-emerald-500" /> Monthly Spend Trend
            </h2>
          </div>
          <SpendTrendChart />
        </div>
      </div>

      {/* My Work widget */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <FileText className="h-5 w-5 text-indigo-500" /> My Work
          </h2>
          <button
            onClick={() => navigate('/workflows')}
            className="text-sm text-indigo-600 hover:text-indigo-800 font-medium"
          >
            View all
          </button>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div
            onClick={() => navigate('/workflows')}
            className="p-4 rounded-lg bg-amber-50 border border-amber-200 hover:bg-amber-100 cursor-pointer transition"
          >
            <p className="text-2xl font-bold text-amber-600">{submittedCount}</p>
            <p className="text-xs text-amber-700 font-medium mt-1">Approvals Pending</p>
          </div>
          <div
            onClick={() => navigate('/procurement/prs')}
            className="p-4 rounded-lg bg-blue-50 border border-blue-200 hover:bg-blue-100 cursor-pointer transition"
          >
            <p className="text-2xl font-bold text-blue-600">{prs?.filter(p => p.status === 'DRAFT' || p.status === 'SUBMITTED').length ?? 0}</p>
            <p className="text-xs text-blue-700 font-medium mt-1">PRs Awaiting Action</p>
          </div>
          <div
            onClick={() => navigate('/contracts')}
            className="p-4 rounded-lg bg-violet-50 border border-violet-200 hover:bg-violet-100 cursor-pointer transition"
          >
            <p className="text-2xl font-bold text-violet-600">{0}</p>
            <p className="text-xs text-violet-700 font-medium mt-1">Contracts Expiring</p>
          </div>
          <div
            onClick={() => navigate('/invoices')}
            className="p-4 rounded-lg bg-rose-50 border border-rose-200 hover:bg-rose-100 cursor-pointer transition"
          >
            <p className="text-2xl font-bold text-rose-600">{exceptionCount}</p>
            <p className="text-xs text-rose-700 font-medium mt-1">Invoice Exceptions</p>
          </div>
        </div>
      </div>

      {/* Alerts section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div
          onClick={() => navigate('/invoices')}
          className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 hover:shadow-md cursor-pointer transition"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-red-50 rounded-lg">
              <Receipt className="h-5 w-5 text-red-500" />
            </div>
            <span className="text-lg font-bold text-gray-900">{exceptionCount}</span>
          </div>
          <p className="text-sm text-gray-500">Invoice exceptions need review</p>
        </div>
        <div
          onClick={() => navigate('/workflows')}
          className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 hover:shadow-md cursor-pointer transition"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-amber-50 rounded-lg">
              <FileText className="h-5 w-5 text-amber-500" />
            </div>
            <span className="text-lg font-bold text-gray-900">{submittedCount}</span>
          </div>
          <p className="text-sm text-gray-500">Requisitions awaiting approval</p>
        </div>
        <div
          onClick={() => navigate('/procurement/pos')}
          className="bg-white rounded-xl p-5 shadow-sm border border-gray-200 hover:shadow-md cursor-pointer transition"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-blue-50 rounded-lg">
              <ShoppingCart className="h-5 w-5 text-blue-500" />
            </div>
            <span className="text-lg font-bold text-gray-900">{pos?.filter(p => p.status === 'SENT').length ?? 0}</span>
          </div>
          <p className="text-sm text-gray-500">Confirmed POs ready for receiving</p>
        </div>
      </div>
    </div>
  );
}

/* ─── Inline CSS Charts (no recharts dependency needed) ─── */

function SpendByCategoryChart() {
  const dashboard = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: () => apiGet<DashboardData>('/api/v1/analytics/dashboard'),
  });
  const categories = dashboard.data?.spend?.by_category as Array<{ category: string; total: number }> | undefined;
  const catData = Array.isArray(categories) ? categories : [];

  if (catData.length === 0) {
    return <p className="text-sm text-gray-400 py-8 text-center">No spend data available yet.</p>;
  }

  const colors = ['bg-indigo-500', 'bg-blue-500', 'bg-emerald-500', 'bg-amber-500', 'bg-violet-500', 'bg-rose-500', 'bg-cyan-500'];
  const total = catData.reduce((sum, c) => sum + c.total, 0);

  return (
    <div className="space-y-3">
      {catData.map((cat, idx) => {
        const pct = total > 0 ? ((cat.total / total) * 100).toFixed(1) : 0;
        return (
          <div key={cat.category} className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-gray-700 font-medium capitalize">{cat.category}</span>
              <span className="text-gray-500">${Number(cat.total).toLocaleString()} ({pct}%)</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
              <div
                className={`h-2 rounded-full ${colors[idx % colors.length]} transition-all duration-500`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SpendTrendChart() {
  const dashboard = useQuery({
    queryKey: ['dashboard-analytics'],
    queryFn: () => apiGet<DashboardData>('/api/v1/analytics/dashboard'),
  });
  const rawTrend = dashboard.data?.spend?.trend;
  const trend = Array.isArray(rawTrend) ? rawTrend as Array<{ month: string; total: number }> : [];

  if (trend.length === 0) {
    return <p className="text-sm text-gray-400 py-8 text-center">No trend data available yet.</p>;
  }

  const values = trend.map(t => t.total);
  const max = Math.max(...values, 1);

  return (
    <div className="flex items-end gap-2 h-40 pt-2">
      {trend.map((item) => {
        const height = (item.total / max) * 100;
        return (
          <div key={item.month} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
            <span className="text-xs text-gray-500">${(item.total / 1000).toFixed(0)}k</span>
            <div
              className="w-full bg-emerald-400 rounded-t-md hover:bg-emerald-500 transition-all min-h-[4px]"
              style={{ height: `${height}%` }}
            />
            <span className="text-xs text-gray-400 mt-1 truncate w-full text-center">
              {item.month?.slice(0, 3) ?? item.month}
            </span>
          </div>
        );
      })}
    </div>
  );
}
