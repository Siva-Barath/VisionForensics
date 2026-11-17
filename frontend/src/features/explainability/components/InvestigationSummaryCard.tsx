import { 
  ShieldCheck, 
  ShieldAlert, 
  AlertTriangle, 
} from 'lucide-react';
import type { DocumentAnalysisResponse, UnifiedRiskTier } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
  onScrollToML?: () => void;
  onScrollToEvidence?: () => void;
}

export function InvestigationSummaryCard({
  analysis,
}: Props) {
  const tier = analysis.unified_risk_tier as UnifiedRiskTier;
  const isHighRisk = tier === 'HIGH_RISK';
  const isSuspicious = tier === 'SUSPICIOUS';
  const isLowRisk = tier === 'LOW_RISK';

  // Verdict style configurations matching reference image
  let bgClass = 'bg-[#EBF9F1] border-[#D1F2DE]';
  let textClass = 'text-[#159B55]';
  let Icon = ShieldCheck;
  let verdictLabel = 'LOW RISK';
  let verdictTitle = 'Document shows low manipulation indicators.';
  let verdictDesc =
    'The ML screening score is below the configured threshold, and no significant signs of tampering were detected.';

  if (isHighRisk) {
    bgClass = 'bg-[#FDF2F2] border-[#FAD8D8]';
    textClass = 'text-[#DC4545]';
    Icon = ShieldAlert;
    verdictLabel = 'HIGH RISK';
    verdictTitle = 'Significant manipulation indicators detected.';
    verdictDesc =
      'The ML screening score exceeds the configured threshold (T = 0.40), or significant physical tampering was identified.';
  } else if (isSuspicious) {
    bgClass = 'bg-[#FFF8EC] border-[#FFE8BF]';
    textClass = 'text-[#E9A12A]';
    Icon = AlertTriangle;
    verdictLabel = 'REQUIRES REVIEW';
    verdictTitle = 'Document requires analyst review.';
    verdictDesc =
      'Borderline or conflicting forensic indicators detected across analytical tracks. Manual examiner inspection is recommended.';
  } else if (!isLowRisk) {
    bgClass = 'bg-[#F8F9FF] border-[#E6E5F0]';
    textClass = 'text-[#73758B]';
    Icon = AlertTriangle;
    verdictLabel = 'UNVERIFIED';
    verdictTitle = 'Inconclusive forensic assessment.';
    verdictDesc =
      'The available pipeline results do not support a conclusive risk classification. Review technical details and examiner notes.';
  }

  return (
    <div className={`rounded-2xl border p-6 ${bgClass} shadow-sm transition-all`}>
      <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
        {/* Left Side: Verdict Badge & Icon */}
        <div className="flex items-center gap-4 shrink-0 pr-0 md:pr-6 border-b md:border-b-0 md:border-r border-black/5 pb-4 md:pb-0 w-full md:w-auto">
          <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-white shadow-sm shrink-0">
            <Icon size={34} className={textClass} />
          </div>
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#73758B] block">
              Final Verdict
            </span>
            <span className={`text-2xl md:text-3xl font-extrabold tracking-tight ${textClass} block leading-tight`}>
              {verdictLabel}
            </span>
          </div>
        </div>

        {/* Right Side: Plain-English Explanation */}
        <div className="flex-1 space-y-1">
          <h2 className="text-base font-bold text-[#17172F] tracking-tight">
            {verdictTitle}
          </h2>
          <p className="text-xs text-[#5A5D72] leading-relaxed max-w-3xl">
            {verdictDesc}
          </p>
        </div>
      </div>
    </div>
  );
}
