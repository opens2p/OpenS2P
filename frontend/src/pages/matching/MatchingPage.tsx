import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useLocation } from 'react-router-dom';
import {
  Bot,
  CheckCircle2,
  FileWarning,
  GitCompareArrows,
  Loader2,
  Package,
  Receipt,
  Scale,
  Sparkles,
} from 'lucide-react';
import { apiGet, apiPost } from '../../api/client';
import type {
  AutoResolveResponse,
  Invoice,
  MatchContextResponse,
  MatchResult,
  ResolutionSuggestion,
} from '../../api/types';
import { useToast } from '../../components/Toast';

const statusColors: Record<string, string> = {
  PENDING: 'bg-amber-100 text-amber-800',
  MATCHED: 'bg-emerald-100 text-emerald-800',
  EXCEPTION: 'bg-rose-100 text-rose-800',
};

function money(n?: number | null) {
  return `$${Number(n ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function MatchingPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const location = useLocation();
  const initialId = (location.state as { invoiceId?: string } | null)?.invoiceId ?? '';
  const [selectedId, setSelectedId] = useState<string>(initialId);

  const { data: invoices, isLoading: listLoading } = useQuery({
    queryKey: ['invoices', 'matching'],
    queryFn: () => apiGet<Invoice[]>('/api/v1/invoices?limit=200'),
  });

  const queue = useMemo(() => {
    const list = invoices ?? [];
    const demo = list.filter((i) =>
      (i.invoice_number ?? '').startsWith('INV-MATCH-') ||
      i.extras?.demo_scenario,
    );
    const pending = list.filter((i) => i.match_status === 'PENDING' || i.match_status === 'EXCEPTION');
    // Prefer demo scenarios first, then other queue items
    const seen = new Set<string>();
    const ordered: Invoice[] = [];
    for (const inv of [...demo, ...pending]) {
      if (seen.has(inv.id)) continue;
      seen.add(inv.id);
      ordered.push(inv);
    }
    return ordered;
  }, [invoices]);

  // Auto-select first queue item
  const activeId = selectedId || queue[0]?.id || '';

  const { data: context, isLoading: ctxLoading, refetch: refetchCtx } = useQuery({
    queryKey: ['match-context', activeId],
    queryFn: () => apiGet<MatchContextResponse>(`/api/v1/ai/invoice/${activeId}/match-context`),
    enabled: !!activeId,
  });

  const { data: suggestion, refetch: refetchSuggestion } = useQuery({
    queryKey: ['match-suggestion', activeId],
    queryFn: () => apiGet<ResolutionSuggestion>(`/api/v1/ai/invoice/${activeId}/suggest-resolution`),
    enabled: !!activeId,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['invoices'] });
    queryClient.invalidateQueries({ queryKey: ['match-context', activeId] });
    queryClient.invalidateQueries({ queryKey: ['match-suggestion', activeId] });
    queryClient.invalidateQueries({ queryKey: ['invoice', activeId] });
  };

  const matchMutation = useMutation({
    mutationFn: () => apiPost<Invoice>(`/api/v1/invoices/${activeId}/match`),
    onSuccess: (data) => {
      invalidate();
      refetchCtx();
      refetchSuggestion();
      toast(
        data.match_status === 'MATCHED' ? 'success' : 'info',
        data.match_status === 'MATCHED'
          ? '3-way match passed'
          : 'Exception flagged — review agent recommendation',
      );
    },
    onError: (err: Error) => toast('error', err.message || 'Match failed'),
  });

  const resolveMutation = useMutation({
    mutationFn: () =>
      apiPost<AutoResolveResponse>(`/api/v1/ai/invoice/${activeId}/resolve-exception`),
    onSuccess: (data) => {
      invalidate();
      refetchCtx();
      refetchSuggestion();
      if (data.success) {
        toast('success', data.explanation || 'Exception auto-resolved');
      } else {
        toast('error', data.error || 'Could not auto-resolve');
      }
    },
    onError: (err: Error) => toast('error', err.message || 'Auto-resolve failed'),
  });

  const sendToPaymentMutation = useMutation({
    mutationFn: () => apiPost(`/api/v1/invoices/${activeId}/pay`),
    onSuccess: () => {
      invalidate();
      refetchCtx();
      toast('success', 'Invoice sent to payment');
    },
    onError: (err: Error) => toast('error', err.message || 'Send to payment failed'),
  });

  const match: MatchResult | undefined =
    context?.stored_match_result || context?.match;
  const invoice = context?.invoice;
  const status = invoice?.match_status ?? 'PENDING';

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-indigo-600 text-sm font-medium mb-1">
            <GitCompareArrows className="h-4 w-4" />
            Intelligent 3-Way Match
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Matching Workspace</h1>
          <p className="text-gray-500 mt-1 max-w-2xl">
            Reconcile Purchase Order, Supplier Invoice, and Goods Receipt — then let the
            autonomous exception handler resolve mismatches within policy.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[280px_1fr_320px] gap-6">
        {/* Queue */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-900">Match Queue</h2>
            <p className="text-xs text-gray-400 mt-0.5">{queue.length} invoices</p>
          </div>
          {listLoading ? (
            <div className="p-6 flex justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-indigo-500" />
            </div>
          ) : (
            <ul className="divide-y divide-gray-50 max-h-[640px] overflow-y-auto">
              {queue.map((inv) => (
                <li key={inv.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(inv.id)}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition ${
                      inv.id === activeId ? 'bg-indigo-50/70' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {inv.invoice_number ?? inv.id.slice(0, 8)}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${statusColors[inv.match_status]}`}>
                        {inv.match_status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{money(inv.amount)}</p>
                    {inv.extras?.demo_scenario && (
                      <p className="text-[10px] text-indigo-500 mt-1 uppercase tracking-wide">
                        Demo · {String(inv.extras.demo_scenario).replace('_', ' ')}
                      </p>
                    )}
                  </button>
                </li>
              ))}
              {queue.length === 0 && (
                <li className="p-6 text-sm text-gray-400 text-center">No pending invoices</li>
              )}
            </ul>
          )}
        </div>

        {/* Triad */}
        <div className="space-y-4">
          {ctxLoading || !activeId ? (
            <div className="bg-white rounded-xl border border-gray-200 p-12 flex justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <DocPanel
                  title="Purchase Order"
                  icon={<Package className="h-4 w-4 text-slate-600" />}
                  accent="border-slate-200"
                >
                  <Metric label="Number" value={match?.po_number ?? '—'} />
                  <Metric label="PO Total" value={money(match?.po_total)} />
                  <Metric label="Qty Ordered" value={String(match?.qty_ordered ?? 0)} />
                </DocPanel>
                <DocPanel
                  title="Supplier Invoice"
                  icon={<Receipt className="h-4 w-4 text-amber-600" />}
                  accent="border-amber-200"
                >
                  <Metric label="Number" value={match?.invoice_number ?? invoice?.invoice_number ?? '—'} />
                  <Metric label="Amount" value={money(match?.invoice_amount ?? invoice?.amount)} />
                  <Metric
                    label="Variance vs PO"
                    value={money(match?.amount_variance)}
                    highlight={Math.abs(Number(match?.amount_variance ?? 0)) > Number(match?.amount_tolerance ?? 0)}
                  />
                </DocPanel>
                <DocPanel
                  title="Goods Receipt"
                  icon={<Scale className="h-4 w-4 text-emerald-600" />}
                  accent="border-emerald-200"
                >
                  <Metric label="Receipts" value={String(match?.receipt_count ?? 0)} />
                  <Metric label="Qty Received" value={String(match?.qty_received ?? 0)} />
                  <Metric label="Amount Received" value={money(match?.amount_received)} />
                </DocPanel>
              </div>

              <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                <div className="flex items-center justify-between gap-3 mb-4">
                  <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                    <FileWarning className="h-4 w-4 text-gray-500" />
                    Match Result
                  </h3>
                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${statusColors[status]}`}>
                    {status}
                    {match?.match_type ? ` · ${match.match_type}` : ''}
                  </span>
                </div>
                {match?.issues && match.issues.length > 0 ? (
                  <ul className="space-y-2">
                    {match.issues.map((issue) => (
                      <li
                        key={issue.code}
                        className="text-sm text-rose-700 bg-rose-50 border border-rose-100 rounded-lg px-3 py-2"
                      >
                        <span className="font-semibold">{issue.code}</span>
                        <span className="text-rose-600"> — {issue.message}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2">
                    {match?.passed
                      ? 'PO, Invoice, and GRN reconcile within tolerance.'
                      : 'Run 3-Way Match to evaluate this invoice.'}
                  </p>
                )}
                <div className="flex flex-wrap gap-2 mt-4">
                  <button
                    type="button"
                    onClick={() => matchMutation.mutate()}
                    disabled={matchMutation.isPending}
                    className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {matchMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <GitCompareArrows className="h-4 w-4" />}
                    Run 3-Way Match
                  </button>
                  {status === 'MATCHED' && invoice?.extras?.payment_status !== 'SENT_TO_PAYMENT' && (
                    <button
                      type="button"
                      onClick={() => sendToPaymentMutation.mutate()}
                      disabled={sendToPaymentMutation.isPending}
                      className="inline-flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
                    >
                      <CheckCircle2 className="h-4 w-4" /> Send to Payment
                    </button>
                  )}
                  {invoice?.extras?.payment_status === 'SENT_TO_PAYMENT' && (
                    <span className="inline-flex items-center gap-2 text-sm text-emerald-700 px-3 py-2 font-medium">
                      <CheckCircle2 className="h-4 w-4" /> Sent to Payment
                    </span>
                  )}
                  <Link
                    to={`/invoices/${activeId}`}
                    className="inline-flex items-center gap-2 text-sm text-gray-600 px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50"
                  >
                    Invoice detail
                  </Link>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Agent panel */}
        <div className="bg-gradient-to-b from-slate-900 to-slate-800 rounded-xl shadow-sm p-5 text-white">
          <div className="flex items-center gap-2 mb-1">
            <Bot className="h-5 w-5 text-cyan-300" />
            <h2 className="text-sm font-semibold">Exception Agent</h2>
          </div>
          <p className="text-xs text-slate-300 mb-4">
            Hybrid rules + AI explanation. Auto-resolves within tolerance; escalates hard mismatches.
          </p>

          {suggestion ? (
            <div className="space-y-4">
              <div className="rounded-lg bg-white/5 border border-white/10 p-3">
                <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">Suggested action</p>
                <p className="text-sm font-semibold text-cyan-200">
                  {suggestion.action.replace(/_/g, ' ')}
                </p>
              </div>
              <div className="rounded-lg bg-white/5 border border-white/10 p-3">
                <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1">
                  <Sparkles className="h-3 w-3" /> Explanation
                </p>
                <p className="text-sm text-slate-100 leading-relaxed">{suggestion.explanation}</p>
              </div>
              <button
                type="button"
                onClick={() => resolveMutation.mutate()}
                disabled={
                  resolveMutation.isPending ||
                  status !== 'EXCEPTION' ||
                  !suggestion.can_auto_resolve
                }
                className="w-full inline-flex items-center justify-center gap-2 bg-cyan-400 text-slate-900 px-4 py-2.5 rounded-lg text-sm font-semibold hover:bg-cyan-300 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {resolveMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
                Auto-Resolve
              </button>
              {status === 'EXCEPTION' && !suggestion.can_auto_resolve && (
                <p className="text-xs text-amber-200/90">
                  {suggestion.action === 'await_grn'
                    ? 'Record a goods receipt on Receiving, then retry Auto-Resolve.'
                    : 'Variance exceeds policy — escalate to AP.'}
                </p>
              )}
              {status !== 'EXCEPTION' && (
                <p className="text-xs text-slate-400">
                  Auto-Resolve is available after Match flags an EXCEPTION.
                </p>
              )}
            </div>
          ) : (
            <div className="flex justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-cyan-300" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DocPanel({
  title,
  icon,
  accent,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  accent: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`bg-white rounded-xl border ${accent} shadow-sm p-4 space-y-3`}>
      <div className="flex items-center gap-2 text-sm font-semibold text-gray-900">
        {icon}
        {title}
      </div>
      {children}
    </div>
  );
}

function Metric({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-gray-400">{label}</p>
      <p className={`text-sm font-medium mt-0.5 ${highlight ? 'text-rose-600' : 'text-gray-900'}`}>
        {value}
      </p>
    </div>
  );
}
