"use client";

import { useEffect, useState, useCallback } from "react";
import {
  listEmployees,
  createEmployee,
  computePayroll,
  listPayrollRecords,
  pesewasToCedis,
  ApiError,
} from "@/lib/api";
import type { Employee, PayrollRecord } from "@/lib/api";

function formatGHS(pesewas: number): string {
  const cedis = pesewas / 100;
  return cedis.toLocaleString("en-GH", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

const CURRENT_YEAR = new Date().getFullYear();
const CURRENT_MONTH = new Date().getMonth() + 1;

export default function PayrollPage() {
  // ---- Employee state ----
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loadingEmployees, setLoadingEmployees] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newFirst, setNewFirst] = useState("");
  const [newLast, setNewLast] = useState("");
  const [newEmpNo, setNewEmpNo] = useState("");
  const [newTin, setNewTin] = useState("");
  const [newSsnit, setNewSsnit] = useState("");
  const [newHireDate, setNewHireDate] = useState("");
  const [addingEmployee, setAddingEmployee] = useState(false);

  // ---- Payroll state ----
  const [payYear, setPayYear] = useState(CURRENT_YEAR);
  const [payMonth, setPayMonth] = useState(CURRENT_MONTH);
  const [computing, setComputing] = useState(false);
  const [payrollRecords, setPayrollRecords] = useState<PayrollRecord[]>([]);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [computeResult, setComputeResult] = useState<{
    employees_computed: number;
    records: Array<{
      employee_name: string;
      gross_salary_pesewas: number;
      ssnit_employee_pesewas: number;
      paye_pesewas: number;
      net_salary_pesewas: number;
    }>;
  } | null>(null);

  // ---- Toast / error ----
  const [error, setError] = useState("");
  const [toast, setToast] = useState("");

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(""), 3000);
  }

  // ---- Load employees ----
  const loadEmployees = useCallback(async () => {
    setLoadingEmployees(true);
    try {
      const data = await listEmployees();
      setEmployees(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load employees");
    } finally {
      setLoadingEmployees(false);
    }
  }, []);

  // ---- Load payroll records ----
  const loadPayrollRecords = useCallback(async () => {
    setLoadingRecords(true);
    try {
      const data = await listPayrollRecords(payYear, payMonth);
      setPayrollRecords(data);
    } catch {
      // silently ignore — records may not exist yet
      setPayrollRecords([]);
    } finally {
      setLoadingRecords(false);
    }
  }, [payYear, payMonth]);

  useEffect(() => {
    loadEmployees();
  }, [loadEmployees]);

  useEffect(() => {
    loadPayrollRecords();
  }, [loadPayrollRecords]);

  // ---- Add employee ----
  async function handleAddEmployee(e: React.FormEvent) {
    e.preventDefault();
    setAddingEmployee(true);
    setError("");
    try {
      await createEmployee({
        first_name: newFirst,
        last_name: newLast,
        employee_number: newEmpNo || undefined,
        tin: newTin || undefined,
        ssnit_number: newSsnit || undefined,
        hire_date: newHireDate,
      });
      showToast("Employee added successfully");
      setShowAddForm(false);
      setNewFirst("");
      setNewLast("");
      setNewEmpNo("");
      setNewTin("");
      setNewSsnit("");
      setNewHireDate("");
      await loadEmployees();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add employee");
    } finally {
      setAddingEmployee(false);
    }
  }

  // ---- Compute payroll ----
  async function handleComputePayroll() {
    setComputing(true);
    setError("");
    setComputeResult(null);
    try {
      const result = await computePayroll(payYear, payMonth);
      setComputeResult(result);
      showToast(`Payroll computed for ${result.employees_computed} employee(s)`);
      await loadPayrollRecords();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to compute payroll");
    } finally {
      setComputing(false);
    }
  }

  const MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
  ];

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="font-display font-extrabold text-2xl text-neutral-text">
          Payroll
        </h1>
        <p className="font-body text-sm text-neutral-muted mt-1">
          Manage employees and compute monthly PAYE / SSNIT deductions
        </p>
      </div>

      {/* Toast */}
      {toast && (
        <div
          role="status"
          aria-live="polite"
          className="fixed top-4 right-4 z-50 bg-success-bg border border-success text-success px-4 py-2 rounded-md shadow-lg font-body text-sm"
        >
          {toast}
        </div>
      )}

      {/* Error */}
      {error && (
        <div
          role="alert"
          className="bg-error-bg border border-error text-error px-4 py-3 rounded-md font-body text-sm"
        >
          {error}
          <button
            onClick={() => setError("")}
            className="ml-2 font-semibold hover:underline"
            aria-label="Dismiss error"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ================================================================ */}
      {/* SECTION 1: Employee List */}
      {/* ================================================================ */}
      <section aria-labelledby="emp-heading">
        <div className="flex items-center justify-between mb-4">
          <h2
            id="emp-heading"
            className="font-display font-bold text-lg text-neutral-text"
          >
            Employees
          </h2>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="font-display font-semibold text-sm px-4 py-2 rounded-sm text-white min-h-[44px] transition-colors hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
            style={{ backgroundColor: "#1B4332" }}
            aria-label={showAddForm ? "Cancel adding employee" : "Add employee"}
          >
            {showAddForm ? "Cancel" : "+ Add Employee"}
          </button>
        </div>

        {/* Inline add form */}
        {showAddForm && (
          <form
            onSubmit={handleAddEmployee}
            className="bg-surface-raised border border-neutral-border-light rounded-lg p-4 mb-4 space-y-3"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label
                  htmlFor="emp-first"
                  className="block font-body text-sm text-neutral-secondary mb-1"
                >
                  First Name *
                </label>
                <input
                  id="emp-first"
                  type="text"
                  required
                  value={newFirst}
                  onChange={(e) => setNewFirst(e.target.value)}
                  className="w-full border border-neutral-border rounded-sm px-3 py-2 font-body text-sm min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  aria-required="true"
                />
              </div>
              <div>
                <label
                  htmlFor="emp-last"
                  className="block font-body text-sm text-neutral-secondary mb-1"
                >
                  Last Name *
                </label>
                <input
                  id="emp-last"
                  type="text"
                  required
                  value={newLast}
                  onChange={(e) => setNewLast(e.target.value)}
                  className="w-full border border-neutral-border rounded-sm px-3 py-2 font-body text-sm min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  aria-required="true"
                />
              </div>
              <div>
                <label
                  htmlFor="emp-number"
                  className="block font-body text-sm text-neutral-secondary mb-1"
                >
                  Employee Number
                </label>
                <input
                  id="emp-number"
                  type="text"
                  value={newEmpNo}
                  onChange={(e) => setNewEmpNo(e.target.value)}
                  className="w-full border border-neutral-border rounded-sm px-3 py-2 font-body text-sm min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label
                  htmlFor="emp-tin"
                  className="block font-body text-sm text-neutral-secondary mb-1"
                >
                  TIN
                </label>
                <input
                  id="emp-tin"
                  type="text"
                  value={newTin}
                  onChange={(e) => setNewTin(e.target.value)}
                  className="w-full border border-neutral-border rounded-sm px-3 py-2 font-body text-sm min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label
                  htmlFor="emp-ssnit"
                  className="block font-body text-sm text-neutral-secondary mb-1"
                >
                  SSNIT Number
                </label>
                <input
                  id="emp-ssnit"
                  type="text"
                  value={newSsnit}
                  onChange={(e) => setNewSsnit(e.target.value)}
                  className="w-full border border-neutral-border rounded-sm px-3 py-2 font-body text-sm min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <div>
                <label
                  htmlFor="emp-hire"
                  className="block font-body text-sm text-neutral-secondary mb-1"
                >
                  Hire Date *
                </label>
                <input
                  id="emp-hire"
                  type="date"
                  required
                  value={newHireDate}
                  onChange={(e) => setNewHireDate(e.target.value)}
                  className="w-full border border-neutral-border rounded-sm px-3 py-2 font-body text-sm min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  aria-required="true"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={addingEmployee}
                className="font-display font-semibold text-sm px-5 py-2 rounded-sm text-white min-h-[44px] transition-colors hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
                style={{ backgroundColor: "#1B4332" }}
              >
                {addingEmployee ? "Saving..." : "Save Employee"}
              </button>
            </div>
          </form>
        )}

        {/* Employee table */}
        {loadingEmployees ? (
          <div className="animate-pulse space-y-2">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-10 bg-surface-alt rounded-sm"
              />
            ))}
          </div>
        ) : employees.length === 0 ? (
          <div className="text-center py-8 text-neutral-muted font-body text-sm">
            No employees found. Add your first employee above.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table
              className="w-full border-collapse"
              role="table"
              aria-label="Employee list"
            >
              <thead>
                <tr className="border-b border-neutral-border-light">
                  <th className="text-left font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                    Name
                  </th>
                  <th className="text-left font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3 hidden sm:table-cell">
                    Emp #
                  </th>
                  <th className="text-left font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3 hidden md:table-cell">
                    TIN
                  </th>
                  <th className="text-left font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3 hidden md:table-cell">
                    SSNIT
                  </th>
                  <th className="text-left font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                    Status
                  </th>
                  <th className="text-left font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3 hidden sm:table-cell">
                    Hire Date
                  </th>
                </tr>
              </thead>
              <tbody>
                {employees.map((emp) => (
                  <tr
                    key={emp.id}
                    className="border-b border-neutral-border-light hover:bg-surface-alt transition-colors"
                  >
                    <td className="py-2.5 px-3 font-body text-sm text-neutral-text">
                      {emp.first_name} {emp.last_name}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-sm text-neutral-secondary hidden sm:table-cell">
                      {emp.employee_number || "\u2014"}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-sm text-neutral-secondary hidden md:table-cell">
                      {emp.tin || "\u2014"}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-sm text-neutral-secondary hidden md:table-cell">
                      {emp.ssnit_number || "\u2014"}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-xs font-body font-semibold ${
                          emp.status === "active"
                            ? "bg-success-bg text-success"
                            : emp.status === "terminated"
                              ? "bg-error-bg text-error"
                              : "bg-warning-bg text-warning"
                        }`}
                      >
                        {emp.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-body text-sm text-neutral-secondary hidden sm:table-cell">
                      {emp.hire_date}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ================================================================ */}
      {/* SECTION 2: Payroll Computation */}
      {/* ================================================================ */}
      <section aria-labelledby="payroll-heading">
        <h2
          id="payroll-heading"
          className="font-display font-bold text-lg text-neutral-text mb-4"
        >
          Payroll Computation
        </h2>

        <div className="bg-surface-raised border border-neutral-border-light rounded-lg p-4 mb-4">
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label
                htmlFor="pay-year"
                className="block font-body text-sm text-neutral-secondary mb-1"
              >
                Year
              </label>
              <select
                id="pay-year"
                value={payYear}
                onChange={(e) => setPayYear(Number(e.target.value))}
                className="border border-neutral-border rounded-sm px-3 py-2 font-body text-sm min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                aria-label="Select payroll year"
              >
                {Array.from({ length: 5 }, (_, i) => CURRENT_YEAR - 2 + i).map(
                  (y) => (
                    <option key={y} value={y}>
                      {y}
                    </option>
                  )
                )}
              </select>
            </div>
            <div>
              <label
                htmlFor="pay-month"
                className="block font-body text-sm text-neutral-secondary mb-1"
              >
                Month
              </label>
              <select
                id="pay-month"
                value={payMonth}
                onChange={(e) => setPayMonth(Number(e.target.value))}
                className="border border-neutral-border rounded-sm px-3 py-2 font-body text-sm min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                aria-label="Select payroll month"
              >
                {MONTH_NAMES.map((name, idx) => (
                  <option key={idx + 1} value={idx + 1}>
                    {name}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={handleComputePayroll}
              disabled={computing}
              className="font-display font-semibold text-sm px-5 py-2 rounded-sm text-white min-h-[44px] transition-colors hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
              style={{ backgroundColor: "#D4A017" }}
              aria-label={`Compute payroll for ${MONTH_NAMES[payMonth - 1]} ${payYear}`}
            >
              {computing ? "Computing..." : "Compute Payroll"}
            </button>
          </div>
        </div>

        {/* Compute result (inline after compute) */}
        {computeResult && computeResult.records.length > 0 && (
          <div className="mb-6">
            <h3 className="font-display font-semibold text-base text-neutral-text mb-2">
              Computed Results &mdash; {MONTH_NAMES[payMonth - 1]} {payYear}
            </h3>
            <div className="overflow-x-auto">
              <table
                className="w-full border-collapse"
                role="table"
                aria-label="Payroll computation results"
              >
                <thead>
                  <tr className="border-b border-neutral-border-light">
                    <th className="text-left font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                      Employee
                    </th>
                    <th className="text-right font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                      Gross (GHS)
                    </th>
                    <th className="text-right font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                      SSNIT 5.5%
                    </th>
                    <th className="text-right font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                      PAYE
                    </th>
                    <th className="text-right font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                      Net Salary
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {computeResult.records.map((rec, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-neutral-border-light hover:bg-surface-alt transition-colors"
                    >
                      <td className="py-2.5 px-3 font-body text-sm text-neutral-text">
                        {rec.employee_name}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-sm text-neutral-text text-right">
                        {formatGHS(rec.gross_salary_pesewas)}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-sm text-neutral-secondary text-right">
                        {formatGHS(rec.ssnit_employee_pesewas)}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-sm text-neutral-secondary text-right">
                        {formatGHS(rec.paye_pesewas)}
                      </td>
                      <td className="py-2.5 px-3 font-mono text-sm font-semibold text-neutral-text text-right">
                        {formatGHS(rec.net_salary_pesewas)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Existing payroll records */}
        <h3 className="font-display font-semibold text-base text-neutral-text mb-2">
          Payroll Records
        </h3>
        {loadingRecords ? (
          <div className="animate-pulse space-y-2">
            {[1, 2].map((i) => (
              <div key={i} className="h-10 bg-surface-alt rounded-sm" />
            ))}
          </div>
        ) : payrollRecords.length === 0 ? (
          <div className="text-center py-6 text-neutral-muted font-body text-sm">
            No payroll records for {MONTH_NAMES[payMonth - 1]} {payYear}.
            Compute payroll above to generate records.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table
              className="w-full border-collapse"
              role="table"
              aria-label="Saved payroll records"
            >
              <thead>
                <tr className="border-b border-neutral-border-light">
                  <th className="text-left font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                    Employee
                  </th>
                  <th className="text-right font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                    Gross (GHS)
                  </th>
                  <th className="text-right font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                    SSNIT 5.5%
                  </th>
                  <th className="text-right font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                    PAYE
                  </th>
                  <th className="text-right font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                    Net Salary
                  </th>
                  <th className="text-left font-body font-semibold text-xs text-neutral-muted uppercase tracking-wider py-2 px-3">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {payrollRecords.map((rec) => (
                  <tr
                    key={rec.id}
                    className="border-b border-neutral-border-light hover:bg-surface-alt transition-colors"
                  >
                    <td className="py-2.5 px-3 font-body text-sm text-neutral-text">
                      {rec.employee_name}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-sm text-neutral-text text-right">
                      {formatGHS(rec.gross_salary_pesewas)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-sm text-neutral-secondary text-right">
                      {formatGHS(rec.ssnit_employee_pesewas)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-sm text-neutral-secondary text-right">
                      {formatGHS(rec.paye_pesewas)}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-sm font-semibold text-neutral-text text-right">
                      {formatGHS(rec.net_salary_pesewas)}
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded-full text-xs font-body font-semibold ${
                          rec.status === "PAID"
                            ? "bg-success-bg text-success"
                            : rec.status === "APPROVED"
                              ? "bg-info-bg text-info"
                              : rec.status === "COMPUTED"
                                ? "bg-warning-bg text-warning"
                                : "bg-surface-alt text-neutral-muted"
                        }`}
                      >
                        {rec.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
