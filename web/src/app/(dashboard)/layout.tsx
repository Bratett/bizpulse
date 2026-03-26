"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { logout } from "@/lib/api";

const navItems = [
  { href: "/reports", label: "P&L Report", icon: "📊" },
  { href: "/transactions", label: "Transactions", icon: "📝" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [businessName, setBusinessName] = useState("");
  const [userName, setUserName] = useState("");
  const [collapsed, setCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  useEffect(() => {
    const user = localStorage.getItem("user");
    if (!user) {
      router.push("/login");
      return;
    }
    const parsed = JSON.parse(user);
    setUserName(parsed.first_name || "");
    const biz = localStorage.getItem("business");
    if (biz) {
      setBusinessName(JSON.parse(biz).legal_name || "My Business");
    }
    const saved = localStorage.getItem("sidebar-collapsed");
    if (saved === "true") setCollapsed(true);
    const theme = localStorage.getItem("theme");
    if (theme === "dark") {
      setDarkMode(true);
      document.documentElement.setAttribute("data-theme", "dark");
    }
  }, [router]);

  const toggleCollapsed = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem("sidebar-collapsed", String(next));
  };

  const toggleDarkMode = () => {
    const next = !darkMode;
    setDarkMode(next);
    localStorage.setItem("theme", next ? "dark" : "light");
    document.documentElement.setAttribute(
      "data-theme",
      next ? "dark" : "light"
    );
  };

  const handleLogout = () => setShowLogoutConfirm(true);
  const confirmLogout = () => {
    logout();
    router.push("/login");
  };

  const sidebarWidth = collapsed ? "w-16" : "w-48";
  const mainMargin = collapsed ? "md:ml-16" : "md:ml-48";

  return (
    <div className="min-h-screen bg-surface flex">
      {/* Desktop Sidebar */}
      <aside
        className={`hidden md:flex md:flex-col ${sidebarWidth} text-white fixed inset-y-0 left-0 z-20 transition-all duration-200 ease-in-out`}
        style={{ backgroundColor: "#1B4332" }}
      >
        {/* Brand + collapse toggle */}
        <div className="px-3 py-4 border-b border-white/10 flex items-center justify-between">
          {!collapsed && (
            <span className="font-display font-extrabold text-lg tracking-tight text-white pl-2">
              BizPulse
            </span>
          )}
          <button
            onClick={toggleCollapsed}
            className={`p-2 rounded-sm text-white/60 hover:text-white hover:bg-white/10 transition-colors ${collapsed ? "mx-auto" : ""}`}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              className={`transition-transform duration-200 ${collapsed ? "rotate-180" : ""}`}
            >
              <path
                d="M10 12L6 8L10 4"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-2 py-4 space-y-1" aria-label="Main navigation">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                title={collapsed ? item.label : undefined}
                className={`flex items-center ${collapsed ? "justify-center px-0 py-2.5" : "gap-3 px-3 py-2.5"} rounded-sm text-sm font-body transition-colors ${isActive ? "bg-white/15 text-white font-semibold" : "text-white/70 hover:bg-white/10 hover:text-white"}`}
              >
                <span className={collapsed ? "text-lg" : "text-base"} aria-hidden="true">
                  {item.icon}
                </span>
                {!collapsed && (
                  <>
                    {item.label}
                    {isActive && (
                      <span className="ml-auto w-1.5 h-1.5 rounded-full bg-accent" />
                    )}
                  </>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User avatar only */}
        <div className="px-2 py-3 border-t border-white/10">
          {!collapsed ? (
            <div className="flex items-center gap-2.5 px-2">
              <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
                <span className="font-display font-bold text-xs text-primary">
                  {userName?.[0]?.toUpperCase() || "?"}
                </span>
              </div>
              <div className="min-w-0">
                <p className="font-body text-sm text-white/90 truncate leading-tight">{userName}</p>
                <p className="font-body text-[11px] text-white/45 truncate leading-tight">{businessName}</p>
              </div>
            </div>
          ) : (
            <div className="flex justify-center">
              <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center" title={`${userName} — ${businessName}`}>
                <span className="font-display font-bold text-xs text-primary">
                  {userName?.[0]?.toUpperCase() || "?"}
                </span>
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Main content area */}
      <div className={`flex-1 ${mainMargin} flex flex-col min-h-screen transition-all duration-200 ease-in-out`}>
        {/* Top header bar */}
        <header className="bg-surface-raised border-b border-neutral-border-light px-4 md:px-6 h-12 flex items-center justify-between sticky top-0 z-10">
          {/* Mobile: show brand. Desktop: empty left side (sidebar has brand) */}
          <span className="md:hidden font-display font-extrabold text-lg text-primary tracking-tight">
            BizPulse
          </span>
          <div className="hidden md:block" />

          {/* Right side: utilities */}
          <div className="flex items-center gap-1">
            <button
              onClick={toggleDarkMode}
              title={darkMode ? "Light mode" : "Dark mode"}
              className="w-9 h-9 flex items-center justify-center text-neutral-muted hover:text-neutral-text hover:bg-surface-alt rounded-sm transition-colors"
            >
              <span className="text-sm">{darkMode ? "☀️" : "🌙"}</span>
            </button>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="w-9 h-9 flex items-center justify-center text-neutral-muted hover:text-neutral-text hover:bg-surface-alt rounded-sm transition-colors"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 max-w-[1080px] w-full mx-auto px-6 py-8 pb-24 md:pb-8">
          {children}
        </main>
      </div>

      {/* Mobile bottom tabs */}
      <nav
        className="md:hidden fixed bottom-0 inset-x-0 bg-surface-raised border-t border-neutral-border-light z-20"
        aria-label="Mobile navigation"
      >
        <div className="flex">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex-1 flex flex-col items-center py-2 min-h-[56px] justify-center transition-colors relative ${isActive ? "text-primary" : "text-neutral-muted"}`}
              >
                <span className="text-xl" aria-hidden="true">{item.icon}</span>
                <span className={`text-[10px] mt-0.5 font-body ${isActive ? "font-semibold" : ""}`}>
                  {item.label}
                </span>
                {isActive && (
                  <span className="absolute top-0 w-8 h-0.5 bg-accent rounded-b" />
                )}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Sign-out confirmation dialog */}
      {showLogoutConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
          onClick={() => setShowLogoutConfirm(false)}
        >
          <div
            className="bg-surface-raised rounded-lg shadow-xl p-6 max-w-sm w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="font-display font-bold text-lg text-neutral-text mb-2">
              Sign out?
            </h2>
            <p className="font-body text-sm text-neutral-muted mb-6">
              Are you sure you want to sign out of BizPulse?
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowLogoutConfirm(false)}
                className="font-display font-semibold text-sm px-4 py-2 rounded-sm border border-neutral-border text-neutral-secondary hover:border-primary hover:text-primary transition-colors min-h-[40px]"
              >
                Cancel
              </button>
              <button
                onClick={confirmLogout}
                className="font-display font-semibold text-sm px-4 py-2 rounded-sm bg-danger text-white hover:opacity-90 transition-colors min-h-[40px]"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
