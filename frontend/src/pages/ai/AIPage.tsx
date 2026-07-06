import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiGet } from '../../api/client';
import type { Supplier } from '../../api/types';
import { Brain, AlertTriangle, TrendingUp, Lightbulb, FileText, DollarSign } from 'lucide-react';

export default function AIPage() {
  const [selectedSupplier, setSelectedSupplier] = useState('');

  const { data: suppliers } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => apiGet<Supplier[]>('/api/v1/suppliers'),
  });

  const { data: riskData } = useQuery({
    queryKey: ['ai-supplier', selectedSupplier],
    queryFn: () => apiGet<{
      risk_score: number; risk_level: string;
      factors: string[]; recommendation: string;
    }>(`/api/v1/ai/supplier/${selectedSupplier}/analyze`),
    enabled: !!selectedSupplier,
  });

  const { data: categories } = useQuery({
    queryKey: ['ai-supplier-cat', selectedSupplier],
    queryFn: () => apiGet<Array<{ category: string; confidence: number }>>(
      `/api/v1/ai/supplier/${selectedSupplier}/recommend-category`,
    ),
    enabled: !!selectedSupplier,
  });

  const riskColor = riskData?.risk_level === 'HIGH' ? 'text-red-600' :
    riskData?.risk_level === 'MEDIUM' ? 'text-amber-600' : 'text-green-600';

  const riskBg = riskData?.risk_level === 'HIGH' ? 'bg-red-50 border-red-200' :
    riskData?.risk_level === 'MEDIUM' ? 'bg-amber-50 border-amber-200' : 'bg-green-50 border-green-200';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Brain className="h-6 w-6 text-indigo-500" /> AI Intelligence
        </h1>
        <p className="text-gray-500 mt-1">AI-powered insights for suppliers, contracts, and invoices</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Supplier Risk Panel */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-indigo-500" /> Supplier Risk Analysis
          </h2>
          <select
            value={selectedSupplier}
            onChange={(e) => setSelectedSupplier(e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
          >
            <option value="">Select a supplier…</option>
            {suppliers?.map((s) => (
              <option key={s.id} value={s.id}>{s.supplier_name}</option>
            ))}
          </select>

          {riskData && (
            <div className={`rounded-lg border p-4 space-y-3 ${riskBg}`}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Risk Score</span>
                <span className={`text-2xl font-bold ${riskColor}`}>{riskData.risk_score}</span>
              </div>
              <div className="flex items-center gap-2">
                <AlertTriangle className={`h-4 w-4 ${riskColor}`} />
                <span className={`text-sm font-medium ${riskColor}`}>{riskData.risk_level}</span>
              </div>
              {riskData.factors.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Factors:</p>
                  <ul className="text-xs text-gray-600 space-y-0.5 list-disc list-inside">
                    {riskData.factors.map((f, i) => <li key={i}>{f}</li>)}
                  </ul>
                </div>
              )}
              <div className="flex items-start gap-2 pt-2 border-t border-gray-200">
                <Lightbulb className="h-4 w-4 text-amber-500 mt-0.5" />
                <p className="text-sm text-gray-700">{riskData.recommendation}</p>
              </div>
            </div>
          )}

          {categories && categories.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Recommended Categories</p>
              <div className="space-y-1">
                {categories.map((c, i) => (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">{c.category}</span>
                    <span className="text-gray-400 text-xs">{Math.round(c.confidence * 100)}% match</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Contract Review Panel */}
        <ContractReviewPanel />
      </div>

      {/* Invoice Analysis */}
      <InvoiceAnalysisPanel />
    </div>
  );
}

function ContractReviewPanel() {
  const [contractId, setContractId] = useState('');

  const { data: contracts } = useQuery({
    queryKey: ['contracts'],
    queryFn: () => apiGet<Array<{ id: string; contract_number?: string }>>('/api/v1/contracts'),
  });

  const { data: review } = useQuery({
    queryKey: ['ai-contract', contractId],
    queryFn: () => apiGet<{ findings: Array<{ severity: string; category: string; description: string }>; finding_count: number; high_risk_count: number }>(
      `/api/v1/ai/contract/${contractId}/review`,
    ),
    enabled: !!contractId,
  });

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
      <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <FileText className="h-5 w-5 text-indigo-500" /> Contract Review
      </h2>
      <select value={contractId} onChange={(e) => setContractId(e.target.value)}
        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-white">
        <option value="">Select a contract…</option>
        {contracts?.map((c) => (
          <option key={c.id} value={c.id}>{c.contract_number ?? c.id.slice(0, 8)}</option>
        ))}
      </select>

      {review && (
        <div className="space-y-3">
          <div className="flex gap-4 text-sm">
            <span className="text-gray-500">{review.finding_count} findings</span>
            {review.high_risk_count > 0 && (
              <span className="text-red-500 font-medium">{review.high_risk_count} high risk</span>
            )}
          </div>
          {review.findings.map((f, i) => (
            <div key={i} className={`border rounded-lg p-3 text-sm ${
              f.severity === 'HIGH' ? 'border-red-200 bg-red-50' :
              f.severity === 'MEDIUM' ? 'border-amber-200 bg-amber-50' : 'border-gray-200'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                  f.severity === 'HIGH' ? 'bg-red-200 text-red-700' :
                  f.severity === 'MEDIUM' ? 'bg-amber-200 text-amber-700' : 'bg-gray-200 text-gray-600'
                }`}>{f.severity}</span>
                <span className="text-xs text-gray-500">{f.category}</span>
              </div>
              <p className="text-gray-700">{f.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function InvoiceAnalysisPanel() {
  const [invoiceId, setInvoiceId] = useState('');

  const { data: invoices } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => apiGet<Array<{ id: string; invoice_number?: string; amount: number }>>('/api/v1/invoices'),
  });

  const { data: analysis } = useQuery({
    queryKey: ['ai-invoice', invoiceId],
    queryFn: () => apiGet<{
      signals: Array<{ type: string; severity: string; message: string }>;
      anomaly_count: number; high_risk_count: number; recommendation: string;
    }>(`/api/v1/ai/invoice/${invoiceId}/analyze`),
    enabled: !!invoiceId,
  });

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
      <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
        <DollarSign className="h-5 w-5 text-indigo-500" /> Invoice Analysis
      </h2>
      <select value={invoiceId} onChange={(e) => setInvoiceId(e.target.value)}
        className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none bg-white">
        <option value="">Select an invoice…</option>
        {invoices?.map((inv) => (
          <option key={inv.id} value={inv.id}>{inv.invoice_number ?? inv.id.slice(0, 8)} — ${Number(inv.amount).toFixed(2)}</option>
        ))}
      </select>

      {analysis && (
        <div className="space-y-3">
          <div className="flex gap-4 text-sm">
            <span className="text-gray-500">{analysis.anomaly_count} signals</span>
            {analysis.high_risk_count > 0 && (
              <span className="text-red-500 font-medium">{analysis.high_risk_count} high risk</span>
            )}
          </div>
          {analysis.signals.map((s, i) => (
            <div key={i} className={`border rounded-lg p-3 text-sm ${
              s.severity === 'HIGH' ? 'border-red-200 bg-red-50' : 'border-gray-200'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                  s.severity === 'HIGH' ? 'bg-red-200 text-red-700' : 'bg-gray-200 text-gray-600'
                }`}>{s.severity}</span>
                <span className="text-xs text-gray-500">{s.type}</span>
              </div>
              <p className="text-gray-700">{s.message}</p>
            </div>
          ))}
          <div className="flex items-start gap-2 pt-2 border-t border-gray-200">
            <Lightbulb className="h-4 w-4 text-amber-500 mt-0.5" />
            <p className="text-sm text-gray-700">{analysis.recommendation}</p>
          </div>
        </div>
      )}
    </div>
  );
}
