"use client";

import { useEffect, useState } from "react";
import { getProfitLoss, getProfitLossTrend, pesewasToCedis } from "@/lib/api";

function formatGHS(pesewas: number): string {
  const cedis = pesewas / 100;
  return cedis.toLocaleString("en-GH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function PnLSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="text-center py-10 mb-8">
        <div className="skeleton h-4 w-40 mx-auto mb-3" />
        <div className="skeleton h-12 w-64 mx-auto mb-3" />
        <div className="skeleton h-6 w-72 mx-auto rounded-full" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <div className="skeleton h-4 w-24 mb-4" />
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex justify-between py-2">
              <div className="skeleton h-4 w-32" />
              <div className="skeleton h-4 w-20" />
            </div>
          ))}
        </div>
        <div>
          <div className="skeleton h-4 w-24 mb-4" />
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex justify-between py-2">
              <div className="skeleton h-4 w-32" />
              <div className="skeleton h-4 w-20" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  const [report, setReport] = useState<any>(null);
  const [trend, setTrend] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [dateFrom, setDateFrom] = useState(
    new Date(new Date().getFullYear(), new Date().getMonth(), 1)
      .toISOString()
      .split("T")[0]
  );
  const [dateTo, setDateTo] = useState(
    new Date().toISOString().split("T")[0]
  );

  useEffect(() => {
    loadReport();
  }, [dateFrom, dateTo]);

  async function loadReport() {
    setLoading(true);
    setError(false);
    try {
      const [pnl, trendData] = await Promise.all([
        getProfitLoss(dateFrom, dateTo),
        getProfitLossTrend(6),
      ]);
      setReport(pnl);
      setTrend(trendData.trend || []);
    } catch (err) {
      setError(true);
      setReport(null);
      setTrend([]);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div>
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-display font-bold text-xl text-neutral-text">
            Profit &amp; Loss
          </h1>
        </div>
        <PnLSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-display font-bold text-xl text-neutral-text">
            Profit &amp; Loss
          </h1>
        </div>
        <div className="text-center py-16">
          <p className="font-body text-neutral-muted mb-2">
            We couldn&apos;t load your report.
          </p>
          <button
            onClick={loadReport}
            className="font-display font-semibold text-sm bg-primary text-white px-6 py-2.5 rounded-sm hover:bg-primary-light transition-colors"
          >
            Tap to retry
          </button>
        </div>
      </div>
    );
  }

  const netIncome = report?.net_income_pesewas ?? 0;
  const isProfit = netIncome >= 0;
  const hasRevenue = (report?.revenue?.items?.length ?? 0) > 0;
  const hasExpenses = (report?.expenses?.items?.length ?? 0) > 0;
  const isEmpty = !hasRevenue && !hasExpenses;

  if (isEmpty && !loading) {
    const biz = typeof window !== "undefined"
      ? JSON.parse(localStorage.getItem("business") || "{}")
      : {};
    return (
      <div>
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-display font-bold text-xl text-neutral-text">
            Profit &amp; Loss
          </h1>
        </div>
        <div className="text-center py-16">
          <p className="font-display font-bold text-lg text-neutral-text mb-1">
            Welcome{biz.legal_name ? `, ${biz.legal_name}` : ""}!
          </p>
          <p className="font-body text-neutral-muted mb-6">
            Add your first transaction to see your business come alive.
          </p>
          <a
            href="/transactions"
            className="inline-block font-display font-semibold text-sm bg-primary text-white px-6 py-2.5 rounded-sm hover:bg-primary-light transition-colors"
          >
            Add a transaction
          </a>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header + date presets + date range */}
      <div className="flex flex-col gap-3 mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h1 className="font-display font-bold text-xl text-neutral-text">
            Profit &amp; Loss
          </h1>
          <div className="flex items-center gap-2">
            <input
              type="date"
              aria-label="Start date"
              className="font-body text-sm border border-neutral-border rounded-sm px-3 py-2 bg-surface-raised text-neutral-text focus:outline-none focus:ring-2 focus:ring-primary"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
            <span className="text-neutral-faint text-sm">to</span>
            <input
              type="date"
              aria-label="End date"
              className="font-body text-sm border border-neutral-border rounded-sm px-3 py-2 bg-surface-raised text-neutral-text focus:outline-none focus:ring-2 focus:ring-primary"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
        </div>
        <div className="flex gap-2 flex-wrap">
          {[
            { label: "This Month", from: new Date(new Date().getFullYear(), new Date().getMonth(), 1), to: new Date() },
            { label: "Last Month", from: new Date(new Date().getFullYear(), new Date().getMonth() - 1, 1), to: new Date(new Date().getFullYear(), new Date().getMonth(), 0) },
            { label: "This Quarter", from: new Date(new Date().getFullYear(), Math.floor(new Date().getMonth() / 3) * 3, 1), to: new Date() },
            { label: "This Year", from: new Date(new Date().getFullYear(), 0, 1), to: new Date() },
          ].map((preset) => {
            const f = preset.from.toISOString().split("T")[0];
            const t = preset.to.toISOString().split("T")[0];
            const isActive = dateFrom === f && dateTo === t;
            return (
              <button
                key={preset.label}
                onClick={() => { setDateFrom(f); setDateTo(t); }}
                className={`font-body text-xs px-3 py-1.5 rounded-sm border transition-colors min-h-[32px] ${
                  isActive
                    ? "bg-primary text-white border-primary"
                    : "bg-surface-raised text-neutral-muted border-neutral-border hover:border-primary hover:text-primary"
                }`}
              >
                {preset.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* NET INCOME HERO */}
      <div className="text-center py-8 mb-8 border-b border-neutral-border-light">
        <p className="font-body text-sm text-neutral-muted mb-1">
          Net Income
        </p>
        <p
          className={`font-mono font-semibold text-3xl sm:text-5xl tracking-tight ${
            isProfit ? "text-success" : "text-danger"
          }`}
          aria-label={`Net income: ${formatGHS(Math.abs(netIncome))} Ghana cedis`}
        >
          {isProfit ? "" : "-"}GHS {formatGHS(Math.abs(netIncome))}
        </p>
        <span
          className={`inline-flex items-center gap-1.5 mt-3 font-body text-sm px-4 py-1 rounded-full ${
            isProfit
              ? "text-success bg-success-bg"
              : "text-danger bg-danger-bg"
          }`}
        >
          {isProfit ? "▲" : "▼"}{" "}
          {isProfit
            ? "You earned more than you spent this period"
            : "Your expenses exceeded your income"}
        </span>
      </div>

      {/* Revenue & Expenses — dense data rows */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        {/* Revenue */}
        <div>
          <h2 className="font-display font-bold text-xs uppercase tracking-widest text-neutral-muted mb-4 pb-2 border-b-2 border-neutral-border-light">
            Revenue
          </h2>
          {report?.revenue?.items?.map((item: any) => (
            <div
              key={item.account_code}
              className="flex justify-between items-baseline py-2 border-b border-neutral-border-light last:border-b-0"
            >
              <span className="font-body text-sm text-neutral-secondary">
                {item.account_name}
              </span>
              <span className="font-mono text-sm text-success">
                {formatGHS(item.total_pesewas)}
              </span>
            </div>
          ))}
          <div className="flex justify-between items-baseline pt-3 mt-1 border-t-2 border-neutral-text">
            <span className="font-display font-bold text-sm">
              Total Revenue
            </span>
            <span className="font-mono font-semibold text-base text-success">
              {formatGHS(report?.revenue?.total_pesewas ?? 0)}
            </span>
          </div>
        </div>

        {/* Expenses */}
        <div>
          <h2 className="font-display font-bold text-xs uppercase tracking-widest text-neutral-muted mb-4 pb-2 border-b-2 border-neutral-border-light">
            Expenses
          </h2>
          {report?.expenses?.items?.map((item: any) => (
            <div
              key={item.account_code}
              className="flex justify-between items-baseline py-2 border-b border-neutral-border-light last:border-b-0"
            >
              <span className="font-body text-sm text-neutral-secondary">
                {item.account_name}
              </span>
              <span className="font-mono text-sm text-danger">
                {formatGHS(item.total_pesewas)}
              </span>
            </div>
          ))}
          <div className="flex justify-between items-baseline pt-3 mt-1 border-t-2 border-neutral-text">
            <span className="font-display font-bold text-sm">
              Total Expenses
            </span>
            <span className="font-mono font-semibold text-base text-danger">
              {formatGHS(report?.expenses?.total_pesewas ?? 0)}
            </span>
          </div>
        </div>
      </div>

      {/* Monthly Trend */}
      {trend.length > 0 && (
        <div>
          <h2 className="font-display font-bold text-xs uppercase tracking-widest text-neutral-muted mb-4 pb-2 border-b-2 border-neutral-border-light">
            Monthly Trend
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full font-body text-sm">
              <thead>
                <tr className="border-b border-neutral-border">
                  <th className="text-left py-2 font-semibold text-neutral-secondary">
                    Month
                  </th>
                  <th className="text-right py-2 font-semibold text-neutral-secondary">
                    Revenue
                  </th>
                  <th className="text-right py-2 font-semibold text-neutral-secondary">
                    Expenses
                  </th>
                  <th className="text-right py-2 font-semibold text-neutral-secondary">
                    Net Income
                  </th>
                </tr>
              </thead>
              <tbody>
                {trend.map((m) => (
                  <tr
                    key={m.month}
                    className="border-b border-neutral-border-light last:border-b-0"
                  >
                    <td className="py-2.5 text-neutral-secondary">
                      {m.month}
                    </td>
                    <td className="py-2.5 text-right font-mono text-success">
                      {formatGHS(m.income_pesewas)}
                    </td>
                    <td className="py-2.5 text-right font-mono text-danger">
                      {formatGHS(m.expense_pesewas)}
                    </td>
                    <td
                      className={`py-2.5 text-right font-mono font-medium ${
                        m.net_income_pesewas >= 0
                          ? "text-success"
                          : "text-danger"
                      }`}
                    >
                      {formatGHS(m.net_income_pesewas)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
