import { 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
  Info, 
  Cpu, 
  Sliders, 
  ArrowRight,
} from 'lucide-react';
import type { DocumentAnalysisResponse, UnifiedRiskTier } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
  onScrollToML: () => void;
  onScrollToEvidence: () => void;
}

export function InvestigationSummaryCard({
  analysis,
  onScrollToML,
  onScrollToEvidence,
}: Props) {
  const tier = analysis.unified_risk_tier as UnifiedRiskTier;
  const isHighRisk = tier === 'HIGH_RISK';
  const isSuspicious = tier === 'SUSPICIOUS';
  const isLowRisk = tier === 'LOW_RISK';

  // 1. Final Assessment Label and Color Palette
  const tierLabel = isHighRisk 
    ? 'HIGH RISK' 
    : isSuspicious 
      ? 'REQUIRES REVIEW' 
      : isLowRisk 
        ? 'LOW RISK' 
        : 'UNVERIFIED';

  const tierDescription = isHighRisk
    ? 'Significant manipulation indicators detected. The document exhibits elevated statistical or visual anomalies consistent with digital tampering.'
    : isSuspicious
      ? 'Borderline or conflicting forensic indicators identified across analytical tracks. Certain areas warrant manual examiner review.'
      : isLowRisk
        ? 'Your document shows relatively few indicators of possible manipulation. Physical substrate features align with authentic reference baselines.'
        : 'The available results do not support a conclusive risk classification. Please review limitations and consider examiner review.';

  // 2. ML Screening Score vs Composite Assessment
  // Raw ML probability from Random Forest (0.0 - 1.0)
  const rawProbability = analysis.raw_ml?.forgery_probability ?? 
                         analysis.track_1_ml?.forgery_probability ?? null;
  const mlPercent = rawProbability !== null ? Math.round(rawProbability * 100) : null;
  const mlThreshold = 40.0; // T = 0.40

  // Composite Heuristic Score (0 - 100)
  const compositeScore = Math.round(analysis.composite_risk_score || 0);

  // 3. Recommended Next Action
  const regionCount = analysis.detected_regions?.length || 0;
  const getRecommendedAction = () => {
    if (tier === 'UNKNOWN') {
      return 'The available results do not support an assessment. Review pipeline limitations and missing evidence, then request examiner review.';
    }
    if (isHighRisk) {
      return 'Do not accept this document as authentic without physical inspection. Verify author signatures, organizational seals, and original paper substrate.';
    }
    if (isSuspicious || regionCount > 0) {
      return `Perform manual examiner inspection on the ${regionCount > 0 ? regionCount : 'flagged'} suspicious region(s) below. Text verification was unavailable in this environment and should be manually read.`;
    }
    return 'Low risk of physical substrate tampering detected. Automated text checks were unavailable and should be visually reviewed if textual content is legally binding.';
  };

  return (
    <div
      className={`rounded-2xl border p-6 lg:p-8 shadow-xl transition-all ${
        isHighRisk
          ? 'border-red-500/40 bg-gradient-to-br from-red-950/20 via-ink-panel to-ink-panel'
          : isSuspicious
            ? 'border-amber-500/40 bg-gradient-to-br from-amber-950/20 via-ink-panel to-ink-panel'
            : isLowRisk
              ? 'border-emerald-500/40 bg-gradient-to-br from-emerald-950/20 via-ink-panel to-ink-panel'
              : 'border-slate-700 bg-ink-panel'
      }`}
    >
      {/* Top Banner: Final Assessment */}
      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 pb-6 border-b border-ink-border">
        <div className="space-y-2 flex-1">
          <div className="flex items-center gap-2.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
              Investigation Verdict
            </span>
            <span
              className={`text-xs font-bold px-3 py-1 rounded-full border ${
                isHighRisk
                  ? 'bg-red-950/80 text-red-400 border-red-800'
                  : isSuspicious
                    ? 'bg-amber-950/80 text-amber-300 border-amber-800'
                    : isLowRisk
                      ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800'
                      : 'bg-slate-900 text-slate-300 border-slate-700'
              }`}
            >
              {tierLabel}
            </span>
          </div>

          <h2 className="text-2xl font-bold text-white tracking-tight">
            {isHighRisk
              ? 'Elevated Forgery Risk Identified'
              : isSuspicious
                ? 'Examination Requires Review'
                : isLowRisk
                  ? 'Document Shows Low Manipulation Indicators'
                  : 'Investigation Outcome Unverified'}
          </h2>

          <p className="text-sm text-gray-300 leading-relaxed max-w-3xl">
            {tierDescription}
          </p>
        </div>

        {/* Visual Verdict Icon */}
        <div className="shrink-0 hidden lg:flex items-center justify-center w-16 h-16 rounded-2xl bg-ink-base border border-ink-border shadow-inner">
          {isHighRisk ? (
            <ShieldAlert size={36} className="text-red-400" />
          ) : isSuspicious ? (
            <AlertTriangle size={36} className="text-amber-400" />
          ) : isLowRisk ? (
            <ShieldCheck size={36} className="text-emerald-400" />
          ) : (
            <Info size={36} className="text-slate-400" />
          )}
        </div>
      </div>

      {/* Middle: Distinct Score Readouts (ML vs Composite) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
        {/* Card 1: Machine Learning Screening Score */}
        <div className="bg-ink-base/80 border border-ink-border rounded-xl p-5 space-y-3 relative overflow-hidden group hover:border-brand/40 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
              <Cpu size={16} className="text-brand" /> 1. Machine Learning Screening Score
            </span>
            <span className="text-[10px] font-mono text-gray-400 bg-ink-panel px-2 py-0.5 rounded border border-ink-border">
              Random Forest
            </span>
          </div>

          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-bold font-mono text-white">
              {mlPercent !== null ? `${mlPercent}%` : 'N/A'}
            </span>
            <span className="text-xs text-gray-400">
              Threshold: <strong className="text-gray-200">40.0% (T=0.40)</strong>
            </span>
          </div>

          <p className="text-xs text-gray-300 leading-relaxed">
            {mlPercent !== null ? (
              mlPercent >= mlThreshold ? (
                <span className="text-red-300 font-medium">
                  Screening score exceeds decision threshold (T=0.40). Raw model classification: <strong>FORGED</strong>.
                </span>
              ) : (
                <span className="text-emerald-300 font-medium">
                  Screening score is below decision threshold (T=0.40). Raw model classification: <strong>AUTHENTIC</strong>.
                </span>
              )
            ) : (
              'Raw model inference probability is currently unavailable.'
            )}
          </p>

          <div className="text-[11px] text-gray-400 pt-1 border-t border-ink-border/50 flex items-center justify-between">
            <span>Derived strictly from 18 physical substrate metrics.</span>
            <button
              onClick={onScrollToML}
              className="text-brand hover:underline font-semibold flex items-center gap-1"
            >
              Explain Model <ArrowRight size={11} />
            </button>
          </div>
        </div>

        {/* Card 2: Composite Heuristic Assessment Index */}
        <div className="bg-ink-base/80 border border-ink-border rounded-xl p-5 space-y-3 relative overflow-hidden group hover:border-brand/40 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
              <Sliders size={16} className="text-cyan-400" /> 2. Composite Heuristic Assessment
            </span>
            <span className="text-[10px] font-mono text-gray-400 bg-ink-panel px-2 py-0.5 rounded border border-ink-border">
              Synthesis Arbiter
            </span>
          </div>

          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-bold font-mono text-white">
              {tier === 'UNKNOWN' ? 'N/A' : `${compositeScore}/100`}
            </span>
            <span className="text-xs text-gray-400">
              Status: <strong className="text-gray-200">{tierLabel}</strong>
            </span>
          </div>

          <p className="text-xs text-gray-300 leading-relaxed">
            Combines physical ML inference with Error Level Analysis, duplicate region arbiter, and file container metadata into a unified score.
          </p>

          <div className="text-[11px] text-gray-400 pt-1 border-t border-ink-border/50 flex items-center justify-between">
            <span className="italic">Display index, not an ML probability.</span>
            <button
              onClick={onScrollToEvidence}
              className="text-cyan-400 hover:underline font-semibold flex items-center gap-1"
            >
              View Synthesis <ArrowRight size={11} />
            </button>
          </div>
        </div>
      </div>

      {/* Bottom: Recommended Action Box */}
      <div className="bg-ink-base/90 border border-ink-border rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <p className="text-[11px] font-bold uppercase tracking-wider text-gray-400">
            Recommended Operational Next Step
          </p>
          <p className="text-xs text-gray-200 leading-relaxed">
            {getRecommendedAction()}
          </p>
        </div>

        <button
          onClick={onScrollToEvidence}
          className="px-4 py-2 bg-ink-panel hover:bg-ink-hover border border-ink-border text-gray-200 rounded-lg text-xs font-semibold shrink-0 transition-colors"
        >
          Inspect Evidence Details
        </button>
      </div>
    </div>
  );
}
