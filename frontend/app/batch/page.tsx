"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type LanguageResponse = { languages: string[] };

type TabKey = "english" | "cldr" | "noncldr";

export default function BatchIngestion() {
  const [activeTab, setActiveTab] = useState<TabKey>("english");
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<any>(null);

  // Languages for CLDR tab
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState("");

  // Files
  const [englishListFile, setEnglishListFile] = useState<File | null>(null); // English tab
  const [bilingualPairsFile, setBilingualPairsFile] = useState<File | null>(null); // CLDR and Non-CLDR tabs
  const [dateElementsFile, setDateElementsFile] = useState<File | null>(null); // Non-CLDR
  const [customLanguageName, setCustomLanguageName] = useState(""); // Non-CLDR

  useEffect(() => {
    fetch("/api/languages")
      .then((r) => r.json() as Promise<LanguageResponse>)
      .then((data) => setAvailableLanguages(data.languages || []))
      .catch(() => setAvailableLanguages([]));
  }, []);

  const TabButton = ({ tab, label }: { tab: TabKey; label: string }) => (
    <button
      type="button"
      onClick={() => setActiveTab(tab)}
      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
        activeTab === tab
          ? "bg-indigo-200 text-indigo-900"
          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
      }`}
    >
      {label}
    </button>
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (activeTab === "english") {
      if (!englishListFile) {
        setError("Please upload the CSV of English expressions.");
        return;
      }
      setIsProcessing(true);
      setTimeout(() => {
        setIsProcessing(false);
        setResults({ mode: "english", englishListFile: englishListFile.name });
      }, 1200);
      return;
    }

    if (activeTab === "cldr") {
      if (!selectedLanguage || !bilingualPairsFile) {
        setError("Please choose a CLDR language and upload the bilingual CSV.");
        return;
      }
      setIsProcessing(true);
      setTimeout(() => {
        setIsProcessing(false);
        setResults({
          mode: "cldr",
          language: selectedLanguage,
          pairsFile: bilingualPairsFile.name,
        });
      }, 1200);
      return;
    }

    // non-CLDR
    if (!customLanguageName || !dateElementsFile || !bilingualPairsFile) {
      setError("Please provide language name, date elements spreadsheet, and bilingual CSV.");
      return;
    }
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      setResults({
        mode: "noncldr",
        language: customLanguageName,
        dateElementsFile: dateElementsFile.name,
        pairsFile: bilingualPairsFile.name,
      });
    }, 1200);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <div className="mb-8">
          <Link href="/" className="text-blue-500 hover:text-blue-600 mb-4 inline-block">
            ← Back to Home
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Batch Processing</h1>
          <p className="text-gray-600 mt-2">Convert multiple date expressions at once.</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
          {/* Tabs */}
          <div className="flex gap-2">
            <TabButton tab="english" label="English" />
            <TabButton tab="cldr" label="CLDR language" />
            <TabButton tab="noncldr" label="Non-CLDR Language" />
          </div>

          {error && (
            <div className="p-3 rounded border border-red-200 bg-red-50 text-red-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            {activeTab === "english" && (
              <>
                <div>
                  <label htmlFor="englishList" className="block text-sm font-medium text-gray-700 mb-2">
                    Upload CSV of English expressions
                  </label>
                  <input
                    id="englishList"
                    type="file"
                    accept=".csv"
                    onChange={(e) => setEnglishListFile(e.target.files?.[0] || null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-sm text-gray-600 mt-2">
                    Download template: <a className="text-blue-600 hover:underline" href="/batch_english_template.csv" download>English list (CSV)</a>
                  </p>
                </div>
              </>
            )}

            {activeTab === "cldr" && (
              <>
                <div>
                  <label htmlFor="cldrLang" className="block text-sm font-medium text-gray-700 mb-2">
                    Choose a CLDR language
                  </label>
                  <select
                    id="cldrLang"
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">None</option>
                    {availableLanguages.map((lang) => (
                      <option key={lang} value={lang}>
                        {lang}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="pairsFile" className="block text-sm font-medium text-gray-700 mb-2">
                    Upload CSV with English expressions and exact translations
                  </label>
                  <input
                    id="pairsFile"
                    type="file"
                    accept=".csv"
                    onChange={(e) => setBilingualPairsFile(e.target.files?.[0] || null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-sm text-gray-600 mt-2">
                    Download template: <a className="text-blue-600 hover:underline" href="/batch_bilingual_template.csv" download>English, translation pairs (CSV)</a>
                  </p>
                </div>
              </>
            )}

            {activeTab === "noncldr" && (
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
                  <label htmlFor="dateElementsFile" className="block text-sm font-medium text-gray-700 mb-2">
                    Upload spreadsheet of date elements
                  </label>
                  <input
                    id="dateElementsFile"
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={(e) => setDateElementsFile(e.target.files?.[0] || null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  />
                  <p className="text-sm text-gray-600 mt-2">
                    Use the same template as single processing: <a className="text-blue-600 hover:underline" href="/cldr_template.csv" download>CLDR template (CSV)</a>
                  </p>
                </div>
                <div>
                  <label htmlFor="pairsFileNon" className="block text-sm font-medium text-gray-700 mb-2">
                    Upload CSV with English expressions and exact translations
                  </label>
                  <input
                    id="pairsFileNon"
                    type="file"
                    accept=".csv"
                    onChange={(e) => setBilingualPairsFile(e.target.files?.[0] || null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-sm text-gray-600 mt-2">
                    Use the same template as the CLDR tab: <a className="text-blue-600 hover:underline" href="/batch_bilingual_template.csv" download>English, translation pairs (CSV)</a>
                  </p>
                </div>
              </>
            )}

            <button
              type="submit"
              className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-md transition-colors"
              disabled={isProcessing}
            >
              {isProcessing ? "Processing..." : "Process Batch"}
            </button>
          </form>

          {isProcessing && (
            <div className="mt-6 p-4 bg-blue-50 rounded-md">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
                <span className="text-blue-700">Processing batch...</span>
              </div>
            </div>
          )}

          {results && (
            <div className="mt-6 p-4 bg-gray-50 rounded-md">
              <h3 className="font-medium text-gray-900 mb-2">Submission preview:</h3>
              <pre className="text-sm text-gray-700">{JSON.stringify(results, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
