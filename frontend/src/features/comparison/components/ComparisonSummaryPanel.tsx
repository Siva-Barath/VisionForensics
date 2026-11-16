import React from 'react';
import {
  ShieldAlert,
  Percent,
  Activity,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Info,
} from 'lucide-react';
import type { ComparisonMetrics, ComparisonMetadataDiff, ComparisonSummary } from '@/types';

interface Props {
  metrics: ComparisonMetrics;
  metadataDiff: ComparisonMetadataDiff;
  summary: ComparisonSummary;
}

export const ComparisonSummaryPanel: React.FC<Props> = ({
  metrics,
  metadataDiff,
  summary,
}) => {
  const simPercent = Math.round(metrics.similarity_score * 100);

  const getVerdictBadge = (verdict: string) => {
    switch (verdict) {
      case 'IDENTICAL':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-emerald-950/80 text-emerald-400 border border-emerald-800 flex items-center gap-1.5">
            <CheckCircle2 size={13} /> IDENTICAL
          </span>
        );
      case 'LOCALIZED_DIFFERENCES':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-amber-950/80 text-amber-400 border border-amber-800 flex items-center gap-1.5">
            <AlertTriangle size={13} /> LOCALIZED DIFFERENCES
          </span>
        );
      case 'SIGNIFICANT_DIFFERENCES':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-red-950/80 text-red-400 border border-red-800 flex items-center gap-1.5">
            <ShieldAlert size={13} /> SIGNIFICANT DIFFERENCES
          </span>
        );
      case 'INCONCLUSIVE_ALIGNMENT':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-purple-950/80 text-purple-400 border border-purple-800 flex items-center gap-1.5">
            <Info size={13} /> INCONCLUSIVE ALIGNMENT
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-gray-800 text-gray-300 border border-gray-700">
            {verdict}
          </span>
        );
    }
  };

  return (
    <div className="bg-ink-panel border-t border-ink-border p-4 text-xs">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-start">
        {/* Metric 1: Overall Similarity */}
        <div className="bg-ink-bg border border-ink-border rounded-lg p-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-gray-400 font-mono flex items-center gap-1">
              <Percent size={13} className="text-brand" /> Overall Similarity
            </span>
            {getVerdictBadge(summary.verdict_category)}
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-white">{simPercent}%</span>
            <span className="text-gray-400 text-[11px] font-mono">
              (Diff: {metrics.difference_percentage}%)
            </span>
          </div>
          <div className="w-full bg-ink-panel rounded-full h-2 mt-2 overflow-hidden border border-ink-border">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                simPercent > 90
                  ? 'bg-emerald-500'
                  : simPercent > 60
                  ? 'bg-amber-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${simPercent}%` }}
            />
          </div>
        </div>

        {/* Metric 2: Structural Similarity (SSIM) */}
        <div className="bg-ink-bg border border-ink-border rounded-lg p-3">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-gray-400 font-mono flex items-center gap-1">
              <Activity size={13} className="text-brand" /> Structural SSIM
            </span>
            <span className="font-mono text-white text-xs font-bold">{metrics.ssim_score.toFixed(4)}</span>
          </div>
          <p className="text-gray-400 text-[11px] leading-relaxed">
            Measures structural luminance, contrast, and texture correlation after registration.
          </p>
          <div className="mt-2 font-mono text-[11px] text-gray-400 flex justify-between">
            <span>Differing Pixels:</span>
            <span className="text-gray-200">
              {metrics.differing_pixels.toLocaleString()} / {metrics.total_pixels.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Metric 3: Exhibit Metadata Comparison Table */}
        <div className="bg-ink-bg border border-ink-border rounded-lg p-3 font-mono">
          <span className="text-gray-400 flex items-center gap-1 mb-2 font-semibold">
            <FileSpreadsheet size={13} className="text-brand" /> Metadata Differential
          </span>
          <div className="space-y-1 text-[11px]">
            <div className="flex justify-between">
              <span className="text-gray-400">Dimensions:</span>
              <span className={metadataDiff.dimension_match ? 'text-emerald-400' : 'text-amber-400'}>
                {metadataDiff.document_a.dimensions.join('×')} vs {metadataDiff.document_b.dimensions.join('×')} px
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Page Counts:</span>
              <span className={metadataDiff.page_count_match ? 'text-emerald-400' : 'text-amber-400'}>
                {metadataDiff.document_a.page_count} vs {metadataDiff.document_b.page_count}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">File Formats:</span>
              <span className={metadataDiff.format_match ? 'text-emerald-400' : 'text-amber-400'}>
                {metadataDiff.document_a.file_type.toUpperCase()} / {metadataDiff.document_b.file_type.toUpperCase()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">SHA-256 Match:</span>
              <span className={metadataDiff.hash_match ? 'text-emerald-400 font-bold' : 'text-gray-400'}>
                {metadataDiff.hash_match ? 'Identical Hashes' : 'Distinct Hashes'}
              </span>
            </div>
          </div>
        </div>

        {/* Metric 4: Defense-Grade Forensic Caveat */}
        <div className="bg-amber-950/20 border border-amber-900/50 rounded-lg p-3">
          <div className="flex items-center gap-1.5 text-amber-400 font-mono font-semibold mb-1">
            <AlertTriangle size={14} />
            <span>Forensic Evidentiary Caveat</span>
          </div>
          <p className="text-amber-200/90 text-[11px] leading-relaxed">
            {summary.forensic_caveat ||
              'Visual differences alone do not prove forgery. Document variations may arise from legitimate revisions, optical scanner tolerances, or formatting adjustments.'}
          </p>
        </div>
      </div>
    </div>
  );
};
