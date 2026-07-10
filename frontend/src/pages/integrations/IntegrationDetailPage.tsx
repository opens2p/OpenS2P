import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import type { ConnectionResponse, RunResponse, SyncResponse } from '../../api/types';
import {
  ArrowLeft, Wifi, WifiOff, RefreshCw, Activity,
  Clock, Trash2, CheckCircle, XCircle,
} from 'lucide-react';
import { useState } from 'react';

export function IntegrationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [syncType, setSyncType] = useState('purchase_order');

  const { data: connection, isLoading } = useQuery({
    queryKey: ['integration', id],
    queryFn: () => apiGet<ConnectionResponse>(`/api/v1/integrations/connections/${id}`),
    enabled: !!id,
  });

  const { data: runs } = useQuery({
    queryKey: ['integration-runs', id],
    queryFn: () => apiGet<RunResponse[]>(`/api/v1/integrations/runs?connection_id=${id}`),
    enabled: !!id,
  });

  const testMutation = useMutation({
    mutationFn: () => apiPost(`/api/v1/integrations/connections/${id}/test`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integration', id] }),
  });

  const syncMutation = useMutation({
    mutationFn: (objectType: string) =>
      apiPost<SyncResponse>(`/api/v1/integrations/connections/${id}/sync`, { object_type: objectType }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integration', id] });
      queryClient.invalidateQueries({ queryKey: ['integration-runs', id] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => apiPost(`/api/v1/integrations/connections/${id}/delete`),
    onSuccess: () => navigate('/integrations'),
  });

  if (isLoading) return <div className="text-gray-500 p-8">Loading…</div>;
  if (!connection) return <div className="text-red-500 p-8">Connection not found</div>;

  return (
    <div className="max-w-3xl space-y-6">
      <button onClick={() => navigate('/integrations')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Integrations
      </button>

      {/* Connection info card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">{connection.connection_name}</h1>
              {connection.is_connected ? (
                <span className="inline-flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                  <Wifi className="h-3 w-3" /> Connected
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-xs text-gray-500 bg-gray-50 px-2 py-0.5 rounded-full">
                  <WifiOff className="h-3 w-3" /> Disconnected
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500 mt-1 capitalize">{connection.connector_type} connector</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6 mt-6 text-sm">
          <div>
            <span className="text-gray-500">Endpoint</span>
            <p className="font-medium text-gray-900 mt-0.5">{connection.endpoint_url ?? 'Not configured'}</p>
          </div>
          <div>
            <span className="text-gray-500">Auth Type</span>
            <p className="font-medium text-gray-900 mt-0.5 capitalize">{connection.auth_type ?? '—'}</p>
          </div>
          <div>
            <span className="text-gray-500">Last Test</span>
            <p className="font-medium text-gray-900 mt-0.5">
              {connection.last_test_at ? new Date(connection.last_test_at).toLocaleString() : 'Never'}
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3 mt-6 pt-4 border-t border-gray-100 flex-wrap">
          <button
            onClick={() => testMutation.mutate()}
            disabled={testMutation.isPending}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${testMutation.isPending ? 'animate-spin' : ''}`} /> Test Connection
          </button>
          <button
            onClick={() => deleteMutation.mutate()}
            className="flex items-center gap-2 text-red-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-50"
          >
            <Trash2 className="h-4 w-4" /> Remove
          </button>
        </div>
      </div>

      {/* Sync panel */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Activity className="h-5 w-5 text-indigo-500" /> Sync Data
        </h2>
        <div className="flex items-center gap-3">
          <select
            value={syncType}
            onChange={(e) => setSyncType(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-indigo-500 outline-none"
          >
            <option value="supplier">Suppliers</option>
            <option value="purchase_order">Purchase Orders</option>
            <option value="invoice">Invoices</option>
            <option value="contract">Contracts</option>
            <option value="payment">Payments</option>
          </select>
          <button
            onClick={() => syncMutation.mutate(syncType)}
            disabled={syncMutation.isPending}
            className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            {syncMutation.isPending ? 'Syncing…' : 'Start Sync'}
          </button>
        </div>
      </div>

      {/* Sync History */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Clock className="h-5 w-5 text-gray-400" /> Sync History
          </h2>
        </div>
        {runs && runs.length > 0 ? (
          <div className="divide-y divide-gray-100">
            {runs.map((run) => (
              <div key={run.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                <div className="flex items-center gap-3">
                  {run.status === 'completed' || run.status === 'success' ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : run.status === 'failed' ? (
                    <XCircle className="h-5 w-5 text-red-500" />
                  ) : (
                    <RefreshCw className="h-5 w-5 text-amber-500 animate-spin" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-gray-900 capitalize">{run.direction}</p>
                    <p className="text-xs text-gray-400">
                      {run.started_at ? new Date(run.started_at).toLocaleString() : '—'}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    run.status === 'completed' || run.status === 'success'
                      ? 'bg-green-100 text-green-700'
                      : run.status === 'failed' ? 'bg-red-100 text-red-600' : 'bg-amber-100 text-amber-700'
                  }`}>
                    {run.status}
                  </span>
                  {run.records_processed != null && (
                    <p className="text-xs text-gray-400 mt-1">{run.records_processed} records</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400 p-6">No sync history yet.</p>
        )}
      </div>
    </div>
  );
}
