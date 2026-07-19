import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '../../api/client';
import type { AutoResolveResponse, Invoice, MatchResult } from '../../api/types';
import { ArrowLeft, DollarSign, CheckCircle, Upload, Bot, GitCompareArrows } from 'lucide-react';
import { ActivityTimeline } from '../../components/audit/ActivityTimeline';
import { useToast } from '../../components/Toast';

const matchColors: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-700',
  MATCHED: 'bg-green-100 text-green-700',
  EXCEPTION: 'bg-red-100 text-red-600',
};

export default function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: invoice, isLoading } = useQuery({
    queryKey: ['invoice', id],
    queryFn: () => apiGet<Invoice>(`/api/v1/invoices/${id}`),
    enabled: !!id,
  });

  const matchMutation = useMutation({
    mutationFn: () => apiPost(`/api/v1/invoices/${id}/match`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] });
      toast('success', 'Match completed');
    },
    onError: (err: Error) => toast('error', err.message || 'Match failed'),
  });

  const resolveMutation = useMutation({
    mutationFn: () =>
      apiPost<AutoResolveResponse>(`/api/v1/ai/invoice/${id}/resolve-exception`),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      if (data.success) toast('success', data.explanation || 'Exception resolved');
      else toast('error', data.error || 'Could not auto-resolve');
    },
    onError: (err: Error) => toast('error', err.message || 'Auto-resolve failed'),
  });

  const manualResolveMutation = useMutation({
    mutationFn: (note: string) =>
      apiPost(`/api/v1/invoices/${id}/resolve-exception`, { mode: 'manual', note }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] });
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      toast('success', 'Exception cleared manually');
    },
    onError: (err: Error) => toast('error', err.message || 'Manual resolve failed'),
  });

  const approveMutation = useMutation({
    mutationFn: () => apiPost(`/api/v1/invoices/${id}/approve`, { approved: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoice', id] });
      toast('success', 'Payment approved');
    },
    onError: (err: Error) => toast('error', err.message || 'Approve failed'),
  });

  if (isLoading) return <div className="text-gray-500 p-8">Loading…</div>;
  if (!invoice) return <div className="text-red-500 p-8">Invoice not found</div>;

  const matchResult = invoice.extras?.match_result as MatchResult | undefined;

  return (
    <div className="max-w-3xl space-y-6">
      <button onClick={() => navigate('/invoices')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700">
        <ArrowLeft className="h-4 w-4" /> Back to Invoices
      </button>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 rounded-lg">
              <DollarSign className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{invoice.invoice_number ?? 'Untitled Invoice'}</h1>
              <p className="text-sm text-gray-500">PO: {invoice.po_id.slice(0, 8)}…</p>
            </div>
          </div>
          <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${matchColors[invoice.match_status] ?? ''}`}>
            {invoice.match_status}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-6 text-sm">
          <div>
            <span className="text-gray-500">Amount</span>
            <p className="text-xl font-bold text-gray-900 mt-0.5">${Number(invoice.amount).toFixed(2)}</p>
          </div>
          <div>
            <span className="text-gray-500">Invoice Date</span>
            <p className="font-medium text-gray-900 mt-0.5">{invoice.invoice_date ?? 'Not set'}</p>
          </div>
          <div>
            <span className="text-gray-500">Due Date</span>
            <p className="font-medium text-gray-900 mt-0.5">{invoice.due_date ?? 'Not set'}</p>
          </div>
        </div>

        {matchResult && (
          <div className="rounded-lg border border-gray-100 bg-gray-50 p-4 text-sm space-y-2">
            <p className="font-medium text-gray-900">Last match result</p>
            <p className="text-gray-600">
              Type: {matchResult.match_type ?? '—'} · PO total ${Number(matchResult.po_total ?? 0).toFixed(2)} ·
              Variance ${Number(matchResult.amount_variance ?? 0).toFixed(2)}
            </p>
            {matchResult.issues && matchResult.issues.length > 0 && (
              <ul className="text-rose-700 space-y-1">
                {matchResult.issues.map((i) => (
                  <li key={i.code}>{i.code}: {i.message}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        <div className="flex gap-3 pt-4 border-t border-gray-100 flex-wrap">
          {(invoice.match_status === 'PENDING' || invoice.match_status === 'EXCEPTION') && (
            <button onClick={() => matchMutation.mutate()}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700">
              <CheckCircle className="h-4 w-4" /> Match Invoice
            </button>
          )}
          {invoice.match_status === 'EXCEPTION' && (
            <button
              onClick={() => resolveMutation.mutate()}
              disabled={resolveMutation.isPending}
              className="flex items-center gap-2 bg-cyan-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-cyan-700 disabled:opacity-50"
            >
              <Bot className="h-4 w-4" /> Auto-Resolve
            </button>
          )}
          {invoice.match_status === 'EXCEPTION' && (
            <button
              onClick={() => {
                const note = window.prompt('Resolution note (required for manual clear):');
                if (note === null) return;
                if (!note.trim()) {
                  toast('error', 'Enter a resolution note');
                  return;
                }
                manualResolveMutation.mutate(note.trim());
              }}
              disabled={manualResolveMutation.isPending}
              className="flex items-center gap-2 bg-amber-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-amber-700 disabled:opacity-50"
            >
              Manual Resolve
            </button>
          )}
          {invoice.match_status === 'MATCHED' && (
            <button onClick={() => approveMutation.mutate()}
              className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700">
              <CheckCircle className="h-4 w-4" /> Approve Payment
            </button>
          )}
          <Link
            to={`/matching`}
            state={{ invoiceId: id }}
            className="flex items-center gap-2 text-indigo-700 px-4 py-2 rounded-lg text-sm font-medium border border-indigo-200 hover:bg-indigo-50"
          >
            <GitCompareArrows className="h-4 w-4" /> Open in Matching
          </Link>
          <button onClick={() => toast('info', 'Upload invoice PDF — coming in v0.8')}
            className="flex items-center gap-2 text-gray-600 px-4 py-2 rounded-lg text-sm font-medium border border-gray-300 hover:bg-gray-50 transition">
            <Upload className="h-4 w-4" /> Upload Invoice PDF
          </button>
        </div>
      </div>

      {id && <ActivityTimeline entityType="invoice" entityId={id} />}
    </div>
  );
}
