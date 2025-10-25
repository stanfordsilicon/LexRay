"use client";
import Link from "next/link";

export default function Home() {
  // Email click handlers
  const handleBugReport = () => {
    window.location.href =
      "mailto:silicon_project@stanford.edu?subject=CharWash:%20Bug%20Report";
  };

  const handleFeatureRequest = () => {
    window.location.href =
      "mailto:silicon_project@stanford.edu?subject=CharWash:%20Feature%20Request";
  };
  return (
    <div className="min-h-screen flex flex-col justify-between items-center justify-center bg-gray-50">
      <main className="flex-grow flex flex-col items-center justify-center text-center p-10">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-black-900 mb-8">
            Welcome to LexRay
          </h1>
          <div className="flex items-center justify-center gap-4">
            <Link
              href="/single"
              className="w-64 inline-block bg-blue-200 hover:bg-indigo-300 text-indigo-900 font-medium py-3 px-6 rounded-lg transition-colors text-center"
            >
              Single Item Processing
            </Link>
            <Link
              href="/batch"
              className="w-64 inline-block bg-blue-200 hover:bg-indigo-300 text-indigo-900 font-medium py-3 px-6 rounded-lg transition-colors text-center"
            >
              Batch Processing
            </Link>
          </div>
        </div>
      </main>
      <div>
        {/* Footer */}
        <footer
          style={{
            padding: "20px 0",
            textAlign: "center",
          }}
        >
          <div className="divide-x" style={{ marginTop: "10px" }}>
            <button
              className="inline-block hover:text-indigo-300 text-indigo-900 font-medium px-3 transition-colors text-center"
              onClick={handleBugReport}
            >
              Bug Report
            </button>

            <button
              className="inline-block hover:text-indigo-300 text-indigo-900 font-medium px-3 transition-colors text-center"
              onClick={handleFeatureRequest}
            >
              Feature Request
            </button>
            <a
              href="https://silicon.stanford.edu"
              target="_blank"
              rel="noopener noreferrer"
            >
              <button className="inline-block hover:text-indigo-300 text-indigo-900 font-medium px-3 transition-colors text-center">
                About SILICON
              </button>
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
}
