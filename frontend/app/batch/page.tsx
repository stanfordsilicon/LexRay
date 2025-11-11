"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

// CSV Preview Component
const CSVPreview = ({ csvContent }: { csvContent: string }) => {
  const [rows, setRows] = useState<string[][]>([]);
  const [headers, setHeaders] = useState<string[]>([]);

  useEffect(() => {
    if (csvContent) {
      // Parse CSV content
      const lines = csvContent.trim().split('\n');
      if (lines.length > 0) {
        // Parse headers (first line)
        const headerRow = parseCSVLine(lines[0]);
        setHeaders(headerRow);
        
        // Parse data rows
        const dataRows = lines.slice(1).map(line => parseCSVLine(line));
        setRows(dataRows);
      }
    }
  }, [csvContent]);

  const parseCSVLine = (line: string): string[] => {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      
      if (char === '"') {
        inQuotes = !inQuotes;
      } else if (char === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    
    result.push(current.trim());
    return result;
  };

  // Function to render skeleton options with hover highlighting
  const renderSkeletonOptions = (skeletonText: string, headerName: string) => {
    // Check if this is a target skeleton column
    const isTargetSkeleton = headerName.toLowerCase().includes('target') && headerName.toLowerCase().includes('skeleton');
    
    if (isTargetSkeleton && skeletonText && skeletonText !== 'ERROR') {
      // Split skeleton options by "; " (semicolon + space) which is how the backend joins them
      const initialOptions = skeletonText.split('; ').map(opt => opt.trim()).filter(opt => opt);
      
      // The backend should be sending complete skeleton options separated by ", "
      // Each option should be a complete skeleton like "EEE, MMM d, y" or "MMM d, y"
      // Don't split these further - treat each as a complete skeleton
      const finalOptions = initialOptions;
      const options = finalOptions;
      
      if (options.length > 1) {
        return (
          <div className="space-y-1">
            {options.map((option, index) => (
              <div
                key={index}
                className="px-3 py-2 bg-gray-100 border border-gray-300 rounded-md text-sm whitespace-nowrap overflow-x-auto"
                title={`Skeleton option ${index + 1}: ${option}`}
              >
                {option}
              </div>
            ))}
          </div>
        );
      } else if (options.length === 1) {
        // Single skeleton option
        return (
          <div
            className="px-3 py-2 bg-gray-100 border border-gray-300 rounded-md text-sm whitespace-nowrap overflow-x-auto"
            title={`Skeleton: ${options[0]}`}
          >
            {options[0]}
          </div>
        );
      }
    }
    
    // Return regular cell content for non-skeleton columns
    return <span>{skeletonText}</span>;
  };

  if (rows.length === 0) {
    return <div className="text-gray-500">No data to preview</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white border border-gray-200 rounded-lg">
        <thead>
          <tr className="bg-gray-50">
            {headers.map((header, index) => (
              <th key={index} className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b border-gray-200">
                {header.replace(/_/g, ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-4 py-2 text-sm text-gray-900 border-b border-gray-200">
                  {renderSkeletonOptions(cell, headers[cellIndex] || '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

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
    setResults(null);

    try {
      setIsProcessing(true);
      const form = new FormData();

      if (activeTab === "english") {
        if (!englishListFile) {
          setError("Please upload the CSV of English expressions.");
          setIsProcessing(false);
          return;
        }
        form.append("mode", "batch-english");
        form.append("csv", englishListFile);
      } else if (activeTab === "cldr") {
        if (!selectedLanguage || !bilingualPairsFile) {
          setError("Please choose a CLDR language and upload the bilingual CSV.");
          setIsProcessing(false);
          return;
        }
        form.append("mode", "batch-cldr");
        form.append("language", selectedLanguage);
        form.append("csv", bilingualPairsFile);
      } else {
        if (!customLanguageName || !dateElementsFile || !bilingualPairsFile) {
          setError("Please provide language name, date elements spreadsheet, and bilingual CSV.");
          setIsProcessing(false);
          return;
        }
        form.append("mode", "batch-noncldr");
        form.append("language", customLanguageName);
        form.append("elements_csv", dateElementsFile);
        form.append("pairs_csv", bilingualPairsFile);
      }

      const res = await fetch("/api/process", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok || data.error) {
        throw new Error(data.error || "Processing failed");
      }
      
      // Ensure csv_content is a string
      if (data.csv_content && typeof data.csv_content !== 'string') {
        console.error("csv_content is not a string:", data.csv_content);
        data.csv_content = String(data.csv_content);
      }
      
      setResults(data);
      // If CSV content is provided, trigger a download
      if (data.csv_content) {
        const csvString = typeof data.csv_content === 'string' ? data.csv_content : JSON.stringify(data.csv_content);
        const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = data.suggested_filename || "results.csv";
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err: any) {
      setError(err?.message || "Something went wrong");
    } finally {
      setIsProcessing(false);
    }
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
            <TabButton tab="noncldr" label="Non-CLDR language" />
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
                    <option value="">Choose language</option>
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
                    Download template: <a className="text-blue-600 hover:underline" href="/cldr_template.csv" download>CLDR template (CSV)</a>
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
                    Download template: <a className="text-blue-600 hover:underline" href="/batch_bilingual_template.csv" download>English, translation pairs (CSV)</a>
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

          {results && !results.error && results.csv_content && (
            <div className="mt-6 p-6 bg-gray-50 rounded-md min-h-[300px] w-full max-w-6xl">
              <h3 className="font-medium text-gray-900 mb-4">Results:</h3>
              {typeof results.csv_content === 'string' ? (
                <CSVPreview csvContent={results.csv_content} />
              ) : (
                <div className="text-red-600">
                  Error: CSV content is not in the expected format. Please check the console for details.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
