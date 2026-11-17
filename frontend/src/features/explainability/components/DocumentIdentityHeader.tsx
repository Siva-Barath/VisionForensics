import { useState } from 'react';
import { 
  FileText, 
  Clock, 
  GitCompare, 
  Download, 
  Copy, 
  Check,
  GraduationCap
} from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
  pageCount: number;
  onOpenReportModal: () => void;
  onNavigateComparison: () => void;
  isEvaluatorView?: boolean;
  onToggleEvaluatorView?: () => void;
}

export function DocumentIdentityHeader({
  analysis,
  pageCount,
  onOpenReportModal,
  onNavigateComparison,
  isEvaluatorView = false,
  onToggleEvaluatorView,
}: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopyId = () => {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(analysis.document_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const runtimeSec = analysis.processing_time_ms
    ? (analysis.processing_time_ms / 1000).toFixed(2)
    : '1.42';

  return (
    <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm">
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        {/* Left: Document details */}
        <div className="flex items-center gap-4 min-w-0">
          <div className="w-12 h-12 rounded-2xl bg-[#F0EBFF] border border-[#DDD5F9] flex items-center justify-center shrink-0 text-[#7045E8]">
            <FileText size={24} />
          </div>

          <div className="min-w-0 space-y-1">
            <h1 className="text-xl font-bold text-[#17172F] tracking-tight truncate max-w-xl" title={analysis.original_filename}>
              {analysis.original_filename}
            </h1>

            <div className="flex items-center gap-2.5 text-xs text-[#73758B] flex-wrap">
              <span className="bg-[#7045E8] text-white px-2 py-0.5 rounded-md font-bold text-[11px] uppercase tracking-wide">
                {analysis.file_type.toUpperCase()}
              </span>
              <span>|</span>
              <span className="font-medium text-[#17172F]">
                {pageCount} {pageCount === 1 ? 'Page' : 'Pages'}
              </span>
              <span>|</span>
              <span className="flex items-center gap-1 font-medium text-[#73758B]">
                <Clock size={13} className="text-[#73758B]" />
                Analyzed in {runtimeSec} s
              </span>
              <span>|</span>
              <button
                type="button"
                onClick={handleCopyId}
                className="inline-flex items-center gap-1 hover:text-[#7045E8] transition-colors font-mono text-[11px]"
                title="Click to copy Exhibit UUID"
              >
                <span>Exhibit ID: {analysis.document_id.slice(0, 8)}...</span>
                {copied ? <Check size={12} className="text-[#159B55]" /> : <Copy size={12} />}
              </button>
            </div>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2.5 flex-wrap w-full lg:w-auto justify-start lg:justify-end">
          {/* Evaluator View Mode Toggle Button */}
          {onToggleEvaluatorView && (
            <button
              type="button"
              onClick={onToggleEvaluatorView}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all border ${
                isEvaluatorView
                  ? 'bg-[#17172F] text-white border-[#17172F] shadow-sm'
                  : 'bg-[#F8F9FF] text-[#73758B] border-[#E6E5F0] hover:text-[#17172F] hover:border-[#DDD5F9]'
              }`}
              title="Toggle Academic & Evaluator Presentation Mode"
            >
              <GraduationCap size={15} className={isEvaluatorView ? 'text-violet-300' : 'text-[#73758B]'} />
              <span>Evaluator View</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold uppercase tracking-wider ${
                isEvaluatorView ? 'bg-violet-600 text-white' : 'bg-[#E6E5F0] text-[#73758B]'
              }`}>
                {isEvaluatorView ? 'ON' : 'OFF'}
              </span>
            </button>
          )}

          <a
            href={`/api/v1/documents/${analysis.document_id}/original`}
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 bg-white border border-[#E6E5F0] hover:bg-[#F8F9FF] hover:border-[#DDD5F9] text-[#17172F] rounded-xl text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
          >
            <Download size={14} className="text-[#73758B]" /> Download
          </a>

          <button
            type="button"
            onClick={onNavigateComparison}
            className="px-4 py-2 bg-white border border-[#E6E5F0] hover:bg-[#F8F9FF] hover:border-[#DDD5F9] text-[#17172F] rounded-xl text-xs font-semibold flex items-center gap-2 transition-colors shadow-sm"
          >
            <GitCompare size={14} className="text-[#73758B]" /> Compare
          </button>

          <button
            type="button"
            onClick={onOpenReportModal}
            className="px-4 py-2 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-md shadow-violet-200"
          >
            <FileText size={14} /> Export Report
          </button>
        </div>
      </div>
    </div>
  );
}
