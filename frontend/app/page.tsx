import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
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
    </div>
  );
}
// Force Vercel to detect changes
