"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login, ApiError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
      router.push("/reports");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Login failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-surface">
      <div className="max-w-sm w-full">
        <div className="text-center mb-8">
          <h1 className="font-display font-extrabold text-2xl text-primary tracking-tight">
            BizPulse
          </h1>
          <p className="font-body text-neutral-muted text-sm mt-1">
            Sign in to your account
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
            <div>
              <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                Email
              </label>
              <input
                type="email"
                required
                autoComplete="email"
                className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div>
              <label className="block font-body text-sm font-medium text-neutral-secondary mb-1">
                Password
              </label>
              <input
                type="password"
                required
                autoComplete="current-password"
                className="w-full font-body text-sm border border-neutral-border rounded-sm px-3 py-2.5 bg-surface text-neutral-text min-h-[44px] focus:outline-none focus:ring-2 focus:ring-primary"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full font-display font-semibold text-sm bg-primary text-white py-2.5 rounded-sm hover:bg-primary-light transition-colors disabled:opacity-50 min-h-[44px]"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>
        </div>

        <p className="text-center font-body text-sm text-neutral-muted mt-4">
          Don&apos;t have an account?{" "}
          <Link
            href="/register"
            className="text-primary font-medium hover:underline"
          >
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
