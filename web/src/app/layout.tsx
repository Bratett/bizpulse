import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BizPulse AI",
  description: "Financial management for Ghanaian SMEs",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=DM+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#1B4332" />
      </head>
      <body className="min-h-screen" style={{ backgroundColor: "rgb(var(--color-surface))", color: "rgb(var(--color-neutral-text))" }}>
        {children}
      </body>
    </html>
  );
}
