import React, { useState } from 'react';
import {
  FileText,
  Download,
  X,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  FileCheck2,
} from 'lucide-react';
import { generateReport, getReportDownloadUrl } from '@/services/api';
import type { ReportDetailResponse } from '@/types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  documentId: string;
  documentFilename: string;
  unifiedRiskTier: string;
  compositeScore: number;
}

export const GenerateReportModal: React.FC<Props> = ({
  isOpen,
  onClose,
  documentId,
  documentFilename,
  unifiedRiskTier,
  compositeScore,
}) => {
  const [title, setTitle] = useState(`Forensic Examination: ${documentFilename}`);
  const [analystNotes, setAnalystNotes] = useState('');
  const [includeEvidenceImages, setIncludeEvidenceImages] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ReportDetailResponse | null>(null);

  if (!isOpen) return null;

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    setError(null);

    try {
      const res = await generateReport({
        document_id: documentId,
        title: title.trim(),
        analyst_notes: analystNotes.trim() || undefined,
        include_evidence_images: includeEvidenceImages,
      });
      setReport(res);
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err?.message ||
        'Failed to compile forensic report.';
      setError(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!report) return;
    const url = getReportDownloadUrl(report.report_id);
    window.open(url, '_blank');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-ink-panel border border-ink-border rounded-xl shadow-2xl max-w-lg w-full overflow-hidden text-gray-200 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink-border bg-ink-bg">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-brand/20 border border-brand text-brand flex items-center justify-center">
              <FileText size={18} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide">
                EXPORT FORENSIC INVESTIGATION REPORT
              </h2>
              <p className="text-[11px] text-gray-400 font-mono">
                Publication-Quality Defense-Grade PDF Dossier
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white p-1 rounded transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-red-950/40 border border-red-800 rounded-lg flex items-start gap-2.5 text-xs text-red-300">
              <AlertCircle size={15} className="text-red-400 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {report ? (
            // Success & Download View
            <div className="space-y-4 text-center py-4">
              <div className="w-14 h-14 rounded-full bg-emerald-950/60 border border-emerald-600/80 text-emerald-400 flex items-center justify-center mx-auto">
                <CheckCircle2 size={32} />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Forensic Dossier Compiled Successfully</h3>
                <p className="text-xs text-gray-400 font-mono mt-1">
                  Report ID: <span className="text-brand font-bold">{report.report_number}</span>
                </p>
              </div>

              <div className="bg-ink-bg border border-ink-border rounded-lg p-3 text-left font-mono text-xs space-y-1.5">
                <div className="flex justify-between text-gray-400">
                  <span>Cryptographic SHA-256:</span>
                  <span className="text-gray-200 truncate w-48 text-right" title={report.sha256_hash}>
                    {report.sha256_hash.slice(0, 20)}...
                  </span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>File Size:</span>
                  <span className="text-gray-200">{(report.file_size_bytes / 1024).toFixed(1)} KB</span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>Page Count:</span>
                  <span className="text-gray-200">{report.page_count} Pages</span>
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleDownload}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-brand hover:bg-brand-hover text-white rounded-lg text-xs font-bold uppercase tracking-wider transition-colors shadow-md"
                >
                  <Download size={15} /> Download PDF Report
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2.5 bg-ink-bg border border-ink-border hover:bg-ink-hover text-gray-300 rounded-lg text-xs font-medium transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          ) : (
            // Configuration Form
            <form onSubmit={handleGenerate} className="space-y-4">
              {/* Exhibit Summary Pill */}
              <div className="p-3 bg-ink-bg border border-ink-border rounded-lg flex items-center justify-between text-xs font-mono">
                <div>
                  <span className="text-gray-400">Target Exhibit: </span>
                  <span className="text-white font-bold">{documentFilename}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] bg-brand/20 text-brand border border-brand/40">
                    {unifiedRiskTier}
                  </span>
                  <span className="text-gray-400">({compositeScore.toFixed(0)}/100)</span>
                </div>
              </div>

              {/* Report Title */}
              <div>
                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1 font-mono">
                  Report Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  className="w-full bg-ink-bg border border-ink-border rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-brand font-sans"
                />
              </div>

              {/* Analyst Observations & Notes */}
              <div>
                <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1 font-mono">
                  Analyst Observations & Notes (Optional)
                </label>
                <textarea
                  value={analystNotes}
                  onChange={(e) => setAnalystNotes(e.target.value)}
                  rows={3}
                  placeholder="Enter manual forensic observations, corroborating exhibit context, or examiner caveats..."
                  className="w-full bg-ink-bg border border-ink-border rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-brand font-sans resize-none placeholder-gray-500"
                />
                <p className="text-[10px] text-gray-400 mt-1">
                  Analyst notes are clearly demarcated in Section 9 as subjective examiner observations.
                </p>
              </div>

              {/* Toggles */}
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="includeImages"
                  checked={includeEvidenceImages}
                  onChange={(e) => setIncludeEvidenceImages(e.target.checked)}
                  className="rounded accent-brand cursor-pointer"
                />
                <label htmlFor="includeImages" className="text-xs text-gray-300 cursor-pointer">
                  Include region coordinates, ELA breakdowns, and two-track decision trace
                </label>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-ink-border">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isGenerating}
                  className="px-4 py-2 bg-ink-bg border border-ink-border hover:bg-ink-hover text-gray-300 rounded-lg text-xs font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="flex items-center gap-2 px-5 py-2 bg-brand hover:bg-brand-hover disabled:opacity-50 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition-colors shadow-md"
                >
                  {isGenerating ? (
                    <>
                      <RefreshCw size={14} className="animate-spin" /> Compiling PDF...
                    </>
                  ) : (
                    <>
                      <FileCheck2 size={14} /> Generate PDF
                    </>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
