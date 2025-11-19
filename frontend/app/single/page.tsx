"use client";

import { useEffect, useRef, useState } from "react";
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
  
  // Ambiguity resolution
  const [ambiguityOptions, setAmbiguityOptions] = useState<Record<number, Array<{name: string, skeleton_code: string}>>>({});
  const [ambiguitySelections, setAmbiguitySelections] = useState<Record<number, string>>({});
  const [pendingEnglishSkeleton, setPendingEnglishSkeleton] = useState<string | null>(null);

  // Existing CLDR
  const [availableLanguages, setAvailableLanguages] = useState<string[]>([]);
  const [selectedExistingLanguage, setSelectedExistingLanguage] = useState("");
  const [existingTranslation, setExistingTranslation] = useState("");

  // New Language
  const [customLanguageName, setCustomLanguageName] = useState("");
  const [customFile, setCustomFile] = useState<File | null>(null);
  const [newTranslation, setNewTranslation] = useState("");

  // Template example modal
  const [showExample, setShowExample] = useState<string | null>(null);

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
      
      // Check if ambiguity resolution is required
      if (data.requires_ambiguity_resolution && data.ambiguity_options) {
        setAmbiguityOptions(data.ambiguity_options);
        setPendingEnglishSkeleton(data.english_skeleton);
        // Initialize selections with first option name for each position
        const initialSelections: Record<number, string> = {};
        for (const [posStr, options] of Object.entries(data.ambiguity_options)) {
          const pos = parseInt(posStr);
          if (Array.isArray(options) && options.length > 0) {
            // Handle both old format (string[]) and new format ({name, skeleton_code}[])
            const firstOption = options[0];
            initialSelections[pos] = typeof firstOption === 'string' ? firstOption : firstOption.name;
          }
        }
        setAmbiguitySelections(initialSelections);
        setSubmitting(false);
        return;
      }
      
      // Add the mode to the results so we know which display logic to use
      setResults({ ...data, mode: activeTab });
    } catch (err: any) {
      setError(err?.message || "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAmbiguityResolution = async () => {
    if (!pendingEnglishSkeleton) return;
    
    setError(null);
    setSubmitting(true);
    
    try {
      const form = new FormData();
      const english = englishDate.trim();
      
      if (activeTab === "english") {
        form.append("mode", "resolve-ambiguity");
        form.append("english", english);
        form.append("english_skeleton", pendingEnglishSkeleton);
      } else if (activeTab === "existing") {
        form.append("mode", "resolve-ambiguity-cldr");
        form.append("english", english);
        form.append("language", selectedExistingLanguage.trim());
        form.append("translation", existingTranslation.trim());
        form.append("english_skeleton", pendingEnglishSkeleton);
      } else {
        form.append("mode", "resolve-ambiguity-noncldr");
        form.append("english", english);
        form.append("language", customLanguageName.trim());
        form.append("translation", newTranslation.trim());
        form.append("english_skeleton", pendingEnglishSkeleton);
        if (customFile) {
          form.append("elements_csv", customFile);
        }
      }
      
      form.append("ambiguity_selections", JSON.stringify(ambiguitySelections));
      form.append("ambiguity_options", JSON.stringify(ambiguityOptions));
      
      const res = await fetch("/api/process", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok || data.error) {
        throw new Error(data.error || "Processing failed");
      }
      
      // Clear ambiguity state
      setAmbiguityOptions({});
      setAmbiguitySelections({});
      setPendingEnglishSkeleton(null);
      
      // Set results
      setResults({ ...data, mode: activeTab });
    } catch (err: any) {
      setError(err?.message || "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  };

  const FileUploadBox = ({
    id,
    accept,
    onFileChange,
    file,
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
      className={`rounded-full px-4 py-2 text-sm font-medium transition ${
        activeTab === tab
          ? "bg-blue-600 text-white shadow-sm"
          : "bg-slate-100 text-slate-600 hover:text-slate-900"
      }`}
    >
      {label}
    </button>
  );

  const TemplateLink = ({ href, label, exampleType }: { href: string; label: string; exampleType: string }) => {
    const buttonRef = useRef<HTMLButtonElement>(null);
    const bubbleRef = useRef<HTMLDivElement>(null);

    const getExample = () => {
      switch (exampleType) {
        case "lexicon":
          return {
            title: "Target Language Lexicon",
            content: (
              <div className="space-y-3 text-sm">
                <p className="text-slate-700">
                  This template should contain date elements (days, months, etc.) in your target language. 
                  Each row should include the Header, XPath, Code, English term, and the Translation in your target language.
                </p>
                <p className="text-slate-700">
                  Click the link below to download a Spanish example CSV file that shows the expected format:
                </p>
                <div className="pt-2">
                  <a
                    href="/spanish_template.csv"
                    download
                    className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
                  >
                    Download Spanish Example CSV
                  </a>
                </div>
              </div>
            ),
          };
        case "translations":
          return {
            title: "Target Language Translations",
            content: (
              <div className="space-y-3 text-sm">
                <p className="text-slate-700">
                  This template should contain pairs of English date expressions and their exact translations in your target language. 
                  Each row should have the English expression in the first column and the translation in the second column.
                </p>
                <p className="text-slate-700">
                  Click the link below to download a Spanish example CSV file that shows the expected format:
                </p>
                <div className="pt-2">
                  <a
                    href="/english_spanish_template.csv"
                    download
                    className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
                  >
                    Download Spanish Example CSV
                  </a>
                </div>
              </div>
            ),
          };
        default:
          return null;
      }
    };

    const example = getExample();
    const isOpen = showExample === exampleType;

    return (
      <span className="relative inline-flex items-center gap-1">
        <a href={href} className="font-medium text-blue-600 hover:underline" download>
          {label}
        </a>
        {example && (
          <>
            <button
              ref={buttonRef}
              type="button"
              onClick={() => setShowExample(isOpen ? null : exampleType)}
              className="inline-flex h-4 w-4 items-center justify-center rounded-full bg-slate-200 text-xs text-slate-600 hover:bg-slate-300"
              title="View Spanish example"
            >
              ?
            </button>
            {isOpen && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setShowExample(null)}
                />
                <div
                  ref={bubbleRef}
                  className="absolute left-0 top-6 z-50 w-80 rounded-lg border border-slate-200 bg-white p-4 shadow-lg"
                  onClick={(e) => e.stopPropagation()}
                >
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-slate-900">{example.title}</h3>
                    <button
                      type="button"
                      onClick={() => setShowExample(null)}
                      className="flex h-6 w-6 items-center justify-center rounded-full text-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                      aria-label="Close"
                    >
                      ×
                    </button>
                  </div>
                  {example.content}
                </div>
              </>
            )}
          </>
        )}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-white py-12">
      <div className="mx-auto w-full max-w-3xl px-6">
        <div className="mb-10">
          <Link href="/" className="mb-4 inline-flex items-center text-sm font-medium text-blue-600 hover:text-blue-700">
            ← Back to home
          </Link>
          <h1 className="text-3xl font-semibold text-slate-900">Single processing</h1>
          <p className="mt-2 text-base text-slate-600">Convert one date expression at a time.</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="flex flex-wrap gap-2">
            <TabButton tab="english" label="English" />
            <TabButton tab="existing" label="CLDR language" />
            <TabButton tab="new" label="Non-CLDR language" />
          </div>

          {error && (
            <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              Invalid input. Please re-enter.
            </div>
          )}

          {Object.keys(ambiguityOptions).length > 0 && (
            <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-6">
              <h3 className="mb-4 text-sm font-semibold text-slate-900">
                Please select the correct interpretation for ambiguous date elements:
              </h3>
              <div className="space-y-4">
                {Object.entries(ambiguityOptions).map(([posStr, options]) => {
                  const pos = parseInt(posStr);
                  // Handle both old format (string[]) and new format ({name, skeleton_code}[])
                  const firstOption = Array.isArray(options) && options.length > 0 ? options[0] : null;
                  const defaultSelected = firstOption 
                    ? (typeof firstOption === 'string' ? firstOption : firstOption.name)
                    : "";
                  const selected = ambiguitySelections[pos] || defaultSelected;
                  return (
                    <div key={pos}>
                      <label className="mb-2 block text-sm font-medium text-slate-700">
                        Position {pos + 1}:
                      </label>
                      <select
                        value={selected}
                        onChange={(e) => {
                          setAmbiguitySelections({ ...ambiguitySelections, [pos]: e.target.value });
                        }}
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                      >
                        {Array.isArray(options) && options.map((option, idx) => {
                          const optionName = typeof option === 'string' ? option : option.name;
                          return (
                            <option key={idx} value={optionName}>
                              {optionName}
                            </option>
                          );
                        })}
                      </select>
                    </div>
                  );
                })}
              </div>
              <button
                type="button"
                onClick={handleAmbiguityResolution}
                disabled={submitting}
                className="mt-4 w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60"
              >
                {submitting ? "Processing..." : "Confirm selections"}
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-8 space-y-6" style={{ display: Object.keys(ambiguityOptions).length > 0 ? 'none' : 'block' }}>
            {activeTab === "new" ? (
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
                  <label htmlFor="englishDate" className="mb-2 block text-sm font-medium text-slate-700">
                    English date expression
                  </label>
                  <input
                    id="englishDate"
                    type="text"
                    value={englishDate}
                    onChange={(e) => setEnglishDate(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  />
                </div>
                <div>
                  <label htmlFor="customFile" className="mb-2 block text-sm font-medium text-slate-700">
                    Upload CSV with date elements in the target language
                  </label>
                  <FileUploadBox
                    id="customFile"
                    accept=".csv,.xlsx,.xls"
                    file={customFile}
                    onFileChange={(file) => setCustomFile(file)}
                  />
                  <p className="mt-2 text-sm text-slate-500">
                    Download template:{" "}
                    <TemplateLink href="/cldr_template.csv" label="Target language lexicon" exampleType="lexicon" />
                  </p>
                </div>
                <div>
                  <label htmlFor="newTranslation" className="mb-2 block text-sm font-medium text-slate-700">
                    Translation in selected language
                  </label>
                  <input
                    id="newTranslation"
                    type="text"
                    value={newTranslation}
                    onChange={(e) => setNewTranslation(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  />
                </div>
              </div>
            ) : activeTab === "existing" ? (
              <div className="space-y-4">
                <div>
                  <label htmlFor="existingLang" className="mb-2 block text-sm font-medium text-slate-700">
                    Language name
                  </label>
                  <select
                    id="existingLang"
                    value={selectedExistingLanguage}
                    onChange={(e) => setSelectedExistingLanguage(e.target.value)}
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
                  <label htmlFor="englishDate" className="mb-2 block text-sm font-medium text-slate-700">
                    English date expression
                  </label>
                  <input
                    id="englishDate"
                    type="text"
                    value={englishDate}
                    onChange={(e) => setEnglishDate(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  />
                </div>
                <div>
                  <label htmlFor="existingTranslation" className="mb-2 block text-sm font-medium text-slate-700">
                    Translation in selected language
                  </label>
                  <input
                    id="existingTranslation"
                    type="text"
                    value={existingTranslation}
                    onChange={(e) => setExistingTranslation(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                  />
                </div>
              </div>
            ) : (
              <div>
                <label htmlFor="englishDate" className="mb-2 block text-sm font-medium text-slate-700">
                  English date expression
                </label>
                <input
                  id="englishDate"
                  type="text"
                  value={englishDate}
                  onChange={(e) => setEnglishDate(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                />
              </div>
            )}

            <button
              type="submit"
              className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-60"
              disabled={submitting}
            >
              {submitting ? "Processing..." : "Convert to CLDR skeleton"}
            </button>
          </form>

          {results && !results.error && (
            <div className="mt-8 space-y-3 text-sm text-slate-800">
              {results.mode === "english" ? (
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
                  <div className="mb-1 font-medium text-slate-900">English skeleton</div>
                  <code className="block font-mono text-slate-900">{results.english_skeleton}</code>
                </div>
              ) : (
                <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
                  <div className="mb-1 font-medium text-slate-900">Target skeletons</div>
                  {Array.isArray(results.target_skeletons) ? (
                    <div className="space-y-2">
                      {results.target_skeletons.map((skeleton: string, index: number) => (
                        <code
                          key={index}
                          className="block font-mono text-slate-900"
                          title={`Skeleton option ${index + 1}`}
                        >
                          {skeleton}
                        </code>
                      ))}
                    </div>
                  ) : (
                    (() => {
                      const skeletonText = String(results.target_skeletons);
                      const options = skeletonText
                        .split(/;|\n/)
                        .map((opt) => opt.trim())
                        .filter((opt) => opt);
                      const finalOptions = options.length > 0 ? options : [skeletonText.trim()];

                      return (
                        <div className="space-y-2">
                          {finalOptions.map((skeleton: string, index: number) => (
                            <code
                              key={index}
                              className="block font-mono text-slate-900"
                              title={`Skeleton option ${index + 1}`}
                            >
                              {skeleton}
                            </code>
                          ))}
                        </div>
                      );
                    })()
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
