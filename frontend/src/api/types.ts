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
  description?: string;
  items: { description?: string; quantity?: number; unit_price?: number }[];
}

// ── Purchase Order ───────────────────────────────────────────────────────

export type POStatus = 'CREATED' | 'SENT' | 'CONFIRMED' | 'CLOSED' | 'CANCELLED';

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

export interface Invoice {
  id: string;
  invoice_number?: string | null;
  po_id: string;
  amount: number;
  match_status: MatchStatus;
  invoice_date?: string | null;
  due_date?: string | null;
  created_at?: string | null;
}

export interface Contract {
  id: string;
  contract_number?: string | null;
  contract_value?: number | null;
  start_date?: string | null;
  end_date?: string | null;
  description?: string | null;
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
