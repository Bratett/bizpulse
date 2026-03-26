"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  getTaxSummary,
  createTaxPeriod,
  computeTaxPeriod,
  markPeriodFiled,
  ApiError,
  type TaxPeriod,
  type TaxSummary,
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

function daysUntil(dateStr: string): number {
  const target = new Date(dateStr);
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

const PERIOD_TYPE_LABELS: Record<string, string> = {
  VAT_MONTHLY: "VAT (Monthly)",
  CIT_ANNUAL: "CIT (Annual)",
  WHT_MONTHLY: "WHT (Monthly)",
};

const STATUS_STYLES: Record<
  string,
  { bg: string; text: string; label: string }
> = {
  DRAFT: {
    bg: "bg-surface-alt",
    text: "text-neutral-muted",
    label: "Draft",
  },
  COMPUTED: {
    bg: "bg-info-bg",
    text: "text-info",
    label: "Computed",
  },
  REVIEWED: {
    bg: "bg-warning-bg",
    text: "text-warning",
    label: "Reviewed",
  },
  FILED: {
    bg: "bg-success-bg",
    text: "text-success",
    label: "Filed",
  },
};

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function TaxSkeleton() {
  return (
    <div className="animate-pulse">
      {/* Hero skeleton */}
      <div className="text-center py-8 mb-8 border-b border-neutral-border-light">
        <div className="skeleton h-4 w-48 mx-auto mb-3" />
        <div className="skeleton h-12 w-64 mx-auto mb-3" />
        <div className="skeleton h-4 w-56 mx-auto" />
      </div>
      {/* Cards skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="border border-neutral-border-light rounded-md p-5"
          >
            <div className="skeleton h-4 w-32 mb-3" />
            <div className="skeleton h-3 w-48 mb-2" />
            <div className="skeleton h-6 w-24 mb-3" />
            <div className="skeleton h-8 w-20" />
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function TaxPage() {
  const [summary, setSummary] = useState<TaxSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  // Create period form
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState({
    period_type: "VAT_MONTHLY",
    start_date: "",
    end_date: "",
  });
  const [creating, setCreating] = useState(false);

  // Mark filed dialog
  const [filingPeriodId, setFilingPeriodId] = useState<string | null>(null);
  const [filingRef, setFilingRef] = useState("");
  const [filingNotes, setFilingNotes] = useState("");
  const [filing, setFiling] = useState(false);

  // Computing state
  const [computingId, setComputingId] = useState<string | null>(null);

  useEffect(() => {
    loadSummary();
  }, []);

  async function loadSummary() {
    setLoading(true);
    setError("");
    try {
      const data = await getTaxSummary();
      setSummary(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load tax data");
      }
    } finally {
      setLoading(false);
    }
  }

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(""), 3000);
  }

  async function handleCreatePeriod(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError("");
    try {
      await createTaxPeriod({
        period_type: createForm.period_type,
        start_date: createForm.start_date,
        end_date: createForm.end_date,
      });
      setShowCreateForm(false);
      setCreateForm({ period_type: "VAT_MONTHLY", start_date: "", end_date: "" });
      showToast("Tax period created");
      await loadSummary();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to create period");
      }
    } finally {
      setCreating(false);
    }
  }

  async function handleCompute(periodId: string) {
    setComputingId(periodId);
    setError("");
    try {
      await computeTaxPeriod(periodId);
      showToast("Taxes computed successfully");
      await loadSummary();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to compute taxes");
      }
    } finally {
      setComputingId(null);
    }
  }

  async function handleMarkFiled() {
    if (!filingPeriodId) return;
    setFiling(true);
    setError("");
    try {
      await markPeriodFiled(filingPeriodId, filingRef || undefined, filingNotes || undefined);
      setFilingPeriodId(null);
      setFilingRef("");
      setFilingNotes("");
      showToast("Period marked as filed");
      await loadSummary();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to mark period as filed");
      }
    } finally {
      setFiling(false);
    }
  }

  // Auto-suggest: check if past months are missing VAT periods
  function getMissingSuggestion(): string | null {
    if (!summary) return null;
    const vatPeriods = summary.periods.filter(
      (p) => p.period_type === "VAT_MONTHLY"
    );
    if (vatPeriods.length > 0) return null;

    const now = new Date();
    const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    const lastMonthEnd = new Date(now.getFullYear(), now.getMonth(), 0);
    return `No VAT periods found. Consider creating one for ${lastMonth.toLocaleDateString(
      "en-GB",
      { month: "long", year: "numeric" }
    )} (${lastMonth.toISOString().split("T")[0]} to ${lastMonthEnd.toISOString().split("T")[0]}).`;
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (loading) {
    return (
      <div>
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-display font-bold text-xl text-neutral-text">
            Tax Obligations
          </h1>
        </div>
        <TaxSkeleton />
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div>
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-display font-bold text-xl text-neutral-text">
            Tax Obligations
          </h1>
        </div>
        <div className="text-center py-16">
          <p className="font-body text-neutral-muted mb-2">
            {error || "We couldn\u2019t load your tax data."}
          </p>
          <button
            onClick={loadSummary}
            className="font-display font-semibold text-sm bg-primary text-white px-6 py-2.5 rounded-sm hover:bg-primary-light transition-colors min-h-[44px]"
          >
            Tap to retry
          </button>
        </div>
      </div>
    );
  }

  const periods = summary?.periods ?? [];
  const totalOutstanding = summary?.total_outstanding_pesewas ?? 0;
  const nextDeadline = summary?.next_deadline ?? null;
  const suggestion = getMissingSuggestion();

  return (
    <div>
      {/* Toast */}
      {toast && (
        <div
          role="alert"
          className="fixed top-4 left-1/2 -translate-x-1/2 z-50 bg-success-bg text-success font-body text-sm px-5 py-2.5 rounded-sm shadow-lg flex items-center gap-2"
        >
          <span aria-hidden="true">&#10003;</span> {toast}
        </div>
      )}

      {/* Inline error banner */}
      {error && (
        <div
          role="alert"
          className="bg-danger-bg text-danger font-body text-sm p-3 rounded-sm mb-6"
        >
          {error}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-display font-bold text-xl text-neutral-text">
          Tax Obligations
        </h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="font-display font-semibold text-sm bg-primary text-white px-5 py-2.5 rounded-sm hover:bg-primary-light transition-colors min-h-[44px]"
          aria-label={showCreateForm ? "Cancel creating period" : "Create new tax period"}
        >
          {showCreateForm ? "Cancel" : "+ Create Period"}
        </button>
      </div>

      {/* Suggestion banner */}
      {suggestion && !showCreateForm && (
        <div className="bg-warning-bg border border-warning/20 text-warning font-body text-sm p-4 rounded-md mb-6">
          {suggestion}
        </div>
      )}

      {/* Create period form */}
      {showCreateForm && (
        <div className="bg-surface-raised border border-neutral-border-light rounded-md p-6 mb-8">
          <h2 className="font-display font-bold text-sm uppercase tracking-widest text-neutral-muted mb-5">
            New Tax Period
          </h2>
          <form onSubmit={handleCreatePeriod} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label
                  htmlFor="period-type"
                  className="block font-body text-sm font-medium text-neutral-secondary mb-1"
                >
                  Period Type
                </label>
                <select
                  id="period-type"
                  required
                  className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  value={createForm.period_type}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, period_type: e.target.value })
                  }
                >
                  <option value="VAT_MONTHLY">VAT (Monthly)</option>
                  <option value="CIT_ANNUAL">CIT (Annual)</option>
                  <option value="WHT_MONTHLY">WHT (Monthly)</option>
                </select>
              </div>
              <div>
                <label
                  htmlFor="period-start"
                  className="block font-body text-sm font-medium text-neutral-secondary mb-1"
                >
                  Start Date
                </label>
                <input
                  id="period-start"
                  type="date"
                  required
                  className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  value={createForm.start_date}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, start_date: e.target.value })
                  }
                />
              </div>
              <div>
                <label
                  htmlFor="period-end"
                  className="block font-body text-sm font-medium text-neutral-secondary mb-1"
                >
                  End Date
                </label>
                <input
                  id="period-end"
                  type="date"
                  required
                  className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  value={createForm.end_date}
                  onChange={(e) =>
                    setCreateForm({ ...createForm, end_date: e.target.value })
                  }
                />
              </div>
            </div>
            <button
              type="submit"
              disabled={creating}
              className="font-display font-semibold text-sm bg-primary text-white px-6 py-2.5 rounded-sm hover:bg-primary-light transition-colors disabled:opacity-50 min-h-[44px]"
            >
              {creating ? "Creating..." : "Create Period"}
            </button>
          </form>
        </div>
      )}

      {/* Hero card: Outstanding liability + next deadline */}
      <div className="text-center py-8 mb-8 border-b border-neutral-border-light">
        <p className="font-body text-sm text-neutral-muted mb-1">
          Total Outstanding Tax Liability
        </p>
        <p
          className={`font-mono font-semibold text-3xl sm:text-5xl tracking-tight ${
            totalOutstanding > 0 ? "text-accent" : "text-success"
          }`}
          aria-label={`Outstanding tax liability: ${formatGHS(totalOutstanding)} Ghana cedis`}
        >
          GHS {formatGHS(totalOutstanding)}
        </p>
        {nextDeadline && (
          <span className="inline-flex items-center gap-1.5 mt-3 font-body text-sm px-4 py-1 rounded-full bg-warning-bg text-warning">
            {(() => {
              const days = daysUntil(nextDeadline);
              if (days < 0)
                return `Overdue by ${Math.abs(days)} day${Math.abs(days) !== 1 ? "s" : ""}`;
              if (days === 0) return "Due today";
              return `${days} day${days !== 1 ? "s" : ""} until next deadline (${formatDate(nextDeadline)})`;
            })()}
          </span>
        )}
      </div>

      {/* Empty state */}
      {periods.length === 0 && (
        <div className="text-center py-16">
          <p className="font-display font-bold text-lg text-neutral-text mb-1">
            No tax periods yet
          </p>
          <p className="font-body text-neutral-muted mb-6">
            Create your first period to start tracking obligations.
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="font-display font-semibold text-sm bg-primary text-white px-6 py-2.5 rounded-sm hover:bg-primary-light transition-colors min-h-[44px]"
          >
            + Create Period
          </button>
        </div>
      )}

      {/* Period cards grid */}
      {periods.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {periods.map((period) => {
            const style = STATUS_STYLES[period.status] || STATUS_STYLES.DRAFT;
            const isDraft = period.status === "DRAFT";
            const isComputed =
              period.status === "COMPUTED" || period.status === "REVIEWED";
            const isFiled = period.status === "FILED";
            const isComputing = computingId === period.id;

            return (
              <div
                key={period.id}
                className="bg-surface-raised border border-neutral-border-light rounded-md p-5 flex flex-col gap-3"
              >
                {/* Top row: type + status */}
                <div className="flex items-center justify-between">
                  <span className="font-display font-bold text-sm text-neutral-text">
                    {PERIOD_TYPE_LABELS[period.period_type] || period.period_type}
                  </span>
                  <span
                    className={`inline-flex items-center font-display font-semibold text-xs uppercase tracking-wide px-2.5 py-0.5 rounded-sm ${style.bg} ${style.text}`}
                    role="status"
                    aria-label={`Status: ${style.label}`}
                  >
                    {style.label}
                  </span>
                </div>

                {/* Date range */}
                <p className="font-body text-sm text-neutral-muted">
                  {formatDate(period.start_date)} &ndash;{" "}
                  {formatDate(period.end_date)}
                </p>

                {/* Amount */}
                {!isDraft && (
                  <p
                    className="font-mono text-lg font-semibold text-neutral-text"
                    aria-label={`Computed liability: ${formatGHS(period.total_liability_pesewas)} Ghana cedis`}
                  >
                    GHS {formatGHS(period.total_liability_pesewas)}
                  </p>
                )}

                {/* Actions */}
                <div className="flex flex-wrap items-center gap-2 mt-auto pt-2 border-t border-neutral-border-light">
                  <Link
                    href={`/tax/${period.id}`}
                    className="font-display font-semibold text-xs text-primary hover:text-primary-light transition-colors min-h-[44px] flex items-center px-3 border border-neutral-border rounded-sm hover:border-primary"
                    aria-label={`View details for ${PERIOD_TYPE_LABELS[period.period_type]} period`}
                  >
                    View Details
                  </Link>

                  {isDraft && (
                    <button
                      onClick={() => handleCompute(period.id)}
                      disabled={isComputing}
                      className="font-display font-semibold text-xs bg-primary text-white px-3 rounded-sm hover:bg-primary-light transition-colors disabled:opacity-50 min-h-[44px]"
                      aria-label={`Compute taxes for ${PERIOD_TYPE_LABELS[period.period_type]} period`}
                    >
                      {isComputing ? "Computing..." : "Compute"}
                    </button>
                  )}

                  {isComputed && !isFiled && (
                    <button
                      onClick={() => setFilingPeriodId(period.id)}
                      className="font-display font-semibold text-xs bg-success text-white px-3 rounded-sm hover:opacity-90 transition-colors min-h-[44px]"
                      aria-label={`Mark ${PERIOD_TYPE_LABELS[period.period_type]} period as filed`}
                    >
                      Mark Filed
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Mark Filed confirmation dialog */}
      {filingPeriodId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={() => {
            setFilingPeriodId(null);
            setFilingRef("");
            setFilingNotes("");
          }}
        >
          <div
            className="bg-surface-raised rounded-lg shadow-xl p-6 max-w-sm w-full mx-4"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-labelledby="filing-dialog-title"
            aria-modal="true"
          >
            <h2
              id="filing-dialog-title"
              className="font-display font-bold text-lg text-neutral-text mb-2"
            >
              Mark as Filed
            </h2>
            <p className="font-body text-sm text-neutral-muted mb-4">
              Confirm that this tax period has been filed with GRA. This action
              cannot be undone.
            </p>
            <div className="space-y-3 mb-6">
              <div>
                <label
                  htmlFor="filing-ref"
                  className="block font-body text-sm font-medium text-neutral-secondary mb-1"
                >
                  Filing Reference (optional)
                </label>
                <input
                  id="filing-ref"
                  type="text"
                  maxLength={200}
                  className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="e.g. GRA-2026-0001"
                  value={filingRef}
                  onChange={(e) => setFilingRef(e.target.value)}
                />
              </div>
              <div>
                <label
                  htmlFor="filing-notes"
                  className="block font-body text-sm font-medium text-neutral-secondary mb-1"
                >
                  Notes (optional)
                </label>
                <input
                  id="filing-notes"
                  type="text"
                  maxLength={500}
                  className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="Additional notes"
                  value={filingNotes}
                  onChange={(e) => setFilingNotes(e.target.value)}
                />
              </div>
            </div>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  setFilingPeriodId(null);
                  setFilingRef("");
                  setFilingNotes("");
                }}
                className="font-display font-semibold text-sm px-4 py-2 rounded-sm border border-neutral-border text-neutral-secondary hover:border-primary hover:text-primary transition-colors min-h-[44px]"
              >
                Cancel
              </button>
              <button
                onClick={handleMarkFiled}
                disabled={filing}
                className="font-display font-semibold text-sm px-4 py-2 rounded-sm bg-success text-white hover:opacity-90 transition-colors disabled:opacity-50 min-h-[44px]"
              >
                {filing ? "Filing..." : "Confirm Filed"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
