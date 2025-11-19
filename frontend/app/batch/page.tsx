"use client";

import { useEffect, useRef, useState } from "react";
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

  const FileUploadBox = ({
    id,
    accept,
    file,
    onFileChange,
  }: {
    id: string;
    accept: string;
    file: File | null;
    onFileChange: (selected: File | null) => void;
  }) => {
    const inputRef = useRef<HTMLInputElement | null>(null);

    return (
      <div>
        <input
          ref={inputRef}
          id={id}
          type="file"
          accept={accept}
          className="hidden"
          onChange={(e) => {
            const selectedFile = e.target.files?.[0] ?? null;
            onFileChange(selectedFile);
          }}
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="flex w-full items-center justify-between rounded-lg border border-slate-300 px-3 py-2 text-left text-sm transition hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
        >
          {file ? (
            <span className="flex w-full items-center gap-2 text-slate-700">
              <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-xs font-semibold text-white">
                ✓
              </span>
              <span className="max-w-[18rem] truncate">{file.name}</span>
            </span>
          ) : (
            <span className="text-slate-500">Choose file</span>
          )}
        </button>
      </div>
    );
  };

  const resetStateForTab = (tab: TabKey) => {
    setError(null);
    setResults(null);
    setIsProcessing(false);

    setEnglishListFile(null);
    setBilingualPairsFile(null);
    setDateElementsFile(null);
    setCustomLanguageName("");
    setSelectedLanguage("");
  };

  const TabButton = ({ tab, label }: { tab: TabKey; label: string }) => (
    <button
      type="button"
      onClick={() => {
        if (tab !== activeTab) {
          resetStateForTab(tab);
          setActiveTab(tab);
        }
      }}
      className={`rounded-full px-4 py-2 text-sm font-medium transition ${
        activeTab === tab
          ? "bg-blue-600 text-white shadow-sm"
          : "bg-slate-100 text-slate-600 hover:text-slate-900"
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
      
      // Ensure csv_content is a string - handle nested objects
      if (data.csv_content && typeof data.csv_content !== 'string') {
        console.error("csv_content is not a string:", data.csv_content);
        // If it's an object, try to extract the actual CSV string
        if (typeof data.csv_content === 'object' && data.csv_content !== null) {
          // Handle nested structure: { csv_content: "...", suggested_filename: "..." }
          if ('csv_content' in data.csv_content && typeof data.csv_content.csv_content === 'string') {
            data.csv_content = data.csv_content.csv_content;
          } else {
            // Fallback: try to stringify, but this shouldn't happen
            console.error("Could not extract csv_content from nested object");
            data.csv_content = "";
          }
        } else {
          data.csv_content = String(data.csv_content);
        }
      }
      
      setResults(data);
      // If CSV content is provided, trigger a download
      if (data.csv_content) {
        const csvString = typeof data.csv_content === 'string' ? data.csv_content : (typeof data.csv_content === 'object' && data.csv_content !== null && 'csv_content' in data.csv_content ? data.csv_content.csv_content : JSON.stringify(data.csv_content));
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
    <div className="min-h-screen bg-white py-12">
      <div className="mx-auto w-full max-w-3xl px-6">
        <div className="mb-10">
          <Link href="/" className="mb-4 inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-700">
            ← Back to home
          </Link>
          <h1 className="text-3xl font-semibold text-slate-900">Batch processing</h1>
          <p className="mt-2 text-base text-slate-600">Convert multiple date expressions at once.</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="flex flex-wrap gap-2">
            <TabButton tab="english" label="English" />
            <TabButton tab="cldr" label="CLDR language" />
            <TabButton tab="noncldr" label="Non-CLDR language" />
          </div>

          {error && (
            <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              Invalid input. Please re-enter.
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-8 space-y-6">
            {activeTab === "english" && (
              <>
                <div>
                  <label htmlFor="englishList" className="mb-2 block text-sm font-medium text-slate-700">
                    Upload CSV of English expressions
                  </label>
                  <FileUploadBox
                    id="englishList"
                    accept=".csv"
                    file={englishListFile}
                    onFileChange={(file) => setEnglishListFile(file)}
                  />
                  <p className="mt-2 text-sm text-slate-500">
                    Download template:{" "}
                    <a className="font-medium text-blue-600 hover:underline" href="/batch_english_template.csv" download>
                      English expressions
                    </a>
                  </p>
                </div>
              </>
            )}

            {activeTab === "cldr" && (
              <div className="space-y-4">
                <div>
                  <label htmlFor="cldrLang" className="mb-2 block text-sm font-medium text-slate-700">
                    Choose a CLDR language
                  </label>
                  <select
                    id="cldrLang"
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
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
                  <label htmlFor="pairsFile" className="mb-2 block text-sm font-medium text-slate-700">
                    Upload CSV with English expressions and exact translations
                  </label>
                  <FileUploadBox
                    id="pairsFile"
                    accept=".csv"
                    file={bilingualPairsFile}
                    onFileChange={(file) => setBilingualPairsFile(file)}
                  />
                  <p className="mt-2 text-sm text-slate-500">
                    Download template:{" "}
                    <a className="font-medium text-blue-600 hover:underline" href="/batch_bilingual_template.csv" download>
                      Target language translations
                    </a>
                  </p>
                </div>
              </div>
            )}

            {activeTab === "noncldr" && (
              <div className="space-y-4">
                <div>
                  <label htmlFor="customLanguageName" className="mb-2 block text-sm font-medium text-slate-700">
                    Language name
                  </label>
                  <input
                    id="customLanguageName"
                    type="text"
                    value={customLanguageName}
                    onChange={(e) => setCustomLanguageName(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  />
                </div>
                <div>
                  <label htmlFor="dateElementsFile" className="mb-2 block text-sm font-medium text-slate-700">
                    Upload CSV with date elements in the target language
                  </label>
                  <FileUploadBox
                    id="dateElementsFile"
                    accept=".csv,.xlsx,.xls"
                    file={dateElementsFile}
                    onFileChange={(file) => setDateElementsFile(file)}
                  />
                  <p className="mt-2 text-sm text-slate-500">
                    Download template:{" "}
                    <a className="font-medium text-blue-600 hover:underline" href="/cldr_template.csv" download>
                      Target language lexicon
                    </a>
                  </p>
                </div>
                <div>
                  <label htmlFor="pairsFileNon" className="mb-2 block text-sm font-medium text-slate-700">
                    Upload CSV with English expressions and exact translations
                  </label>
                  <FileUploadBox
                    id="pairsFileNon"
                    accept=".csv"
                    file={bilingualPairsFile}
                    onFileChange={(file) => setBilingualPairsFile(file)}
                  />
                  <p className="mt-2 text-sm text-slate-500">
                    Download template:{" "}
                    <a className="font-medium text-blue-600 hover:underline" href="/batch_bilingual_template.csv" download>
                      Target language translations
                    </a>
                  </p>
                </div>
              </div>
            )}

            <button
              type="submit"
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60"
              disabled={isProcessing}
            >
              {isProcessing ? "Processing..." : "Process Batch"}
            </button>
          </form>

          {results && !results.error && results.csv_content && (
            <div className="mt-8 rounded-lg border border-slate-200 bg-slate-50 p-6">
              <h3 className="mb-4 text-sm font-semibold text-slate-900">Results</h3>
              {typeof results.csv_content === 'string' ? (
                <CSVPreview csvContent={results.csv_content} />
              ) : (
                <div className="text-sm text-red-600">
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
