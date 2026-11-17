import { 
  GitMerge, 
  Cpu, 
  ShieldCheck, 
  Scale, 
} from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
}

export function TwoTrackArbiterSection({ analysis }: Props) {
  const t1 = analysis.track_1_ml;
  const t2 = analysis.track_2_symbolic;
  const t3 = analysis.track_3_visual;
  const trace = analysis.decision_trace || [];

  return (
    <section className="space-y-5" aria-labelledby="arbiter-title">
      <div>
        <div className="flex items-center gap-2">
          <GitMerge size={20} className="text-brand" />
          <h2 id="arbiter-title" className="text-lg font-bold text-white tracking-tight">
            Two-Track Analytical Architecture & Synthesis Arbiter
          </h2>
        </div>
        <p className="text-xs text-gray-400 mt-1">
          VisionForensics AI separates statistical physical machine learning from symbolic forensic rules before synthesizing a unified verdict.
        </p>
      </div>

      <div className="bg-ink-panel border border-ink-border rounded-xl p-6 space-y-6 shadow-md">
        {/* The Two Analytical Tracks */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative">
          {/* TRACK 1: Machine Learning */}
          <div className="bg-ink-base border border-ink-border rounded-xl p-5 space-y-3 relative overflow-hidden">
            <div className="flex items-center justify-between pb-2 border-b border-ink-border/60">
              <span className="text-xs font-bold text-brand flex items-center gap-1.5 uppercase tracking-wider">
                <Cpu size={16} /> Track 1: Statistical Machine Learning
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800">
                {t1?.status || 'EXECUTED'}
              </span>
            </div>

            <p className="text-xs text-gray-300 leading-relaxed">
              Evaluates 18 numerical physical substrate measurements (sharpness, blur variance, noise sigma, ELA discrepancies) against training medians using a frozen Random Forest classifier.
            </p>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-ink-border/40">
              <div>
                <span className="text-[10px] text-gray-500 uppercase block">Screening Score</span>
                <span className="font-bold text-white">
                  {t1?.forgery_probability !== null && t1?.forgery_probability !== undefined 
                    ? `${(t1.forgery_probability * 100).toFixed(1)}%` 
                    : 'N/A'}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-gray-500 uppercase block">Model Prediction</span>
                <span className={`font-bold ${t1?.predicted_class === 'FORGED' ? 'text-red-400' : 'text-emerald-400'}`}>
                  {t1?.predicted_class || 'UNKNOWN'}
                </span>
              </div>
            </div>
          </div>

          {/* TRACK 2: Symbolic Forensic Rules */}
          <div className="bg-ink-base border border-ink-border rounded-xl p-5 space-y-3 relative overflow-hidden">
            <div className="flex items-center justify-between pb-2 border-b border-ink-border/60">
              <span className="text-xs font-bold text-cyan-400 flex items-center gap-1.5 uppercase tracking-wider">
                <ShieldCheck size={16} /> Track 2: Symbolic Forensic Rules
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-400 border border-cyan-800">
                {t2?.available ? 'EXECUTED' : 'STANDBY'}
              </span>
            </div>

            <p className="text-xs text-gray-300 leading-relaxed">
              Examines deterministic forensic rules: file container metadata, PDF software signatures, visual copy-move keypoint clusters, and JPEG quantization tables.
            </p>

            <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-2 border-t border-ink-border/40">
              <div>
                <span className="text-[10px] text-gray-500 uppercase block">Rule Severity Score</span>
                <span className="font-bold text-white">
                  {t2?.symbolic_severity_score !== undefined ? `${t2.symbolic_severity_score.toFixed(1)} / 100` : '0.0'}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-gray-500 uppercase block">Visual Clusters</span>
                <span className="font-bold text-white">
                  {t3?.detected_clusters ?? 0} Flagged
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Synthesis Arbiter Card */}
        <div className="bg-gradient-to-r from-ink-base via-[#101b2b] to-ink-base border border-ink-border rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-ink-border">
            <div className="flex items-center gap-2">
              <Scale size={18} className="text-brand" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Synthesis Arbiter Logic
              </h3>
            </div>
            <span className="text-xs font-mono font-bold text-white px-2.5 py-0.5 rounded bg-ink-panel border border-ink-border">
              Final Verdict: {analysis.unified_risk_tier}
            </span>
          </div>

          <p className="text-xs text-gray-300 leading-relaxed">
            The Synthesis Arbiter corroborates Track 1 statistical screening with Track 2 rule findings. If both tracks confirm authentic characteristics, the document is cleared as <strong>LOW_RISK</strong>. If localized visual tampering (e.g. cloned seals) is corroborated, the tier is elevated to <strong>HIGH_RISK</strong> regardless of global substrate average.
          </p>

          {/* Decision Trace Steps */}
          {trace.length > 0 && (
            <div className="space-y-2 pt-2">
              <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">
                Corroborated Decision Trace ({trace.length} Steps)
              </span>
              <div className="space-y-1.5 font-mono text-xs">
                {trace.map((step, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 bg-ink-panel rounded-lg border border-ink-border/80 flex items-start gap-2.5"
                  >
                    <span className="text-brand font-bold shrink-0">
                      [{step.track || `Step ${idx + 1}`}]:
                    </span>
                    <span className="text-gray-200">
                      {step.finding} {step.description ? `— ${step.description}` : ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
