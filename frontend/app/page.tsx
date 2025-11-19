"use client";
import Link from "next/link";

export default function Home() {
  // Email click handlers
  const handleBugReport = () => {
    window.location.href =
      "mailto:silicon_project@stanford.edu?subject=LexRay:%20Bug%20Report";
  };

  const handleFeatureRequest = () => {
    window.location.href =
      "mailto:silicon_project@stanford.edu?subject=LexRay:%20Feature%20Request";
  };
  return (
    <main className="flex flex-1 items-center justify-center bg-white">
      <div className="mx-auto flex w-full max-w-3xl flex-col items-center gap-8 px-6 py-24 text-center">
        <div className="space-y-3">
          <h1 className="text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
            Welcome to LexRay
          </h1>
          <p className="text-base text-slate-600">
            Choose an option below to begin working with CLDR skeletons.
          </p>
        </div>
        <div className="flex w-full flex-col items-center gap-4 sm:flex-row sm:justify-center">
          <Link
            href="/single"
            className="inline-flex w-full items-center justify-center rounded-lg border-2 border-blue-600 px-8 py-3 text-base font-semibold text-blue-600 transition hover:bg-blue-600 hover:text-white sm:w-auto sm:min-w-[200px]"
          >
            Single processing
          </Link>
          <Link
            href="/batch"
            className="inline-flex w-full items-center justify-center rounded-lg border-2 border-blue-600 px-8 py-3 text-base font-semibold text-blue-600 transition hover:bg-blue-600 hover:text-white sm:w-auto sm:min-w-[200px]"
          >
            Batch processing
          </Link>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-slate-500">
          <button onClick={handleBugReport} className="transition hover:text-blue-600">
            Report a bug
          </button>
          <span aria-hidden="true">•</span>
          <button onClick={handleFeatureRequest} className="transition hover:text-blue-600">
            Request a feature
          </button>
          <span aria-hidden="true">•</span>
          <a
            href="https://silicon.stanford.edu"
            target="_blank"
            rel="noopener noreferrer"
            className="transition hover:text-blue-600"
          >
            About SILICON
          </a>
        </div>
      </div>
    </main>
  );
}
