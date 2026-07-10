import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { apiGet, apiPost } from '../../api/client';
import type { ConnectionResponse } from '../../api/types';
import { Plug, Plus, Wifi, WifiOff, RefreshCw, Search } from 'lucide-react';
import { useState } from 'react';

const connectorIcons: Record<string, string> = {
  sap: 'SAP',
  coupa: 'Coupa',
  oracle: 'Oracle',
  netsuite: 'NS',
  generic_rest: 'API',
};

const connectorColors: Record<string, string> = {
  sap: 'bg-blue-100 text-blue-600',
  coupa: 'bg-green-100 text-green-600',
  oracle: 'bg-red-100 text-red-600',
  netsuite: 'bg-purple-100 text-purple-600',
  generic_rest: 'bg-gray-100 text-gray-600',
};

export function IntegrationListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');

  const { data: connections } = useQuery({
    queryKey: ['integrations'],
    queryFn: () => apiGet<ConnectionResponse[]>('/api/v1/integrations/connections'),
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => apiPost(`/api/v1/integrations/connections/${id}/test`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['integrations'] }),
  });

  const filtered = connections?.filter((c) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return c.connection_name.toLowerCase().includes(q) ||
           c.connector_type.toLowerCase().includes(q);
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Plug className="h-6 w-6 text-indigo-500" /> Integrations
          </h1>
          <p className="text-gray-500 mt-1">{connections?.length ?? 0} connections configured</p>
        </div>
        <button className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition">
          <Plus className="h-4 w-4" /> New Connection
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search connections…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
        />
      </div>

      {/* Connection list */}
      {filtered && filtered.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((conn) => (
            <div
              key={conn.id}
              onClick={() => navigate(`/integrations/connections/${conn.id}`)}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:shadow-md cursor-pointer transition group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-lg ${connectorColors[conn.connector_type] ?? 'bg-gray-100 text-gray-600'}`}>
                  <span className="text-xs font-bold">{connectorIcons[conn.connector_type] ?? conn.connector_type.toUpperCase()}</span>
                </div>
                {conn.is_connected ? (
                  <span className="inline-flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                    <Wifi className="h-3 w-3" /> Connected
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs text-gray-500 bg-gray-50 px-2 py-0.5 rounded-full">
                    <WifiOff className="h-3 w-3" /> Disconnected
                  </span>
                )}
              </div>
              <h3 className="font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">
                {conn.connection_name}
              </h3>
              <p className="text-xs text-gray-400 capitalize mt-0.5">{conn.connector_type} connector</p>
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
                <span className="text-xs text-gray-400">
                  {conn.last_sync_at ? `Last sync: ${new Date(conn.last_sync_at).toLocaleDateString()}` : 'Not synced'}
                </span>
                <button
                  onClick={(e) => { e.stopPropagation(); testMutation.mutate(conn.id); }}
                  className="text-xs text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1"
                >
                  <RefreshCw className="h-3 w-3" /> Test
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
          <Plug className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-gray-900">No connections yet</h3>
          <p className="text-gray-500 mt-1">Connect to SAP, Coupa, Oracle, or other systems.</p>
        </div>
      )}
    </div>
  );
}
