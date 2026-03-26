"use client";

import { useEffect, useState } from "react";
import {
  listTransactions,
  listAccounts,
  createTransaction,
  cedisToPesewas,
  ApiError,
} from "@/lib/api";

function formatGHS(pesewas: number): string {
  const cedis = pesewas / 100;
  return cedis.toLocaleString("en-GH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const pageSize = 20;
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    type: "EXPENSE" as "INCOME" | "EXPENSE",
    amount_cedis: "",
    account_code: "",
    description: "",
    transaction_date: new Date().toISOString().split("T")[0],
  });

  useEffect(() => {
    loadData();
  }, []);

  async function loadData(pageNum = page) {
    setLoading(true);
    try {
      const [txnRes, acctRes] = await Promise.all([
        listTransactions({ limit: pageSize, offset: pageNum * pageSize }),
        listAccounts(),
      ]);
      setTransactions(txnRes.transactions);
      setTotal(txnRes.total);
      setAccounts(acctRes);
    } catch (err) {
      setError("Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const amountPesewas = cedisToPesewas(parseFloat(form.amount_cedis));
      if (amountPesewas <= 0 || isNaN(amountPesewas)) {
        setError("Enter a valid amount");
        setSubmitting(false);
        return;
      }

      await createTransaction({
        type: form.type,
        amount_pesewas: amountPesewas,
        account_code: form.account_code,
        description: form.description || undefined,
        transaction_date: form.transaction_date,
      });

      setForm({
        type: "EXPENSE",
        amount_cedis: "",
        account_code: "",
        description: "",
        transaction_date: new Date().toISOString().split("T")[0],
      });
      setShowForm(false);
      setToast("Transaction saved");
      setTimeout(() => setToast(""), 3000);
      await loadData();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to create transaction");
      }
    } finally {
      setSubmitting(false);
    }
  }

  const incomeAccounts = accounts.filter((a) => a.account_type === "income");
  const expenseAccounts = accounts.filter((a) => a.account_type === "expense");
  const relevantAccounts =
    form.type === "INCOME" ? incomeAccounts : expenseAccounts;
  const accountNameMap: Record<string, string> = {};
  accounts.forEach((a) => { accountNameMap[a.account_code] = a.account_name; });

  if (loading) {
    return (
      <div>
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-display font-bold text-xl text-neutral-text">
            Transactions
          </h1>
        </div>
        <div className="animate-pulse">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="flex justify-between py-3 border-b border-neutral-border-light"
            >
              <div className="skeleton h-4 w-24" />
              <div className="skeleton h-4 w-16" />
              <div className="skeleton h-4 w-32" />
              <div className="skeleton h-4 w-20" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Toast */}
      {toast && (
        <div
          role="alert"
          className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-success-bg text-success font-body text-sm px-5 py-2.5 rounded-sm shadow-lg flex items-center gap-2 animate-[slideDown_0.2s_ease-out]"
        >
          ✓ {toast}
        </div>
      )}

      <div className="flex items-center justify-between mb-8">
        <h1 className="font-display font-bold text-xl text-neutral-text">
          Transactions
        </h1>
        <div className="flex items-center gap-2">
          {transactions.length > 0 && (
            <button
              onClick={() => {
                const header = "Date,Type,Category,Description,Amount (GHS)\n";
                const rows = transactions.map((t) => {
                  const date = formatDate(t.transaction_date);
                  const name = accountNameMap[t.account_code] || t.account_code;
                  const desc = (t.description || "").replace(/,/g, ";");
                  const sign = t.type === "INCOME" ? "" : "-";
                  const amount = sign + (t.amount_pesewas / 100).toFixed(2);
                  return `${date},${t.type},${name},${desc},${amount}`;
                }).join("\n");
                const blob = new Blob([header + rows], { type: "text/csv" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `bizpulse-transactions-${new Date().toISOString().split("T")[0]}.csv`;
                a.click();
                URL.revokeObjectURL(url);
              }}
              className="font-display font-semibold text-sm bg-surface-raised text-neutral-secondary border border-neutral-border px-4 py-2.5 rounded-sm hover:border-primary hover:text-primary transition-colors min-h-[44px]"
            >
              Download CSV
            </button>
          )}
          <button
            onClick={() => setShowForm(!showForm)}
            className="font-display font-semibold text-sm bg-primary text-white px-5 py-2.5 rounded-sm hover:bg-primary-light transition-colors min-h-[44px]"
          >
            {showForm ? "Cancel" : "+ Add Transaction"}
          </button>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="bg-danger-bg text-danger font-body text-sm p-3 rounded-sm mb-6"
        >
          {error}
        </div>
      )}

      {/* Transaction Form */}
      {showForm && (
        <div className="bg-surface-raised border border-neutral-border-light rounded-md p-6 mb-8">
          <h2 className="font-display font-bold text-sm uppercase tracking-widest text-neutral-muted mb-5">
            New Transaction
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                  Type
                </label>
                <select
                  className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  value={form.type}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      type: e.target.value as "INCOME" | "EXPENSE",
                      account_code: "",
                    })
                  }
                >
                  <option value="INCOME">Income</option>
                  <option value="EXPENSE">Expense</option>
                </select>
              </div>
              <div>
                <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                  Amount (GHS)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  className="w-full font-mono text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="0.00"
                  value={form.amount_cedis}
                  onChange={(e) =>
                    setForm({ ...form, amount_cedis: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                  Category
                </label>
                <select
                  required
                  className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  value={form.account_code}
                  onChange={(e) =>
                    setForm({ ...form, account_code: e.target.value })
                  }
                >
                  <option value="">Select category</option>
                  {relevantAccounts.map((a) => (
                    <option key={a.account_code} value={a.account_code}>
                      {a.account_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                  Date
                </label>
                <input
                  type="date"
                  required
                  className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  value={form.transaction_date}
                  onChange={(e) =>
                    setForm({ ...form, transaction_date: e.target.value })
                  }
                />
              </div>
            </div>

            <div>
              <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                Description (optional)
              </label>
              <input
                type="text"
                maxLength={500}
                className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="What was this for?"
                value={form.description}
                onChange={(e) =>
                  setForm({ ...form, description: e.target.value })
                }
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="font-display font-semibold text-sm bg-primary text-white px-6 py-2.5 rounded-sm hover:bg-primary-light transition-colors disabled:opacity-50 min-h-[44px]"
            >
              {submitting ? "Saving..." : "Save Transaction"}
            </button>
          </form>
        </div>
      )}

      {/* Transaction List */}
      {transactions.length === 0 ? (
        <div className="text-center py-16">
          <p className="font-display font-bold text-lg text-neutral-text mb-1">
            Your first transaction is waiting
          </p>
          <p className="font-body text-neutral-muted mb-6">
            Add one to start tracking your finances.
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="font-display font-semibold text-sm bg-primary text-white px-6 py-2.5 rounded-sm hover:bg-primary-light transition-colors min-h-[44px]"
          >
            + Add Transaction
          </button>
        </div>
      ) : (
        <>
          {/* Desktop table */}
          <div className="hidden sm:block">
            <table className="w-full font-body text-sm">
              <thead>
                <tr className="border-b-2 border-neutral-border-light">
                  <th className="text-left py-2.5 font-semibold text-neutral-muted text-xs uppercase tracking-widest">
                    Date
                  </th>
                  <th className="text-left py-2.5 font-semibold text-neutral-muted text-xs uppercase tracking-widest">
                    Type
                  </th>
                  <th className="text-left py-2.5 font-semibold text-neutral-muted text-xs uppercase tracking-widest">
                    Category
                  </th>
                  <th className="text-left py-2.5 font-semibold text-neutral-muted text-xs uppercase tracking-widest">
                    Description
                  </th>
                  <th className="text-right py-2.5 font-semibold text-neutral-muted text-xs uppercase tracking-widest">
                    Amount
                  </th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((t) => (
                  <tr
                    key={t.id}
                    className="border-b border-neutral-border-light last:border-b-0"
                  >
                    <td className="py-3 text-neutral-secondary">
                      {formatDate(t.transaction_date)}
                    </td>
                    <td className="py-3">
                      <span
                        className={`inline-block font-display font-semibold text-xs uppercase tracking-wide px-2 py-0.5 rounded-sm ${
                          t.type === "INCOME"
                            ? "bg-success-bg text-success"
                            : "bg-danger-bg text-danger"
                        }`}
                      >
                        {t.type}
                      </span>
                    </td>
                    <td className="py-3 text-neutral-secondary">
                      {accountNameMap[t.account_code] || t.account_code}
                    </td>
                    <td className="py-3 text-neutral-muted">
                      {t.description || "—"}
                    </td>
                    <td
                      className={`py-3 text-right font-mono ${
                        t.type === "INCOME"
                          ? "text-success"
                          : "text-danger"
                      }`}
                    >
                      {t.type === "INCOME" ? "+" : "-"}
                      {formatGHS(t.amount_pesewas)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile card list */}
          <div className="sm:hidden space-y-3">
            {transactions.map((t) => (
              <div
                key={t.id}
                className="flex items-center justify-between py-3 border-b border-neutral-border-light"
              >
                <div>
                  <p className="font-body text-sm text-neutral-text">
                    {t.description || t.account_code}
                  </p>
                  <p className="font-body text-xs text-neutral-muted">
                    {formatDate(t.transaction_date)} ·{" "}
                    <span
                      className={
                        t.type === "INCOME"
                          ? "text-success"
                          : "text-danger"
                      }
                    >
                      {t.type}
                    </span>
                  </p>
                </div>
                <span
                  className={`font-mono text-sm font-medium ${
                    t.type === "INCOME" ? "text-success" : "text-danger"
                  }`}
                >
                  {t.type === "INCOME" ? "+" : "-"}
                  {formatGHS(t.amount_pesewas)}
                </span>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {total > pageSize && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t border-neutral-border-light">
              <p className="font-body text-sm text-neutral-muted">
                Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, total)} of {total}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => { const p = page - 1; setPage(p); loadData(p); }}
                  disabled={page === 0}
                  className="font-body text-sm px-3 py-1.5 rounded-sm border border-neutral-border bg-surface-raised text-neutral-secondary hover:border-primary disabled:opacity-40 disabled:cursor-not-allowed min-h-[36px]"
                >
                  Previous
                </button>
                <button
                  onClick={() => { const p = page + 1; setPage(p); loadData(p); }}
                  disabled={(page + 1) * pageSize >= total}
                  className="font-body text-sm px-3 py-1.5 rounded-sm border border-neutral-border bg-surface-raised text-neutral-secondary hover:border-primary disabled:opacity-40 disabled:cursor-not-allowed min-h-[36px]"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
