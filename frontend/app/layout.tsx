import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Image from "next/image";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LexRay",
  description: "Generate, validate, and explore CLDR skeletons across languages.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="flex min-h-screen flex-col bg-white text-slate-900">
          <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
            <div className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-4">
              <Link href="/" aria-label="LexRay home" className="flex items-center gap-2">
                <Image src="/logo.svg" alt="LexRay logo" width={36} height={36} priority />
                <span className="text-base font-semibold tracking-tight text-slate-900">LexRay</span>
              </Link>
              <a
                href="mailto:silicon_project@stanford.edu?subject=LexRay%20Feedback"
                className="text-sm font-medium text-blue-600 transition hover:text-blue-700"
              >
                Feedback
              </a>
            </div>
          </header>
          <main className="flex-1">{children}</main>
        </div>
      </body>
    </html>
  );
}
