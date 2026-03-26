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
