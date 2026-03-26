"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { register, ApiError } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    business_name: "",
  });
  const [consent, setConsent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!consent) {
      setError("You must consent to data processing to create an account.");
      return;
    }

    setLoading(true);

    try {
      await register(form);
      router.push("/reports");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-surface">
      <div className="max-w-sm w-full">
        <div className="text-center mb-8">
          <h1 className="font-display font-extrabold text-2xl text-primary tracking-tight">
            BizPulse
          </h1>
          <p className="font-body text-neutral-muted text-sm mt-1">
            Start managing your business finances
          </p>
        </div>

        <div className="bg-surface-raised border border-neutral-border-light rounded-md p-6">
          {error && (
            <div
              role="alert"
              className="bg-danger-bg text-danger font-body text-sm p-3 rounded-sm mb-4"
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                  First name
                </label>
                <input
                  type="text"
                  required
                  autoComplete="given-name"
                  className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  value={form.first_name}
                  onChange={(e) =>
                    setForm({ ...form, first_name: e.target.value })
                  }
                />
              </div>
              <div>
                <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                  Last name
                </label>
                <input
                  type="text"
                  required
                  autoComplete="family-name"
                  className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                  value={form.last_name}
                  onChange={(e) =>
                    setForm({ ...form, last_name: e.target.value })
                  }
                />
              </div>
            </div>

            <div>
              <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                Business name
              </label>
              <input
                type="text"
                required
                autoComplete="organization"
                className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                value={form.business_name}
                onChange={(e) =>
                  setForm({ ...form, business_name: e.target.value })
                }
              />
            </div>

            <div>
              <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                Email
              </label>
              <input
                type="email"
                required
                autoComplete="email"
                className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>

            <div>
              <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                Password
              </label>
              <input
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
                className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                value={form.password}
                onChange={(e) =>
                  setForm({ ...form, password: e.target.value })
                }
              />
              <p className="font-body text-xs text-neutral-faint mt-1">
                Minimum 8 characters
              </p>
            </div>

            <label className="flex items-start gap-2 cursor-pointer py-1">
              <input
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded-sm border-neutral-border accent-primary"
              />
              <span className="font-body text-xs text-neutral-muted leading-relaxed">
                I consent to the processing of my data in accordance with the
                Ghana Data Protection Act 2012 (Act 843).
              </span>
            </label>

            <button
              type="submit"
              disabled={loading}
              className="w-full font-display font-semibold text-sm bg-primary text-white py-2.5 rounded-sm hover:bg-primary-light transition-colors disabled:opacity-50 min-h-[44px]"
            >
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>
        </div>

        <p className="text-center font-body text-sm text-neutral-muted mt-4">
          Already have an account?{" "}
          <Link
            href="/login"
            className="text-primary font-medium hover:underline"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
