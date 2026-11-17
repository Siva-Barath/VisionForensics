import { useState } from 'react';
import { 
  FileText, 
  Clock, 
  GitCompare, 
  Download, 
  Copy, 
  Check, 
} from 'lucide-react';
import Badge from '@/components/ui/Badge';
import type { DocumentAnalysisResponse, UnifiedRiskTier } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
  pageCount: number;
  onOpenReportModal: () => void;
  onNavigateComparison: () => void;
}

export function DocumentIdentityHeader({
  analysis,
  pageCount,
  onOpenReportModal,
  onNavigateComparison,
}: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopyId = () => {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(analysis.document_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const tier = analysis.unified_risk_tier as UnifiedRiskTier;
  const isHighRisk = tier === 'HIGH_RISK';
  const isSuspicious = tier === 'SUSPICIOUS';
  const isLowRisk = tier === 'LOW_RISK';

  const riskBadgeVariant = isHighRisk ? 'critical' : isSuspicious ? 'high' : isLowRisk ? 'verified' : 'low';
  const tierLabel = isHighRisk ? 'HIGH RISK' : isSuspicious ? 'REQUIRES REVIEW' : isLowRisk ? 'LOW RISK' : 'UNVERIFIED';

  return (
    <div className="bg-ink-panel border border-ink-border rounded-xl p-5 shadow-lg">
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        {/* Left: Document details */}
        <div className="flex items-start gap-4 min-w-0">
          <div className="w-12 h-12 rounded-lg bg-ink-base border border-ink-border flex items-center justify-center shrink-0 text-brand">
            <FileText size={24} />
          </div>

          <div className="min-w-0 space-y-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-xl font-bold text-white tracking-tight truncate max-w-xl" title={analysis.original_filename}>
                {analysis.original_filename}
              </h1>
              <Badge variant={riskBadgeVariant} label={tierLabel} size="sm" />
            </div>

            <div className="flex items-center gap-3 text-xs text-gray-400 font-mono flex-wrap">
              <span className="bg-ink-base px-2 py-0.5 rounded border border-ink-border text-gray-300">
                {analysis.file_type.toUpperCase()}
              </span>
              <span>
                {pageCount} {pageCount === 1 ? 'Page' : 'Pages'}
              </span>
              {analysis.processing_time_ms && (
                <span className="flex items-center gap-1">
                  <Clock size={12} className="text-gray-500" />
                  {analysis.processing_time_ms.toFixed(0)} ms
                </span>
              )}
              <span className="text-gray-500">|</span>
              <button
                onClick={handleCopyId}
                className="inline-flex items-center gap-1 hover:text-white transition-colors"
                title="Click to copy Exhibit UUID"
              >
                <span>ID: {analysis.document_id.slice(0, 8)}...</span>
                {copied ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
              </button>
            </div>
          </div>
        </div>

        {/* Right: Quick actions */}
        <div className="flex items-center gap-2.5 flex-wrap w-full lg:w-auto justify-start lg:justify-end">
          <a
            href={`/api/v1/documents/${analysis.document_id}/original`}
            target="_blank"
            rel="noreferrer"
            className="px-3 py-2 bg-ink-base border border-ink-border hover:bg-ink-hover text-gray-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Download size={13} /> Original
          </a>

          <button
            onClick={onNavigateComparison}
            className="px-3.5 py-2 bg-ink-base border border-ink-border hover:bg-ink-hover text-gray-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <GitCompare size={14} className="text-brand" /> Compare Exhibit
          </button>

          <button
            onClick={onOpenReportModal}
            className="px-4 py-2 bg-brand hover:bg-brand-hover text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md"
          >
            <Download size={14} /> Export PDF Report
          </button>
        </div>
      </div>
    </div>
  );
}
