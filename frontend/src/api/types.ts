// ---------------------------------------------------------------------------
// Shared API types mirroring backend Pydantic schemas
// ---------------------------------------------------------------------------

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  message?: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

// ── Auth ──────────────────────────────────────────────────────────────────

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface MeResponse {
  user: User;
  roles: string[];
  tenant_id: string;
}

// ── User ──────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  username: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  is_superuser: boolean;
}

// ── Supplier ──────────────────────────────────────────────────────────────

export type SupplierStatus = 'DRAFT' | 'INVITED' | 'REGISTERED' | 'APPROVED' | 'BLOCKED';

export interface Supplier {
  id: string;
  supplier_name: string;
  supplier_number?: string | null;
  status: SupplierStatus;
  risk_score?: number | null;
  description?: string | null;
  address?: string | null;
  is_active: boolean;
  created_at?: string | null;
}

export interface SupplierCreatePayload {
  supplier_name: string;
  supplier_number?: string;
  description?: string;
  address?: string;
}

// ── Purchase Requisition ─────────────────────────────────────────────────

export type PRStatus = 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'ORDERED';

export interface PurchaseRequisition {
  id: string;
  pr_number?: string | null;
  status: PRStatus;
  supplier_id?: string | null;
  description?: string | null;
  items?: PRItem[];
  created_at?: string | null;
}

export interface PRItem {
  id: string;
  description?: string | null;
  quantity?: number | null;
  unit_price?: number | null;
}

export interface PRCreatePayload {
  supplier_id?: string;
  description?: string;
  items: { description?: string; quantity?: number; unit_price?: number }[];
}

// ── Purchase Order ───────────────────────────────────────────────────────

export type POStatus = 'CREATED' | 'APPROVED' | 'SENT' | 'ACKNOWLEDGED' | 'PARTIALLY_RECEIVED' | 'RECEIVED' | 'CLOSED' | 'CANCELLED';

export interface PurchaseOrder {
  id: string;
  po_number?: string | null;
  supplier_id: string;
  status: POStatus;
  items?: POItem[];
  created_at?: string | null;
}

export interface POItem {
  id: string;
  description?: string | null;
  quantity?: number | null;
  price?: number | null;
}

// ── Invoice ──────────────────────────────────────────────────────────────

export type MatchStatus = 'PENDING' | 'MATCHED' | 'EXCEPTION';

export interface MatchIssue {
  code: string;
  message: string;
  variance?: number;
  tolerance?: number;
  qty_ordered?: number;
  qty_received?: number;
}

export interface MatchResult {
  invoice_id?: string;
  invoice_number?: string | null;
  invoice_amount?: number;
  po_id?: string | null;
  po_number?: string | null;
  po_total?: number;
  qty_ordered?: number;
  qty_received?: number;
  amount_received?: number;
  receipt_ids?: string[];
  receipt_count?: number;
  amount_variance?: number;
  amount_tolerance?: number;
  auto_resolve_tolerance?: number;
  has_po?: boolean;
  has_receipt?: boolean;
  match_type?: string;
  status?: string;
  primary_issue?: string | null;
  issues?: MatchIssue[];
  passed?: boolean;
  evaluated_at?: string;
  resolution?: Record<string, unknown>;
}

export interface Invoice {
  id: string;
  invoice_number?: string | null;
  po_id: string;
  amount: number;
  match_status: MatchStatus;
  invoice_date?: string | null;
  due_date?: string | null;
  extras?: {
    match_result?: MatchResult;
    demo_scenario?: string;
    payment_status?: 'READY' | 'SENT_TO_PAYMENT' | string;
    payment_ready?: boolean;
    sent_to_payment_at?: string;
    [key: string]: unknown;
  } | null;
  created_at?: string | null;
}

export interface InvoiceCreatePayload {
  po_id: string;
  amount: number;
  invoice_number?: string;
  invoice_date?: string;
  due_date?: string;
}

export interface MatchContextResponse {
  invoice: Invoice;
  match: MatchResult;
  stored_match_result?: MatchResult | null;
}

export interface ResolutionSuggestion {
  invoice_id: string;
  match_status?: string | null;
  action: 'auto_match_tolerance' | 'await_grn' | 're_match' | 'escalate' | string;
  can_auto_resolve: boolean;
  explanation: string;
  match?: MatchResult;
}

export interface AutoResolveResponse {
  success: boolean;
  action?: string;
  explanation?: string;
  error?: string;
  invoice_id?: string;
  match_status?: string | null;
}

export interface Receipt {
  id: string;
  receipt_number?: string | null;
  po_id: string;
  status?: string | null;
  received_date?: string | null;
  quantity_received?: number | null;
  amount_received?: number | null;
}

export interface Contract {
  id: string;
  contract_number?: string | null;
  contract_value?: number | null;
  start_date?: string | null;
  end_date?: string | null;
  description?: string | null;
  status?: string | null;
  created_at?: string | null;
}

// ── Workflow ─────────────────────────────────────────────────────────────

export interface ApprovalTask {
  id: string;
  workflow_id: string;
  approver_id?: string | null;
  status?: string | null;
  completed_at?: string | null;
  created_at?: string | null;
}

export interface Workflow {
  id: string;
  object_type: string;
  object_id: string;
  status: string;
  tasks?: ApprovalTask[];
  created_at?: string | null;
}

// ── Dashboard / Analytics ────────────────────────────────────────────────

export interface DashboardData {
  kpi_summary: Record<string, unknown>;
  spend: Record<string, unknown>;
  suppliers: Record<string, unknown>;
  cycle_times: Record<string, unknown>;
  contracts: Record<string, unknown>;
}

export interface SpendCategory {
  category: string;
  total: number;
  percentage?: number;
}

export interface SpendTrend {
  month: string;
  total: number;
}

export interface SupplierScorecard {
  supplier_id: string;
  supplier_name: string;
  total_spend: number;
  invoice_count: number;
  on_time_rate?: number;
  quality_score?: number;
  risk_score?: number;
}

// ── Integrations ─────────────────────────────────────────────────────────

export interface ConnectionResponse {
  id: string;
  connection_name: string;
  connector_type: string;
  endpoint_url?: string | null;
  auth_type?: string | null;
  is_connected: boolean;
  last_test_at?: string | null;
  last_sync_at?: string | null;
  tenant_id: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface SyncResponse {
  run_id: string;
  status: string;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_failed: number;
  errors?: Array<Record<string, unknown>> | null;
}

export interface RunResponse {
  id: string;
  connection_id: string;
  direction: string;
  status: string;
  started_at?: string | null;
  completed_at?: string | null;
  records_processed?: number | null;
  errors?: Record<string, unknown> | null;
  created_at?: string | null;
}

// ── Receiving ────────────────────────────────────────────────────────────

export interface Receipt {
  id: string;
  receipt_number?: string | null;
  po_id: string;
  status: string;
  received_date?: string | null;
  quantity_received?: number | null;
  amount_received?: number | null;
  created_at?: string | null;
}

export interface SupplierContract {
  id: string;
  contract_number?: string | null;
  contract_value?: number | null;
  start_date?: string | null;
  end_date?: string | null;
}

export interface SupplierPurchaseOrder {
  id: string;
  po_number?: string | null;
  status: string;
  total_amount: number;
  created_at?: string | null;
}
