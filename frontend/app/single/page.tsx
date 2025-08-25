"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type LanguageResponse = { languages: string[] };

type TabKey = "english" | "existing" | "new";

export default function SingleIngestion() {
  // Tabs
  const [activeTab, setActiveTab] = useState<TabKey>("english");

  // Common
  const [englishDate, setEnglishDate] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);

  // Existing CLDR
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);
  const [selectedExistingLanguage, setSelectedExistingLanguage] = useState("");
  const [existingTranslation, setExistingTranslation] = useState("");

  // New Language
  const [customLanguageName, setCustomLanguageName] = useState("");
  const [customFile, setCustomFile] = useState<File | null>(null);
  const [newTranslation, setNewTranslation] = useState("");

  useEffect(() => {
    fetch("/api/languages")
      .then((r) => r.json() as Promise<LanguageResponse>)
      .then((data) => setAvailableLanguages(data.languages || []))
      .catch(() => setAvailableLanguages([]));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResults(null);

    const english = englishDate.trim();
    if (!english) {
      setError("Please enter the English date expression.");
      return;
    }

    try {
      setSubmitting(true);
      const form = new FormData();

      if (activeTab === "english") {
        form.append("mode", "single-english");
        form.append("english", english);
      } else if (activeTab === "existing") {
        if (!selectedExistingLanguage.trim() || !existingTranslation.trim()) {
          setError("Please choose a CLDR language and enter the translation.");
          setSubmitting(false);
          return;
        }
        form.append("mode", "single-cldr");
        form.append("english", english);
        form.append("language", selectedExistingLanguage.trim());
        form.append("translation", existingTranslation.trim());
      } else {
        if (!customLanguageName.trim() || !customFile || !newTranslation.trim()) {
          setError("Please provide language name, spreadsheet, and translation.");
          setSubmitting(false);
          return;
        }
        form.append("mode", "single-new");
        form.append("english", english);
        form.append("language", customLanguageName.trim());
        form.append("translation", newTranslation.trim());
        form.append("elements_csv", customFile);
      }

      const res = await fetch("/api/process", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok || data.error) {
        throw new Error(data.error || "Processing failed");
      }
      setResults(data);
    } catch (err: any) {
      setError(err?.message || "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  const TabButton = ({ tab, label }: { tab: TabKey; label: string }) => (
    <button
      type="button"
      onClick={() => {
        setActiveTab(tab);
        // Clear form fields when switching tabs
        setEnglishDate("");
        setSelectedExistingLanguage("");
        setExistingTranslation("");
        setCustomLanguageName("");
        setCustomFile(null);
        setNewTranslation("");
        setError(null);
        setResults(null);
      }}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        activeTab === tab
          ? "bg-indigo-200 text-indigo-900"
          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <div className="mb-8">
          <Link href="/" className="text-blue-500 hover:text-blue-600 mb-4 inline-block">
            ← Back to Home
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Single Item Processing</h1>
          <p className="text-gray-600 mt-2">Convert a single date expression.</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
          {/* Tabs */}
          <div className="flex gap-2">
            <TabButton tab="english" label="English" />
            <TabButton tab="existing" label="CLDR language" />
            <TabButton tab="new" label="Non-CLDR language" />
          </div>

          {error && (
            <div className="p-3 rounded border border-red-200 bg-red-50 text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Always ask for English first */}
            <div>
              <label htmlFor="englishDate" className="block text-sm font-medium text-gray-700 mb-2">
                English date expression
              </label>
              <input
                id="englishDate"
                type="text"
                value={englishDate}
                onChange={(e) => setEnglishDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {activeTab === "existing" && (
              <>
                <div>
                  <label htmlFor="existingLang" className="block text-sm font-medium text-gray-700 mb-2">
                    Language name
                  </label>
                  <select
                    id="existingLang"
                    value={selectedExistingLanguage}
                    onChange={(e) => setSelectedExistingLanguage(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">Choose language</option>
                    {availableLanguages.map((lang) => (
                      <option key={lang} value={lang}>
                        {lang}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="existingTranslation" className="block text-sm font-medium text-gray-700 mb-2">
                    Translation in selected language
                  </label>
                  <input
                    id="existingTranslation"
                    type="text"
                    value={existingTranslation}
                    onChange={(e) => setExistingTranslation(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </>
            )}

            {activeTab === "new" && (
              <>
                <div>
                  <label htmlFor="customLanguageName" className="block text-sm font-medium text-gray-700 mb-2">
                    Language name
                  </label>
                  <input
                    id="customLanguageName"
                    type="text"
                    value={customLanguageName}
                    onChange={(e) => setCustomLanguageName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="customFile" className="block text-sm font-medium text-gray-700 mb-2">
                    Upload spreadsheet of date elements
                  </label>
                  <input
                    id="customFile"
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={(e) => setCustomFile(e.target.files?.[0] || null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  />
                  <p className="text-sm text-gray-600 mt-2">
                    Download template: {" "}
                    <a href="/cldr_template.csv" className="text-blue-600 hover:underline" download>
                      CLDR template (CSV)
                    </a>
                  </p>
                </div>
                <div>
                  <label htmlFor="newTranslation" className="block text-sm font-medium text-gray-700 mb-2">
                    Translation in selected language
                  </label>
                  <input
                    id="newTranslation"
                    type="text"
                    value={newTranslation}
                    onChange={(e) => setNewTranslation(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </>
            )}

            <button
              type="submit"
              className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-md transition-colors disabled:opacity-60"
              disabled={submitting}
            >
              {submitting ? "Processing..." : "Convert to CLDR Skeleton"}
            </button>
          </form>

          {results && !results.error && (
            <div className="mt-6 p-6 bg-gray-50 rounded-md text-sm text-gray-800 min-h-[200px] w-full max-w-6xl">
              {results.mode === "english" ? (
                <div>English skeleton: {results.english_skeleton}</div>
              ) : (
                <div>
                  <div className="mb-2 font-medium text-gray-900">Target skeletons:</div>
                  <div className="text-sm text-gray-800">
                    {Array.isArray(results.target_skeletons) ? (
                      <div className="space-y-1">
                        {results.target_skeletons.map((skeleton: string, index: number) => (
                          <div
                            key={index}
                            className="px-3 py-2 bg-gray-100 border border-gray-300 rounded-md text-sm whitespace-nowrap overflow-x-auto"
                            title={`Skeleton option ${index + 1}`}
                          >
                            {skeleton}
                          </div>
                        ))}
                      </div>
                    ) : (
                      // Handle string format (comma-separated options)
                      (() => {
                        const skeletonText = String(results.target_skeletons);
                        const options = skeletonText.split('; ').map(opt => opt.trim()).filter(opt => opt);
                        
                        // The backend should be sending complete skeleton options separated by ", "
                        // Each option should be a complete skeleton like "EEE, MMM d, y" or "MMM d, y"
                        // Don't split these further - treat each as a complete skeleton
                        const finalOptions = options;
                        
                        return (
                          <div className="space-y-1">
                            {finalOptions.map((skeleton: string, index: number) => (
                              <div
                                key={index}
                                className="px-3 py-2 bg-gray-100 border border-gray-300 rounded-md text-sm whitespace-nowrap overflow-x-auto"
                                title={`Skeleton option ${index + 1}`}
                              >
                                {skeleton}
                              </div>
                            ))}
                          </div>
                        );
                      })()
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
