"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  getTaxPeriods,
  computeTaxPeriod,
  getVATReport,
  getCITReport,
  markPeriodFiled,
  ApiError,
  type TaxPeriod,
  type VATReport,
  type CITReport,
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

const PERIOD_TYPE_LABELS: Record<string, string> = {
  VAT_MONTHLY: "VAT (Monthly)",
  CIT_ANNUAL: "CIT (Annual)",
  WHT_MONTHLY: "WHT (Monthly)",
};

const STATUS_STYLES: Record<
  string,
  { bg: string; text: string; label: string }
> = {
  DRAFT: { bg: "bg-surface-alt", text: "text-neutral-muted", label: "Draft" },
  COMPUTED: { bg: "bg-info-bg", text: "text-info", label: "Computed" },
  REVIEWED: { bg: "bg-warning-bg", text: "text-warning", label: "Reviewed" },
  FILED: { bg: "bg-success-bg", text: "text-success", label: "Filed" },
};

const TIMELINE_STEPS = ["DRAFT", "COMPUTED", "REVIEWED", "FILED"] as const;

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

function DetailSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="skeleton h-6 w-48 mb-2" />
      <div className="skeleton h-4 w-64 mb-8" />
      <div className="skeleton h-4 w-32 mb-4" />
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex justify-between py-2">
          <div className="skeleton h-4 w-40" />
          <div className="skeleton h-4 w-24" />
          <div className="skeleton h-4 w-16" />
          <div className="skeleton h-4 w-24" />
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Computation breakdown rows for VAT report
// ---------------------------------------------------------------------------

interface BreakdownRow {
  label: string;
  basePesewas: number | null;
  rate: string;
  amountPesewas: number;
  isTotal?: boolean;
}

function vatBreakdownRows(report: VATReport): BreakdownRow[] {
  return [
    {
      label: "Taxable Sales",
      basePesewas: report.taxable_sales_pesewas,
      rate: "",
      amountPesewas: report.output_vat_pesewas,
    },
    {
      label: "Less: Input VAT (Purchases)",
      basePesewas: report.taxable_purchases_pesewas,
      rate: "",
      amountPesewas: -report.input_vat_pesewas,
    },
    {
      label: "Net VAT Payable",
      basePesewas: null,
      rate: "",
      amountPesewas: report.net_vat_payable_pesewas,
    },
    {
      label: "NHIL",
      basePesewas: null,
      rate: "",
      amountPesewas: report.nhil_pesewas,
    },
    {
      label: "GETFund Levy",
      basePesewas: null,
      rate: "",
      amountPesewas: report.getfund_pesewas,
    },
    {
      label: "Total Payable",
      basePesewas: null,
      rate: "",
      amountPesewas: report.total_payable_pesewas,
      isTotal: true,
    },
  ];
}

function citBreakdownRows(report: CITReport): BreakdownRow[] {
  const ratePct = (report.cit_rate_bps / 100).toFixed(2) + "%";
  return [
    {
      label: "Total Revenue",
      basePesewas: null,
      rate: "",
      amountPesewas: report.total_revenue_pesewas,
    },
    {
      label: "Less: Deductible Expenses",
      basePesewas: null,
      rate: "",
      amountPesewas: -report.total_deductible_expenses_pesewas,
    },
    {
      label: "Non-Deductible Expenses (reference)",
      basePesewas: null,
      rate: "",
      amountPesewas: report.non_deductible_expenses_pesewas,
    },
    {
      label: "Net Profit / (Loss)",
      basePesewas: null,
      rate: "",
      amountPesewas: report.net_profit_pesewas,
    },
    {
      label: "CIT Liability",
      basePesewas: report.net_profit_pesewas,
      rate: ratePct,
      amountPesewas: report.cit_liability_pesewas,
      isTotal: true,
    },
  ];
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function TaxPeriodDetailPage() {
  const params = useParams();
  const router = useRouter();
  const periodId = params.periodId as string;

  const [period, setPeriod] = useState<TaxPeriod | null>(null);
  const [vatReport, setVatReport] = useState<VATReport | null>(null);
  const [citReport, setCitReport] = useState<CITReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  // Filing dialog
  const [showFilingDialog, setShowFilingDialog] = useState(false);
  const [filingRef, setFilingRef] = useState("");
  const [filingNotes, setFilingNotes] = useState("");
  const [filing, setFiling] = useState(false);

  // Computing
  const [computing, setComputing] = useState(false);

  useEffect(() => {
    loadPeriod();
  }, [periodId]);

  async function loadPeriod() {
    setLoading(true);
    setError("");
    try {
      // Fetch all periods and find the right one (no single-period endpoint)
      const periods = await getTaxPeriods();
      const found = periods.find((p) => p.id === periodId);
      if (!found) {
        setError("Tax period not found");
        setLoading(false);
        return;
      }
      setPeriod(found);

      // If computed+, load the appropriate report
      if (found.status !== "DRAFT") {
        if (
          found.period_type === "VAT_MONTHLY" ||
          found.period_type === "WHT_MONTHLY"
        ) {
          try {
            const vat = await getVATReport(periodId);
            setVatReport(vat);
          } catch {
            // Report may not be available for WHT
          }
        }
        if (found.period_type === "CIT_ANNUAL") {
          try {
            const cit = await getCITReport(periodId);
            setCitReport(cit);
          } catch {
            // Ignore if not available
          }
        }
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to load tax period");
      }
    } finally {
      setLoading(false);
    }
  }

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(""), 3000);
  }

  async function handleCompute() {
    setComputing(true);
    setError("");
    try {
      await computeTaxPeriod(periodId);
      showToast("Taxes computed successfully");
      await loadPeriod();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError("Failed to compute taxes");
    } finally {
      setComputing(false);
    }
  }

  async function handleMarkFiled() {
    setFiling(true);
    setError("");
    try {
      await markPeriodFiled(
        periodId,
        filingRef || undefined,
        filingNotes || undefined
      );
      setShowFilingDialog(false);
      setFilingRef("");
      setFilingNotes("");
      showToast("Period marked as filed");
      await loadPeriod();
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError("Failed to mark as filed");
    } finally {
      setFiling(false);
    }
  }

  function exportCSV(rows: BreakdownRow[], filename: string) {
    const header = "Item,Base Amount (GHS),Rate,Amount (GHS)\n";
    const csvRows = rows
      .map((r) => {
        const base = r.basePesewas !== null ? (r.basePesewas / 100).toFixed(2) : "";
        const amount = (r.amountPesewas / 100).toFixed(2);
        return `"${r.label}",${base},${r.rate},${amount}`;
      })
      .join("\n");
    const blob = new Blob([header + csvRows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  if (loading) {
    return (
      <div>
        <Link
          href="/tax"
          className="inline-flex items-center gap-1 font-body text-sm text-primary hover:text-primary-light transition-colors mb-6 min-h-[44px]"
        >
          <span aria-hidden="true">&larr;</span> Back to Tax Overview
        </Link>
        <DetailSkeleton />
      </div>
    );
  }

  if (error && !period) {
    return (
      <div>
        <Link
          href="/tax"
          className="inline-flex items-center gap-1 font-body text-sm text-primary hover:text-primary-light transition-colors mb-6 min-h-[44px]"
        >
          <span aria-hidden="true">&larr;</span> Back to Tax Overview
        </Link>
        <div className="text-center py-16">
          <p className="font-body text-neutral-muted mb-2">{error}</p>
          <button
            onClick={loadPeriod}
            className="font-display font-semibold text-sm bg-primary text-white px-6 py-2.5 rounded-sm hover:bg-primary-light transition-colors min-h-[44px]"
          >
            Tap to retry
          </button>
        </div>
      </div>
    );
  }

  if (!period) return null;

  const style = STATUS_STYLES[period.status] || STATUS_STYLES.DRAFT;
  const isDraft = period.status === "DRAFT";
  const isComputed = period.status === "COMPUTED" || period.status === "REVIEWED";
  const breakdownRows = vatReport
    ? vatBreakdownRows(vatReport)
    : citReport
      ? citBreakdownRows(citReport)
      : [];

  // Timeline: determine which step is active
  const currentStepIndex = TIMELINE_STEPS.indexOf(
    period.status as (typeof TIMELINE_STEPS)[number]
  );

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

      {/* Error */}
      {error && (
        <div
          role="alert"
          className="bg-danger-bg text-danger font-body text-sm p-3 rounded-sm mb-6"
        >
          {error}
        </div>
      )}

      {/* Back link */}
      <Link
        href="/tax"
        className="inline-flex items-center gap-1 font-body text-sm text-primary hover:text-primary-light transition-colors mb-6 min-h-[44px]"
      >
        <span aria-hidden="true">&larr;</span> Back to Tax Overview
      </Link>

      {/* Period header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-8">
        <div>
          <h1 className="font-display font-bold text-xl text-neutral-text">
            {PERIOD_TYPE_LABELS[period.period_type] || period.period_type}
          </h1>
          <p className="font-body text-sm text-neutral-muted mt-1">
            {formatDate(period.start_date)} &ndash;{" "}
            {formatDate(period.end_date)}
          </p>
        </div>
        <span
          className={`inline-flex items-center self-start font-display font-semibold text-xs uppercase tracking-wide px-3 py-1 rounded-sm ${style.bg} ${style.text}`}
          role="status"
          aria-label={`Status: ${style.label}`}
        >
          {style.label}
        </span>
      </div>

      {/* Filing status timeline */}
      <div className="mb-8" aria-label="Filing progress timeline">
        <div className="flex items-center justify-between max-w-md mx-auto">
          {TIMELINE_STEPS.map((step, idx) => {
            const isCompleted = idx <= currentStepIndex;
            const isCurrent = idx === currentStepIndex;
            const isLast = idx === TIMELINE_STEPS.length - 1;
            const stepStyle = STATUS_STYLES[step];

            return (
              <div key={step} className="flex items-center flex-1 last:flex-none">
                <div className="flex flex-col items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors ${
                      isCompleted
                        ? isCurrent
                          ? `${stepStyle.bg} border-primary`
                          : "bg-success-bg border-success"
                        : "bg-surface-alt border-neutral-border"
                    }`}
                    aria-label={`${stepStyle.label}${isCurrent ? " (current)" : isCompleted ? " (completed)" : ""}`}
                  >
                    {isCompleted && !isCurrent && (
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="text-success"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    )}
                    {isCurrent && (
                      <div className="w-2.5 h-2.5 rounded-full bg-primary" />
                    )}
                  </div>
                  <span
                    className={`font-body text-[10px] mt-1.5 ${
                      isCompleted ? "text-neutral-text font-medium" : "text-neutral-faint"
                    }`}
                  >
                    {stepStyle.label}
                  </span>
                </div>
                {!isLast && (
                  <div
                    className={`flex-1 h-0.5 mx-1 mt-[-18px] ${
                      idx < currentStepIndex
                        ? "bg-success"
                        : "bg-neutral-border-light"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Computation breakdown table */}
      {breakdownRows.length > 0 && (
        <div className="mb-8">
          <h2 className="font-display font-bold text-xs uppercase tracking-widest text-neutral-muted mb-4 pb-2 border-b-2 border-neutral-border-light">
            Computation Breakdown
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full font-body text-sm">
              <thead>
                <tr className="border-b border-neutral-border">
                  <th className="text-left py-2 font-semibold text-neutral-secondary">
                    Item
                  </th>
                  <th className="text-right py-2 font-semibold text-neutral-secondary">
                    Base Amount
                  </th>
                  <th className="text-right py-2 font-semibold text-neutral-secondary">
                    Rate
                  </th>
                  <th className="text-right py-2 font-semibold text-neutral-secondary">
                    Amount
                  </th>
                </tr>
              </thead>
              <tbody>
                {breakdownRows.map((row, idx) => (
                  <tr
                    key={idx}
                    className={
                      row.isTotal
                        ? "border-t-2 border-neutral-text"
                        : "border-b border-neutral-border-light"
                    }
                  >
                    <td
                      className={`py-2.5 text-neutral-secondary ${
                        row.isTotal ? "font-display font-bold text-neutral-text" : ""
                      }`}
                    >
                      {row.label}
                    </td>
                    <td className="py-2.5 text-right font-mono">
                      {row.basePesewas !== null
                        ? `GHS ${formatGHS(row.basePesewas)}`
                        : "\u2014"}
                    </td>
                    <td className="py-2.5 text-right font-mono">
                      {row.rate || "\u2014"}
                    </td>
                    <td
                      className={`py-2.5 text-right font-mono ${
                        row.isTotal ? "font-semibold text-neutral-text" : ""
                      } ${row.amountPesewas < 0 ? "text-danger" : ""}`}
                    >
                      {row.amountPesewas < 0 ? "-" : ""}GHS{" "}
                      {formatGHS(Math.abs(row.amountPesewas))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Draft state: no breakdown yet */}
      {isDraft && (
        <div className="text-center py-12 border border-neutral-border-light rounded-md mb-8">
          <p className="font-body text-neutral-muted mb-4">
            Taxes have not been computed for this period yet.
          </p>
          <button
            onClick={handleCompute}
            disabled={computing}
            className="font-display font-semibold text-sm bg-primary text-white px-6 py-2.5 rounded-sm hover:bg-primary-light transition-colors disabled:opacity-50 min-h-[44px]"
          >
            {computing ? "Computing..." : "Compute Taxes"}
          </button>
        </div>
      )}

      {/* Actions */}
      {!isDraft && (
        <div className="flex flex-wrap gap-3">
          {breakdownRows.length > 0 && (
            <button
              onClick={() => {
                const type = period.period_type.toLowerCase().replace("_", "-");
                exportCSV(
                  breakdownRows,
                  `bizpulse-${type}-${period.start_date}-to-${period.end_date}.csv`
                );
              }}
              className="font-display font-semibold text-sm bg-surface-raised text-neutral-secondary border border-neutral-border px-4 py-2.5 rounded-sm hover:border-primary hover:text-primary transition-colors min-h-[44px]"
              aria-label="Export report as CSV"
            >
              Export CSV
            </button>
          )}

          {isComputed && (
            <button
              onClick={() => setShowFilingDialog(true)}
              className="font-display font-semibold text-sm bg-success text-white px-4 py-2.5 rounded-sm hover:opacity-90 transition-colors min-h-[44px]"
              aria-label="Mark this period as filed with GRA"
            >
              Mark Filed
            </button>
          )}
        </div>
      )}

      {/* Mark Filed dialog */}
      {showFilingDialog && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={() => {
            setShowFilingDialog(false);
            setFilingRef("");
            setFilingNotes("");
          }}
        >
          <div
            className="bg-surface-raised rounded-lg shadow-xl p-6 max-w-sm w-full mx-4"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-labelledby="filing-dialog-title-detail"
            aria-modal="true"
          >
            <h2
              id="filing-dialog-title-detail"
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
                  htmlFor="detail-filing-ref"
                  className="block font-body text-sm font-medium text-neutral-secondary mb-1"
                >
                  Filing Reference (optional)
                </label>
                <input
                  id="detail-filing-ref"
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
                  htmlFor="detail-filing-notes"
                  className="block font-body text-sm font-medium text-neutral-secondary mb-1"
                >
                  Notes (optional)
                </label>
                <input
                  id="detail-filing-notes"
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
                  setShowFilingDialog(false);
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
