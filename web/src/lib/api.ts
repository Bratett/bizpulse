const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
const ANALYTICS_URL =
  process.env.NEXT_PUBLIC_ANALYTICS_URL || "http://localhost:8081";

async function request<T>(
  baseUrl: string,
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  const res = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
    credentials: "include", // Send httpOnly cookies
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      res.status,
      body?.error?.code || "UNKNOWN",
      body?.error?.message || "Request failed"
    );
  }

  return res.json();
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
  }
}

// Auth API
export async function register(data: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  business_name: string;
}) {
  const res = await request<{
    token: string;
    user: any;
    business: any;
  }>(API_URL, "/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(data),
  });
  // Store user/business info (token is in httpOnly cookie)
  localStorage.setItem("user", JSON.stringify(res.user));
  localStorage.setItem("business", JSON.stringify(res.business));
  return res;
}

export async function login(email: string, password: string) {
  const res = await request<{
    token: string;
    user: any;
    business: any;
  }>(API_URL, "/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("user", JSON.stringify(res.user));
  localStorage.setItem("business", JSON.stringify(res.business));
  return res;
}

export function logout() {
  localStorage.removeItem("user");
  localStorage.removeItem("business");
}

// Transaction API
export async function createTransaction(data: {
  type: "INCOME" | "EXPENSE";
  amount_pesewas: number;
  account_code: string;
  description?: string;
  transaction_date: string;
}) {
  return request<any>(API_URL, "/v1/transactions", {
    method: "POST",
    body: JSON.stringify({
      ...data,
      idempotency_key: crypto.randomUUID(),
    }),
  });
}

export async function listTransactions(params?: {
  type?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}) {
  const query = new URLSearchParams();
  if (params?.type) query.set("type", params.type);
  if (params?.date_from) query.set("date_from", params.date_from);
  if (params?.date_to) query.set("date_to", params.date_to);
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));

  const qs = query.toString();
  return request<{ transactions: any[]; total: number }>(
    API_URL,
    `/v1/transactions${qs ? `?${qs}` : ""}`
  );
}

export async function listAccounts() {
  return request<any[]>(API_URL, "/v1/accounts");
}

// Analytics API
export async function getProfitLoss(dateFrom?: string, dateTo?: string) {
  const query = new URLSearchParams();
  if (dateFrom) query.set("date_from", dateFrom);
  if (dateTo) query.set("date_to", dateTo);

  const qs = query.toString();
  return request<any>(
    ANALYTICS_URL,
    `/reports/profit-loss${qs ? `?${qs}` : ""}`
  );
}

export async function getProfitLossTrend(months?: number) {
  const query = new URLSearchParams();
  if (months) query.set("months", String(months));

  const qs = query.toString();
  return request<any>(
    ANALYTICS_URL,
    `/reports/profit-loss/trend${qs ? `?${qs}` : ""}`
  );
}

// Helpers
export function pesewasToCedis(pesewas: number): string {
  return (pesewas / 100).toFixed(2);
}

export function cedisToPesewas(cedis: number): number {
  return Math.round(cedis * 100);
}

// ---------------------------------------------------------------------------
// Compliance / Tax API
// ---------------------------------------------------------------------------

const COMPLIANCE_URL =
  process.env.NEXT_PUBLIC_COMPLIANCE_URL || "http://localhost:8082";

// Types

export interface TaxPeriod {
  id: string;
  business_id: string;
  period_type: "VAT_MONTHLY" | "CIT_ANNUAL" | "WHT_MONTHLY";
  start_date: string;
  end_date: string;
  status: "DRAFT" | "COMPUTED" | "REVIEWED" | "FILED";
  computed_at: string | null;
  filed_at: string | null;
  created_at: string;
  total_liability_pesewas: number;
}

export interface TaxSummary {
  business_id: string;
  total_outstanding_pesewas: number;
  next_deadline: string | null;
  periods: TaxPeriod[];
  rates_as_of: string;
}

export interface VATReport {
  period_id: string;
  business_name: string;
  business_tin: string | null;
  period_start: string;
  period_end: string;
  taxable_sales_pesewas: number;
  output_vat_pesewas: number;
  taxable_purchases_pesewas: number;
  input_vat_pesewas: number;
  net_vat_payable_pesewas: number;
  nhil_pesewas: number;
  getfund_pesewas: number;
  total_payable_pesewas: number;
  computation_date: string | null;
}

export interface CITReport {
  period_id: string;
  business_name: string;
  business_tin: string | null;
  period_start: string;
  period_end: string;
  total_revenue_pesewas: number;
  total_deductible_expenses_pesewas: number;
  non_deductible_expenses_pesewas: number;
  net_profit_pesewas: number;
  cit_rate_bps: number;
  cit_liability_pesewas: number;
  computation_date: string | null;
}

export interface TaxRate {
  rate_type: string;
  rate_code: string;
  percentage_basis_points: number;
  effective_from: string;
  effective_to: string | null;
}

export interface TaxComputationItem {
  rate_type: string;
  rate_code: string;
  base_amount_pesewas: number;
  rate_bps: number;
  computed_amount_pesewas: number;
  computation_details: Record<string, unknown> | null;
}

export interface InvoiceLineItem {
  description: string;
  quantity: number;
  unit_price_pesewas: number;
  vat_applicable: boolean;
}

// Functions

export async function getTaxSummary(): Promise<TaxSummary> {
  return request<TaxSummary>(COMPLIANCE_URL, "/tax/summary");
}

export async function getTaxPeriods(filters?: {
  period_type?: string;
  status?: string;
}): Promise<TaxPeriod[]> {
  const params = new URLSearchParams();
  if (filters?.period_type) params.set("period_type", filters.period_type);
  if (filters?.status) params.set("status", filters.status);
  const qs = params.toString();
  return request<TaxPeriod[]>(
    COMPLIANCE_URL,
    `/tax/periods${qs ? `?${qs}` : ""}`
  );
}

export async function createTaxPeriod(data: {
  period_type: string;
  start_date: string;
  end_date: string;
}): Promise<TaxPeriod> {
  return request<TaxPeriod>(COMPLIANCE_URL, "/tax/periods", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function computeTaxPeriod(
  periodId: string
): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>(
    COMPLIANCE_URL,
    `/tax/periods/${periodId}/compute`,
    { method: "POST" }
  );
}

export async function getVATReport(periodId: string): Promise<VATReport> {
  return request<VATReport>(
    COMPLIANCE_URL,
    `/tax/reports/vat/${periodId}`
  );
}

export async function getCITReport(periodId: string): Promise<CITReport> {
  return request<CITReport>(
    COMPLIANCE_URL,
    `/tax/reports/cit/${periodId}`
  );
}

export async function markPeriodFiled(
  periodId: string,
  filingReference?: string,
  notes?: string
): Promise<{ status: string; period_id: string; filing_id: string; filed_at: string }> {
  return request(COMPLIANCE_URL, `/tax/periods/${periodId}/mark-filed`, {
    method: "POST",
    body: JSON.stringify({
      filing_reference: filingReference || null,
      filing_method: "MANUAL",
      notes: notes || null,
    }),
  });
}

export async function getTaxRates(): Promise<{
  rates: TaxRate[];
  as_of: string;
}> {
  return request(COMPLIANCE_URL, "/tax/rates");
}

export async function updateTaxCategory(
  transactionId: string,
  taxCategory: string
): Promise<{ transaction_id: string; tax_category: string }> {
  return request(COMPLIANCE_URL, `/tax/metadata/${transactionId}`, {
    method: "PATCH",
    body: JSON.stringify({ tax_category: taxCategory }),
  });
}

export async function generateInvoicePreview(data: {
  customer_name: string;
  customer_tin?: string;
  line_items: InvoiceLineItem[];
  notes?: string;
}): Promise<Blob> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  const res = await fetch(`${COMPLIANCE_URL}/invoices/preview`, {
    method: "POST",
    headers,
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      res.status,
      body?.error?.code || "UNKNOWN",
      body?.error?.message || "Failed to generate invoice"
    );
  }
  return res.blob();
}

// ---------------------------------------------------------------------------
// Kong Gateway URL (for future gateway-routed calls)
// ---------------------------------------------------------------------------

export const KONG_URL =
  process.env.NEXT_PUBLIC_KONG_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Invoice CRUD
// ---------------------------------------------------------------------------

export interface Invoice {
  id: string;
  business_id: string;
  invoice_number: string | null;
  customer_name: string;
  customer_tin: string | null;
  line_items: InvoiceLineItem[];
  subtotal_pesewas: number;
  vat_pesewas: number;
  total_pesewas: number;
  notes: string | null;
  status: "DRAFT" | "SENT" | "PAID" | "CANCELLED";
  created_at: string;
}

export async function createInvoice(data: {
  customer_name: string;
  customer_tin?: string;
  line_items: InvoiceLineItem[];
  notes?: string;
}): Promise<Invoice> {
  return request<Invoice>(COMPLIANCE_URL, "/invoices", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function listInvoices(status?: string): Promise<Invoice[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  const qs = params.toString();
  return request<Invoice[]>(
    COMPLIANCE_URL,
    `/invoices${qs ? `?${qs}` : ""}`
  );
}

export async function getInvoice(id: string): Promise<Invoice> {
  return request<Invoice>(COMPLIANCE_URL, `/invoices/${id}`);
}

export async function updateInvoice(
  id: string,
  data: {
    status?: string;
    notes?: string;
    customer_name?: string;
    customer_tin?: string;
  }
): Promise<Invoice> {
  return request<Invoice>(COMPLIANCE_URL, `/invoices/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function getInvoicePdf(id: string): Promise<Blob> {
  const res = await fetch(`${COMPLIANCE_URL}/invoices/${id}/pdf`, {
    credentials: "include",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      res.status,
      body?.error?.code || "UNKNOWN",
      body?.error?.message || "Failed to generate invoice PDF"
    );
  }
  return res.blob();
}

// ---------------------------------------------------------------------------
// Payroll API
// ---------------------------------------------------------------------------

export interface Employee {
  id: string;
  business_id: string;
  employee_number: string | null;
  first_name: string;
  last_name: string;
  tin: string | null;
  ssnit_number: string | null;
  status: string;
  hire_date: string;
}

export interface PayrollRecord {
  id: string;
  employee_id: string;
  employee_name: string;
  period_year: number;
  period_month: number;
  gross_salary_pesewas: number;
  ssnit_employee_pesewas: number;
  paye_pesewas: number;
  net_salary_pesewas: number;
  status: string;
}

export async function listEmployees(status?: string): Promise<Employee[]> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  const qs = params.toString();
  return request<Employee[]>(
    COMPLIANCE_URL,
    `/employees${qs ? `?${qs}` : ""}`
  );
}

export async function createEmployee(data: {
  first_name: string;
  last_name: string;
  employee_number?: string;
  tin?: string;
  ssnit_number?: string;
  hire_date: string;
}): Promise<Employee> {
  return request<Employee>(COMPLIANCE_URL, "/employees", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function computePayroll(
  year: number,
  month: number
): Promise<{
  period_year: number;
  period_month: number;
  employees_computed: number;
  records: Array<{
    employee_id: string;
    employee_name: string;
    gross_salary_pesewas: number;
    ssnit_employee_pesewas: number;
    paye_pesewas: number;
    net_salary_pesewas: number;
  }>;
}> {
  return request(COMPLIANCE_URL, "/payroll/compute", {
    method: "POST",
    body: JSON.stringify({ period_year: year, period_month: month }),
  });
}

export async function listPayrollRecords(
  year?: number,
  month?: number
): Promise<PayrollRecord[]> {
  const params = new URLSearchParams();
  if (year !== undefined) params.set("period_year", String(year));
  if (month !== undefined) params.set("period_month", String(month));
  const qs = params.toString();
  return request<PayrollRecord[]>(
    COMPLIANCE_URL,
    `/payroll/records${qs ? `?${qs}` : ""}`
  );
}
