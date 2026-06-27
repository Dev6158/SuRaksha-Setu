"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import RiskDistributionChart from "@/components/RiskDistributionChart";
import RiskTrendChart from "@/components/RiskTrendChart";

interface DocumentLog {
  id: string;
  documentName: string;
  contentType: string;
  sha256Hash: string;
  riskScore: number;
  riskDecision: string;
  createdAt: string;
  metadataSnapshot?: {
    originalFilename?: string;
    declaredPurpose?: string;
    byteSize?: number;
    uploadedAt?: string;
    summary?: string;
    qrCodeDetected?: boolean;
    qrCodeData?: string;
    pdfMetadata?: Record<string, string>;
    pdfHasSignature?: boolean;
  };
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({
    total: 0,
    high: 0,
    medium: 0,
    low: 0,
  });
  const [documents, setDocuments] = useState<DocumentLog[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentLog | null>(null);

  // Upload States
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadPurpose, setUploadPurpose] = useState("Manual Document Check");
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<DocumentLog | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Authentication State
  const [authToken, setAuthToken] = useState("");

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

  const loginAndGetToken = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: "demo_user",
          password: "password123",
        }),
      });
      if (response.ok) {
        const data = await response.json();
        setAuthToken(data.accessToken);
        return data.accessToken;
      }
    } catch (e) {
      console.error("Login failed, falling back to hardcoded token", e);
    }
    const fallbackToken = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJkZW1vX3VzZXIiLCJyb2xlcyI6WyJST0xFX1VTRVIiXSwiaWF0IjoxNzgyNDk2OTE3LCJleHAiOjE3ODI1MDA1MTd9.U6LYbDM7PGfuwLj9Vj_tswm-LeDpTPWDj6DbA1Kw-z4";
    setAuthToken(fallbackToken);
    return fallbackToken;
  };

  const fetchData = async (tokenOverride?: string) => {
    const activeToken = tokenOverride || authToken;
    if (!activeToken) return;

    try {
      setLoading(true);
      const [summaryRes, transRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/account/summary`, {
          headers: {
            Authorization: `Bearer ${activeToken}`,
          },
        }),
        fetch(`${API_BASE_URL}/api/v1/transactions`, {
          headers: {
            Authorization: `Bearer ${activeToken}`,
          },
        }),
      ]);

      if (summaryRes.ok && transRes.ok) {
        const summaryData = await summaryRes.json();
        const transData = await transRes.json();

        let lowCount = 0;
        let medCount = 0;
        let highCount = 0;

        transData.forEach((doc: DocumentLog) => {
          if (doc.riskScore >= 0.65) highCount++;
          else if (doc.riskScore >= 0.4) medCount++;
          else lowCount++;
        });

        setSummary({
          total: transData.length,
          high: highCount,
          medium: medCount,
          low: lowCount,
        });
        setDocuments(transData);
      }
    } catch (error) {
      console.error("Error fetching admin dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadError(null);
    setUploadResult(null);

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("purpose", uploadPurpose);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setUploadResult(result);
        fetchData();
      } else {
        const errorText = await response.text();
        setUploadError(`Upload failed: ${errorText || response.statusText}`);
      }
    } catch (err: any) {
      setUploadError(`Network error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      const token = await loginAndGetToken();
      fetchData(token);
    };
    init();
  }, []);

  return (
    <div className="flex min-h-screen bg-slate-900 text-slate-100 font-sans">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <div className="flex-grow p-8 overflow-y-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Incident Command Dashboard
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Real-time document forensics and behavioral threat indicators
            </p>
          </div>
          <button
            onClick={() => fetchData()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-colors duration-150"
          >
            🔄 Refresh Data
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        ) : (
          <>
            {/* Tab: Dashboard */}
            {activeTab === "dashboard" && (
              <div className="space-y-8 animate-fade-in">
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg">
                    <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Scanned</h2>
                    <p className="text-4xl font-extrabold text-white mt-2">{summary.total}</p>
                  </div>
                  <div className="bg-slate-800 border border-red-900/50 rounded-xl p-6 shadow-lg">
                    <h2 className="text-xs font-semibold text-red-400 uppercase tracking-wider">High Risk</h2>
                    <p className="text-4xl font-extrabold text-red-500 mt-2">{summary.high}</p>
                  </div>
                  <div className="bg-slate-800 border border-yellow-900/50 rounded-xl p-6 shadow-lg">
                    <h2 className="text-xs font-semibold text-yellow-400 uppercase tracking-wider">Medium Risk</h2>
                    <p className="text-4xl font-extrabold text-yellow-500 mt-2">{summary.medium}</p>
                  </div>
                  <div className="bg-slate-800 border border-green-900/50 rounded-xl p-6 shadow-lg">
                    <h2 className="text-xs font-semibold text-green-400 uppercase tracking-wider">Authentic</h2>
                    <p className="text-4xl font-extrabold text-green-500 mt-2">{summary.low}</p>
                  </div>
                </div>

                {/* Charts */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <RiskDistributionChart />
                  <RiskTrendChart />
                </div>
              </div>
            )}

            {/* Tab: Analytics */}
            {activeTab === "analytics" && (
              <div className="space-y-8 animate-fade-in">
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg">
                  <h2 className="text-xl font-bold text-white mb-4">Security Incident Log</h2>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-700 text-slate-400 text-xs uppercase tracking-wider">
                          <th className="py-3 px-4">Document</th>
                          <th className="py-3 px-4">Verdict</th>
                          <th className="py-3 px-4">Score</th>
                          <th className="py-3 px-4">Scan Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {documents.filter(d => d.riskScore >= 0.4).length === 0 ? (
                          <tr>
                            <td colSpan={4} className="text-center py-8 text-slate-500">
                              No high or medium-risk security incidents flagged.
                            </td>
                          </tr>
                        ) : (
                          documents.filter(d => d.riskScore >= 0.4).map((doc) => (
                            <tr key={doc.id} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors duration-150">
                              <td className="py-4 px-4 font-medium text-white">{doc.documentName}</td>
                              <td className="py-4 px-4">
                                <span className={`px-2 py-1 rounded text-xs font-bold ${
                                  doc.riskScore >= 0.65 ? "bg-red-900/50 text-red-400" : "bg-yellow-900/50 text-yellow-400"
                                }`}>
                                  {doc.riskDecision}
                                </span>
                              </td>
                              <td className="py-4 px-4 text-slate-300">{(doc.riskScore * 100).toFixed(1)}%</td>
                              <td className="py-4 px-4 text-slate-400">{new Date(doc.createdAt).toLocaleString()}</td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Tab: Documents */}
            {activeTab === "documents" && (
              <div className="space-y-8 animate-fade-in">
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg">
                  <h2 className="text-xl font-bold text-white mb-4">All Uploaded Assets</h2>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-700 text-slate-400 text-xs uppercase tracking-wider">
                          <th className="py-3 px-4">Filename</th>
                          <th className="py-3 px-4">MIME Type</th>
                          <th className="py-3 px-4">Hash</th>
                          <th className="py-3 px-4">Risk Score</th>
                          <th className="py-3 px-4">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {documents.length === 0 ? (
                          <tr>
                            <td colSpan={5} className="text-center py-8 text-slate-500">
                              No files uploaded yet. Execute standard uploads from Swagger or the mobile client.
                            </td>
                          </tr>
                        ) : (
                          documents.map((doc) => (
                            <tr key={doc.id} className="border-b border-slate-800 hover:bg-slate-850 transition-colors duration-150">
                              <td className="py-4 px-4 font-semibold text-white">{doc.documentName}</td>
                              <td className="py-4 px-4 text-slate-400 text-sm">{doc.contentType}</td>
                              <td className="py-4 px-4 text-slate-500 font-mono text-xs">{doc.sha256Hash.substring(0, 10)}...</td>
                              <td className="py-4 px-4">
                                <span className={`px-2 py-1 rounded text-xs font-bold ${
                                  doc.riskScore >= 0.65 ? "bg-red-900/50 text-red-400" :
                                  doc.riskScore >= 0.4 ? "bg-yellow-900/50 text-yellow-400" :
                                  "bg-green-900/50 text-green-400"
                                }`}>
                                  {(doc.riskScore * 100).toFixed(1)}% ({doc.riskDecision})
                                </span>
                              </td>
                              <td className="py-4 px-4">
                                <button
                                  onClick={() => setSelectedDoc(doc)}
                                  className="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-white rounded text-xs font-semibold"
                                >
                                  🔍 Inspect
                                </button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Tab: Upload */}
            {activeTab === "upload" && (
              <div className="space-y-8 animate-fade-in max-w-4xl mx-auto">
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg">
                  <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                    <span>📤</span> Document Integrity Scan
                  </h2>
                  <p className="text-xs text-slate-400 mb-6">
                    Upload an asset (Image, PDF, JSON, or XML) to perform active forensics checks, ELA, and QR authenticity.
                  </p>

                  <form onSubmit={handleUpload} className="space-y-6">
                    {/* Drag-and-drop or select box */}
                    <div className="border-2 border-dashed border-slate-700 hover:border-blue-500 rounded-xl p-8 text-center bg-slate-900/50 hover:bg-slate-900 transition-all duration-150 relative cursor-pointer group">
                      <input
                        type="file"
                        id="document-file"
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) setUploadFile(file);
                        }}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        accept=".jpeg,.jpg,.png,.pdf,.avif,.json,.xml,.txt"
                        required
                      />
                      <div className="space-y-2">
                        <div className="text-4xl text-slate-500 group-hover:text-blue-400 transition-colors duration-150">📂</div>
                        {uploadFile ? (
                          <div className="text-sm font-semibold text-white">
                            Selected: <span className="text-blue-400">{uploadFile.name}</span> ({(uploadFile.size / 1024).toFixed(1)} KB)
                          </div>
                        ) : (
                          <>
                            <div className="text-sm font-semibold text-slate-200">
                              Drag and drop your file here, or <span className="text-blue-500 underline">browse</span>
                            </div>
                            <div className="text-xs text-slate-500">
                              Supports JPG, PNG, PDF, WebP, AVIF, JSON, XML (Max 30MB)
                            </div>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Purpose Input */}
                    <div>
                      <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                        Verification Purpose
                      </label>
                      <input
                        type="text"
                        value={uploadPurpose}
                        onChange={(e) => setUploadPurpose(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 text-sm focus:border-blue-500 focus:outline-none"
                        placeholder="e.g., Customer onboarding audit"
                        required
                      />
                    </div>

                    {/* Submit Button */}
                    <button
                      type="submit"
                      disabled={uploading || !uploadFile}
                      className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg text-sm font-bold transition-all duration-150 flex items-center justify-center gap-2"
                    >
                      {uploading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                          <span>Analyzing Document Integrity...</span>
                        </>
                      ) : (
                        <>
                          <span>🛡️</span> Run Forensic Scan
                        </>
                      )}
                    </button>
                  </form>

                  {uploadError && (
                    <div className="mt-6 p-4 bg-red-950/50 border border-red-900/50 rounded-lg text-sm text-red-400">
                      ⚠️ {uploadError}
                    </div>
                  )}
                </div>

                {/* Audit Scan Results */}
                {uploadResult && (
                  <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-xl animate-fade-in space-y-6">
                    <div className="flex justify-between items-center border-b border-slate-700 pb-4">
                      <div>
                        <h3 className="text-lg font-bold text-white">Forensic Audit Results</h3>
                        <p className="text-xs text-slate-400 mt-1 font-mono">ID: {uploadResult.id}</p>
                      </div>
                      <span className={`px-3 py-1.5 rounded-full text-xs font-extrabold tracking-wide uppercase ${
                        uploadResult.riskScore >= 0.65 ? "bg-red-950 text-red-400 border border-red-800" :
                        uploadResult.riskScore >= 0.4 ? "bg-yellow-950 text-yellow-400 border border-yellow-800" :
                        "bg-green-950 text-green-400 border border-green-800"
                      }`}>
                        Verdict: {uploadResult.riskDecision}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="bg-slate-900 p-4 rounded-lg border border-slate-800 flex flex-col justify-between">
                        <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Risk Score</span>
                        <div className="mt-2 flex items-baseline gap-2">
                          <span className={`text-4xl font-extrabold ${
                            uploadResult.riskScore >= 0.65 ? "text-red-500" :
                            uploadResult.riskScore >= 0.4 ? "text-yellow-500" :
                            "text-green-500"
                          }`}>
                            {(uploadResult.riskScore * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full bg-slate-800 rounded-full h-2 mt-3">
                          <div
                            className={`h-2 rounded-full ${
                              uploadResult.riskScore >= 0.65 ? "bg-red-500" :
                              uploadResult.riskScore >= 0.4 ? "bg-yellow-500" :
                              "bg-green-500"
                            }`}
                            style={{ width: `${uploadResult.riskScore * 100}%` }}
                          ></div>
                        </div>
                      </div>

                      <div className="bg-slate-900 p-4 rounded-lg border border-slate-800 col-span-2 space-y-3">
                        <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Diagnostic Findings</span>
                        <p className="text-sm font-medium text-slate-200">
                          {uploadResult.metadataSnapshot?.summary || "Analysis completed with no critical warnings."}
                        </p>
                      </div>
                    </div>

                    {/* Metadata items */}
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div className="bg-slate-850 p-3 rounded border border-slate-700">
                        <span className="text-slate-400 block font-semibold mb-1">MIME Content Type</span>
                        <span className="text-slate-200 font-mono">{uploadResult.contentType}</span>
                      </div>
                      <div className="bg-slate-850 p-3 rounded border border-slate-700">
                        <span className="text-slate-400 block font-semibold mb-1">SHA-256 Signature</span>
                        <span className="text-slate-200 font-mono">{uploadResult.sha256Hash}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab: Settings */}
            {activeTab === "settings" && (
              <div className="space-y-6 animate-fade-in">
                <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 shadow-lg">
                  <h2 className="text-xl font-bold text-white mb-4">Forensic Hyper-parameters</h2>
                  <ul className="space-y-4 text-slate-300">
                    <li className="flex justify-between border-b border-slate-700 pb-2">
                      <span>ELA Target JPEG Quality</span>
                      <span className="font-semibold text-white">85%</span>
                    </li>
                    <li className="flex justify-between border-b border-slate-700 pb-2">
                      <span>ELA Amplification Factor</span>
                      <span className="font-semibold text-white">15.0</span>
                    </li>
                    <li className="flex justify-between border-b border-slate-700 pb-2">
                      <span>ELA Anomaly Percentile Threshold</span>
                      <span className="font-semibold text-white">95.0%</span>
                    </li>
                    <li className="flex justify-between border-b border-slate-700 pb-2">
                      <span>FFT DC Exclusion Radius</span>
                      <span className="font-semibold text-white">5 px</span>
                    </li>
                    <li className="flex justify-between border-b border-slate-700 pb-2">
                      <span>FFT Periodicity Sigma Threshold</span>
                      <span className="font-semibold text-white">3.5 σ</span>
                    </li>
                    <li className="flex justify-between pb-2">
                      <span>Composite Weighting</span>
                      <span className="font-semibold text-blue-400">ELA (55%) + FFT (45%)</span>
                    </li>
                  </ul>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Modal: Audit Log Details */}
      {selectedDoc && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-xl max-w-2xl w-full p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
            <div className="flex justify-between items-start border-b border-slate-700 pb-4 mb-4">
              <div>
                <h3 className="text-lg font-bold text-white">{selectedDoc.documentName}</h3>
                <p className="text-xs text-slate-500 font-mono mt-1">UUID: {selectedDoc.id}</p>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="text-slate-400 hover:text-white text-xl"
              >
                ✕
              </button>
            </div>

            <div className="space-y-6 text-sm text-slate-300">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-slate-400 block">SHA-256 Hash</span>
                  <span className="font-mono text-xs text-slate-200">{selectedDoc.sha256Hash}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 block">Ingest Timestamp</span>
                  <span className="text-slate-200">{new Date(selectedDoc.createdAt).toLocaleString()}</span>
                </div>
              </div>

              <div className="p-4 bg-slate-900 border border-slate-750 rounded-lg">
                <span className="text-xs text-slate-400 block">Audit Summary</span>
                <span className="text-slate-200 block mt-1 font-medium">{selectedDoc.metadataSnapshot?.summary || "N/A"}</span>
              </div>

              {/* QR and PDF Diagnostic indicators */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-850 rounded border border-slate-700">
                  <span className="text-xs text-slate-400 block">Secure QR Scan</span>
                  <span className={`text-xs font-bold mt-1 inline-block ${
                    selectedDoc.metadataSnapshot?.qrCodeDetected ? "text-green-400" : "text-slate-500"
                  }`}>
                    {selectedDoc.metadataSnapshot?.qrCodeDetected 
                      ? `Detected: ${selectedDoc.metadataSnapshot.qrCodeData}` 
                      : "None Found"}
                  </span>
                </div>
                <div className="p-3 bg-slate-850 rounded border border-slate-700">
                  <span className="text-xs text-slate-400 block">Cryptographic Signature</span>
                  <span className={`text-xs font-bold mt-1 inline-block ${
                    selectedDoc.metadataSnapshot?.pdfHasSignature ? "text-green-400" : "text-slate-500"
                  }`}>
                    {selectedDoc.metadataSnapshot?.pdfHasSignature 
                      ? "DSC Verified (Signed PDF)" 
                      : "None Found"}
                  </span>
                </div>
              </div>

              {selectedDoc.metadataSnapshot?.pdfMetadata && (
                <div>
                  <span className="text-xs text-slate-400 block mb-2">PDF Document Metadata</span>
                  <div className="bg-slate-900 border border-slate-750 rounded-lg p-4 font-mono text-xs text-slate-300 max-h-40 overflow-y-auto">
                    {Object.entries(selectedDoc.metadataSnapshot.pdfMetadata).map(([key, val]) => (
                      <div key={key} className="flex justify-between border-b border-slate-800 py-1">
                        <span className="text-blue-400">{key}</span>
                        <span className="text-slate-200">{val}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end border-t border-slate-700 pt-4 mt-6">
              <button
                onClick={() => setSelectedDoc(null)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-semibold transition-colors duration-150"
              >
                Close Audit Log
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}