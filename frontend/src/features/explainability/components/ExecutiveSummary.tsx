import React from 'react';
import { AlertTriangle, ShieldAlert, CheckCircle2, Info } from 'lucide-react';
import Card from '@/components/ui/Card';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
}

export const ExecutiveSummary: React.FC<Props> = ({ analysis }) => {
  const tier = analysis.unified_risk_tier;
  const isHighRisk = tier === 'HIGH_RISK';
  const isSuspicious = tier === 'SUSPICIOUS';
  const isLowRisk = tier === 'LOW_RISK';

  const tierColor = isHighRisk 
    ? 'text-severity-critical' 
    : isSuspicious 
    ? 'text-severity-high' 
    : isLowRisk 
    ? 'text-severity-low' 
    : 'text-gray-400';

  const tierBg = isHighRisk 
    ? 'bg-severity-critical/20' 
    : isSuspicious 
    ? 'bg-severity-high/20' 
    : isLowRisk 
    ? 'bg-severity-low/20' 
    : 'bg-gray-700/20';

  const TierIcon = isHighRisk 
    ? ShieldAlert 
    : isSuspicious 
    ? AlertTriangle 
    : isLowRisk 
    ? CheckCircle2 
    : Info;

  const topFeatures = Object.entries(analysis.track_1_ml.top_contributing_features || {});

  return (
    <Card title="Executive Forensic Summary">
      <div className="p-6 space-y-6">
        {/* Risk & Verdict Banner */}
        <div className="flex items-start gap-4 p-4 rounded-sm bg-ink-base border border-ink-border">
          <div className={`w-12 h-12 rounded-sm ${tierBg} flex items-center justify-center shrink-0`}>
            <TierIcon size={26} className={tierColor} />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <span className={`text-lg font-bold uppercase tracking-wider ${tierColor}`}>
                {analysis.overall_verdict}
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded-sm bg-ink-panel border border-ink-border text-gray-300">
                Tier: {analysis.unified_risk_tier}
              </span>
            </div>
            <p className="text-xs text-gray-300 leading-relaxed font-sans">
              {analysis.risk_description}
            </p>
          </div>
        </div>

        {/* Calibrated Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Track 1: ML Model Probability */}
          <div className="p-3 bg-ink-base border border-ink-border rounded-sm space-y-1">
            <p className="text-[10px] font-bold text-muted uppercase tracking-wider">
              Track 1: ML Forgery Probability
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-mono font-bold text-brand">
                {analysis.track_1_ml.forgery_probability !== null 
                  ? `${(analysis.track_1_ml.forgery_probability * 100).toFixed(1)}%` 
                  : 'N/A'}
              </span>
              <span className="text-[10px] text-gray-400 font-mono">
                (T={analysis.track_1_ml.operational_threshold.toFixed(2)})
              </span>
            </div>
            <p className="text-[10px] text-muted">
              Classified: <strong className="text-gray-200">{analysis.track_1_ml.predicted_class || 'N/A'}</strong>
            </p>
          </div>

          {/* Track 2: Symbolic Severity Score */}
          <div className="p-3 bg-ink-base border border-ink-border rounded-sm space-y-1">
            <p className="text-[10px] font-bold text-muted uppercase tracking-wider">
              Track 2: Symbolic Severity
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-mono font-bold text-gray-200">
                {analysis.track_2_symbolic.symbolic_severity_score.toFixed(1)}
              </span>
              <span className="text-[10px] text-gray-400 font-mono">/ 100</span>
            </div>
            <p className="text-[10px] text-muted">
              Findings: <strong className="text-gray-200">{analysis.track_2_symbolic.symbolic_evidence.length}</strong>
            </p>
          </div>

          {/* Composite Display Score */}
          <div className="p-3 bg-ink-base border border-ink-border rounded-sm space-y-1">
            <p className="text-[10px] font-bold text-muted uppercase tracking-wider">
              Composite Display Score
            </p>
            <div className="flex items-baseline gap-2">
              <span className={`text-2xl font-mono font-bold ${tierColor}`}>
                {analysis.composite_risk_score.toFixed(1)}
              </span>
              <span className="text-[10px] text-gray-400 font-mono">/ 100</span>
            </div>
            <p className="text-[10px] text-muted">
              Heuristic max display (not a joint probability)
            </p>
          </div>
        </div>

        {/* Additional Track 3 & Track 4 Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Track 3: Visual Evidence Arbiter */}
          <div className="p-3 bg-ink-base border border-ink-border rounded-sm space-y-1">
            <p className="text-[10px] font-bold text-muted uppercase tracking-wider">
              Track 3: Visual Evidence Arbiter (REM-03)
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-mono font-bold text-gray-200">
                {analysis.track_3_visual?.available ? `${analysis.track_3_visual.detected_clusters} Cluster(s)` : 'Standby'}
              </span>
              <span className="text-[10px] text-gray-400 font-mono">
                {analysis.track_3_visual?.total_inlier_matches ? `(${analysis.track_3_visual.total_inlier_matches} inliers)` : ''}
              </span>
            </div>
            <p className="text-[10px] text-muted">
              Visual Tier: <strong className="text-gray-200">{analysis.track_3_visual?.visual_tier || 'LOW_RISK'}</strong>
              {analysis.track_3_visual?.copy_move_confirmed && ' — Cloned patches detected'}
            </p>
          </div>

          {/* Track 4: Compression Qualification */}
          <div className="p-3 bg-ink-base border border-ink-border rounded-sm space-y-1">
            <p className="text-[10px] font-bold text-muted uppercase tracking-wider">
              Track 4: Compression Qualification (REM-04)
            </p>
            <div className="flex items-baseline gap-2">
              <span className="text-lg font-mono font-bold text-gray-200">
                {analysis.compression_qualification?.is_jpeg 
                  ? `Quality ~${analysis.compression_qualification.estimated_quality?.toFixed(0) || 'N/A'}` 
                  : 'Lossless Substrate'}
              </span>
              {analysis.compression_qualification?.is_heavily_compressed && (
                <span className="text-[10px] text-amber-400 font-mono">
                  (Heavy Compression)
                </span>
              )}
            </div>
            <p className="text-[10px] text-muted truncate">
              {analysis.compression_qualification?.compression_notice || 'Standard compression characteristics'}
            </p>
          </div>
        </div>

        {/* Top Contributing Forensic Features */}
        <div>
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Top Physical Forensic Indicators (ML Deviations)
          </h4>
          
          {topFeatures.length === 0 ? (
            <p className="text-xs text-muted font-mono bg-ink-base p-3 rounded-sm border border-ink-border">
              No significant feature deviations from authentic baselines detected.
            </p>
          ) : (
            <div className="space-y-3">
              {topFeatures.map(([featKey, featVal]) => (
                <div key={featKey} className="bg-ink-base border border-ink-border p-2.5 rounded-sm">
                  <div className="flex justify-between text-xs font-mono mb-1">
                    <span className="text-gray-300 font-medium">{featKey}</span>
                    <span className="text-brand font-bold">{featVal.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
          <p className="text-[10px] text-muted mt-2 italic">
            Note: Top indicators represent statistical deviations from authentic baseline medians for forensic decision support. They do not constitute definitive legal proof of manipulation.
          </p>
        </div>
      </div>
    </Card>
  );
};
