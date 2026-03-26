"use client";

import { useState } from "react";
import {
  cedisToPesewas,
  generateInvoicePreview,
  ApiError,
} from "@/lib/api";

function formatGHS(pesewas: number): string {
  const cedis = pesewas / 100;
  return cedis.toLocaleString("en-GH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

interface LineItem {
  id: string;
  description: string;
  quantity: string;
  unit_price_cedis: string;
  vat_applicable: boolean;
}

function newLineItem(): LineItem {
  return {
    id: crypto.randomUUID(),
    description: "",
    quantity: "1",
    unit_price_cedis: "",
    vat_applicable: true,
  };
}

// Default VAT rate for client-side preview (15% standard rate)
const VAT_RATE = 0.15;

export default function InvoicesPage() {
  const [customerName, setCustomerName] = useState("");
  const [customerTin, setCustomerTin] = useState("");
  const [notes, setNotes] = useState("");
  const [lineItems, setLineItems] = useState<LineItem[]>([newLineItem()]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(""), 3000);
  }

  function updateLineItem(id: string, updates: Partial<LineItem>) {
    setLineItems((items) =>
      items.map((item) => (item.id === id ? { ...item, ...updates } : item))
    );
  }

  function removeLineItem(id: string) {
    setLineItems((items) => items.filter((item) => item.id !== id));
  }

  function addLineItem() {
    setLineItems((items) => [...items, newLineItem()]);
  }

  // Compute totals client-side
  function computeTotals() {
    let subtotalPesewas = 0;
    let vatTotalPesewas = 0;

    for (const item of lineItems) {
      const qty = parseFloat(item.quantity) || 0;
      const unitPricePesewas = cedisToPesewas(
        parseFloat(item.unit_price_cedis) || 0
      );
      const lineSubtotal = Math.round(qty * unitPricePesewas);
      subtotalPesewas += lineSubtotal;

      if (item.vat_applicable) {
        vatTotalPesewas += Math.round(lineSubtotal * VAT_RATE);
      }
    }

    return {
      subtotalPesewas,
      vatTotalPesewas,
      grandTotalPesewas: subtotalPesewas + vatTotalPesewas,
    };
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    // Validate at least one line item with values
    const validItems = lineItems.filter(
      (item) =>
        item.description.trim() &&
        parseFloat(item.quantity) > 0 &&
        parseFloat(item.unit_price_cedis) > 0
    );

    if (validItems.length === 0) {
      setError("Add at least one line item with description, quantity, and price.");
      return;
    }

    if (!customerName.trim()) {
      setError("Customer name is required.");
      return;
    }

    setGenerating(true);
    try {
      const blob = await generateInvoicePreview({
        customer_name: customerName.trim(),
        customer_tin: customerTin.trim() || undefined,
        line_items: validItems.map((item) => ({
          description: item.description.trim(),
          quantity: parseFloat(item.quantity),
          unit_price_pesewas: cedisToPesewas(
            parseFloat(item.unit_price_cedis)
          ),
          vat_applicable: item.vat_applicable,
        })),
        notes: notes.trim() || undefined,
      });

      // Open PDF in new tab
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
      showToast("Invoice PDF generated");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to generate invoice. The service may be unavailable.");
      }
    } finally {
      setGenerating(false);
    }
  }

  const { subtotalPesewas, vatTotalPesewas, grandTotalPesewas } =
    computeTotals();

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

      <div className="flex items-center justify-between mb-8">
        <h1 className="font-display font-bold text-xl text-neutral-text">
          Invoice Preview
        </h1>
      </div>

      {error && (
        <div
          role="alert"
          className="bg-danger-bg text-danger font-body text-sm p-3 rounded-sm mb-6"
        >
          {error}
        </div>
      )}

      <form onSubmit={handleGenerate}>
        {/* Customer info */}
        <div className="bg-surface-raised border border-neutral-border-light rounded-md p-6 mb-6">
          <h2 className="font-display font-bold text-sm uppercase tracking-widest text-neutral-muted mb-5">
            Customer Details
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="customer-name"
                className="block font-body text-sm font-medium text-neutral-secondary mb-1"
              >
                Customer Name
              </label>
              <input
                id="customer-name"
                type="text"
                required
                maxLength={200}
                className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Customer or company name"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
              />
            </div>
            <div>
              <label
                htmlFor="customer-tin"
                className="block font-body text-sm font-medium text-neutral-secondary mb-1"
              >
                Customer TIN (optional)
              </label>
              <input
                id="customer-tin"
                type="text"
                maxLength={50}
                className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Tax Identification Number"
                value={customerTin}
                onChange={(e) => setCustomerTin(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Line items */}
        <div className="bg-surface-raised border border-neutral-border-light rounded-md p-6 mb-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-display font-bold text-sm uppercase tracking-widest text-neutral-muted">
              Line Items
            </h2>
            <button
              type="button"
              onClick={addLineItem}
              className="font-display font-semibold text-xs text-primary hover:text-primary-light transition-colors min-h-[44px] px-3 border border-neutral-border rounded-sm hover:border-primary"
              aria-label="Add another line item"
            >
              + Add Item
            </button>
          </div>

          {/* Desktop header */}
          <div className="hidden sm:grid sm:grid-cols-[1fr_80px_120px_60px_40px] gap-3 mb-2">
            <span className="font-body text-xs font-semibold text-neutral-muted uppercase tracking-widest">
              Description
            </span>
            <span className="font-body text-xs font-semibold text-neutral-muted uppercase tracking-widest">
              Qty
            </span>
            <span className="font-body text-xs font-semibold text-neutral-muted uppercase tracking-widest">
              Unit Price (GHS)
            </span>
            <span className="font-body text-xs font-semibold text-neutral-muted uppercase tracking-widest text-center">
              VAT
            </span>
            <span className="sr-only">Remove</span>
          </div>

          <div className="space-y-3">
            {lineItems.map((item, idx) => (
              <div
                key={item.id}
                className="grid grid-cols-1 sm:grid-cols-[1fr_80px_120px_60px_40px] gap-3 items-start border-b border-neutral-border-light pb-3 last:border-b-0 last:pb-0"
              >
                {/* Description */}
                <div>
                  <label
                    htmlFor={`desc-${item.id}`}
                    className="sm:hidden block font-body text-xs font-medium text-neutral-muted mb-1"
                  >
                    Description
                  </label>
                  <input
                    id={`desc-${item.id}`}
                    type="text"
                    required
                    maxLength={300}
                    className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="Item description"
                    value={item.description}
                    onChange={(e) =>
                      updateLineItem(item.id, { description: e.target.value })
                    }
                  />
                </div>

                {/* Quantity */}
                <div>
                  <label
                    htmlFor={`qty-${item.id}`}
                    className="sm:hidden block font-body text-xs font-medium text-neutral-muted mb-1"
                  >
                    Qty
                  </label>
                  <input
                    id={`qty-${item.id}`}
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    className="w-full font-mono text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="1"
                    value={item.quantity}
                    onChange={(e) =>
                      updateLineItem(item.id, { quantity: e.target.value })
                    }
                  />
                </div>

                {/* Unit price */}
                <div>
                  <label
                    htmlFor={`price-${item.id}`}
                    className="sm:hidden block font-body text-xs font-medium text-neutral-muted mb-1"
                  >
                    Unit Price (GHS)
                  </label>
                  <input
                    id={`price-${item.id}`}
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    className="w-full font-mono text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                    placeholder="0.00"
                    value={item.unit_price_cedis}
                    onChange={(e) =>
                      updateLineItem(item.id, {
                        unit_price_cedis: e.target.value,
                      })
                    }
                  />
                </div>

                {/* VAT checkbox */}
                <div className="flex items-center justify-center min-h-[44px]">
                  <label className="sm:hidden font-body text-xs font-medium text-neutral-muted mr-2">
                    VAT
                  </label>
                  <input
                    type="checkbox"
                    checked={item.vat_applicable}
                    onChange={(e) =>
                      updateLineItem(item.id, {
                        vat_applicable: e.target.checked,
                      })
                    }
                    className="w-5 h-5 rounded border-neutral-border text-primary focus:ring-primary cursor-pointer"
                    aria-label={`VAT applicable for item ${idx + 1}`}
                  />
                </div>

                {/* Remove button */}
                <div className="flex items-center justify-center min-h-[44px]">
                  {lineItems.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeLineItem(item.id)}
                      className="w-9 h-9 flex items-center justify-center text-neutral-muted hover:text-danger transition-colors rounded-sm"
                      aria-label={`Remove line item ${idx + 1}`}
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Totals */}
        <div className="bg-surface-raised border border-neutral-border-light rounded-md p-6 mb-6">
          <h2 className="font-display font-bold text-sm uppercase tracking-widest text-neutral-muted mb-4">
            Totals
          </h2>
          <div className="max-w-xs ml-auto space-y-2">
            <div className="flex justify-between items-baseline">
              <span className="font-body text-sm text-neutral-secondary">
                Subtotal
              </span>
              <span
                className="font-mono text-sm text-neutral-text"
                aria-label={`Subtotal: ${formatGHS(subtotalPesewas)} Ghana cedis`}
              >
                GHS {formatGHS(subtotalPesewas)}
              </span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="font-body text-sm text-neutral-secondary">
                VAT (15%)
              </span>
              <span
                className="font-mono text-sm text-neutral-text"
                aria-label={`VAT total: ${formatGHS(vatTotalPesewas)} Ghana cedis`}
              >
                GHS {formatGHS(vatTotalPesewas)}
              </span>
            </div>
            <div className="flex justify-between items-baseline pt-2 border-t-2 border-neutral-text">
              <span className="font-display font-bold text-sm text-neutral-text">
                Grand Total
              </span>
              <span
                className="font-mono font-semibold text-lg text-neutral-text"
                aria-label={`Grand total: ${formatGHS(grandTotalPesewas)} Ghana cedis`}
              >
                GHS {formatGHS(grandTotalPesewas)}
              </span>
            </div>
          </div>
        </div>

        {/* Notes */}
        <div className="bg-surface-raised border border-neutral-border-light rounded-md p-6 mb-6">
          <label
            htmlFor="invoice-notes"
            className="block font-body text-sm font-medium text-neutral-secondary mb-1"
          >
            Notes (optional)
          </label>
          <textarea
            id="invoice-notes"
            maxLength={1000}
            rows={3}
            className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface-raised text-neutral-text focus:outline-none focus:ring-2 focus:ring-primary resize-y"
            placeholder="Payment terms, additional details, etc."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        {/* Generate button */}
        <button
          type="submit"
          disabled={generating}
          className="font-display font-semibold text-sm bg-primary text-white px-6 py-2.5 rounded-sm hover:bg-primary-light transition-colors disabled:opacity-50 min-h-[44px]"
          aria-label="Generate invoice PDF preview"
        >
          {generating ? "Generating PDF..." : "Generate PDF"}
        </button>
      </form>
    </div>
  );
}
