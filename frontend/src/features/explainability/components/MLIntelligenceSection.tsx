import { 
  Cpu, 
  Sliders, 
} from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
}

export function MLIntelligenceSection({ analysis }: Props) {
  // Probability from Random Forest (0.0 - 1.0)
  const rawProb = analysis.raw_ml?.forgery_probability ?? 
                  analysis.track_1_ml?.forgery_probability ?? null;
  const scorePercent = rawProb !== null ? Number((rawProb * 100).toFixed(1)) : null;
  const threshold = 40.0; // T = 0.40
  const isAboveThreshold = scorePercent !== null && scorePercent >= threshold;
  const rawClass = analysis.raw_ml?.predicted_class ?? analysis.track_1_ml?.predicted_class ?? (isAboveThreshold ? 'FORGED' : 'AUTHENTIC');
  const executionStatus = analysis.track_1_ml?.status || 'SUCCESS';

  // Position on threshold bar (capped between 2% and 98% for clean UI pin)
  const markerPosition = scorePercent !== null ? Math.min(96, Math.max(4, scorePercent)) : 0;

  return (
    <section className="space-y-5" aria-labelledby="ml-analysis-title">
      <div>
        <div className="flex items-center gap-2">
          <Cpu size={20} className="text-brand" />
          <h2 id="ml-analysis-title" className="text-lg font-bold text-white tracking-tight">
            Machine Learning Analysis
          </h2>
        </div>
        <p className="text-xs text-gray-400 mt-1">
          Supervised classification using the frozen 18-feature Random Forest model at locked threshold T = 0.40.
        </p>
      </div>

      <div className="bg-ink-panel border border-ink-border rounded-xl p-6 space-y-6 shadow-md">
        {/* Top: Model summary cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-ink-base border border-ink-border rounded-lg p-3.5 space-y-1">
            <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider block">
              Active Classifier
            </span>
            <span className="text-sm font-bold text-white block">
              Random Forest
            </span>
            <span className="text-[11px] text-gray-400">
              100 Trees • Supervised Baseline
            </span>
          </div>

          <div className="bg-ink-base border border-ink-border rounded-lg p-3.5 space-y-1">
            <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider block">
              Screening Score
            </span>
            <span className="text-sm font-bold text-white font-mono block">
              {scorePercent !== null ? `${scorePercent}%` : 'Unavailable'}
            </span>
            <span className="text-[11px] text-gray-400">
              Probabilistic Model Output
            </span>
          </div>

          <div className="bg-ink-base border border-ink-border rounded-lg p-3.5 space-y-1">
            <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider block">
              Decision Boundary
            </span>
            <span className="text-sm font-bold text-brand font-mono block">
              T = 0.40 (40.0%)
            </span>
            <span className="text-[11px] text-gray-400">
              Locked Operational Boundary
            </span>
          </div>

          <div className="bg-ink-base border border-ink-border rounded-lg p-3.5 space-y-1">
            <span className="text-[10px] font-mono text-gray-400 uppercase tracking-wider block">
              Raw Classification
            </span>
            <span
              className={`text-sm font-bold font-mono block ${
                isAboveThreshold ? 'text-red-400' : 'text-emerald-400'
              }`}
            >
              {rawClass}
            </span>
            <span className="text-[11px] text-gray-400">
              Execution: {executionStatus}
            </span>
          </div>
        </div>

        {/* Middle: Horizontal Threshold Visualizer */}
        <div className="bg-ink-base border border-ink-border rounded-xl p-5 space-y-4">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                <Sliders size={14} className="text-brand" /> Threshold Position Visualization
              </h3>
              <p className="text-[11px] text-gray-400">
                Visual position of the document's screening score relative to the locked operational decision threshold.
              </p>
            </div>
            {scorePercent !== null && (
              <span
                className={`text-xs font-mono font-bold px-2.5 py-1 rounded border ${
                  isAboveThreshold
                    ? 'bg-red-950/80 text-red-300 border-red-800'
                    : 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
                }`}
              >
                Score: {scorePercent}% • {isAboveThreshold ? 'Above Threshold' : 'Below Threshold'}
              </span>
            )}
          </div>

          {/* The Threshold Bar */}
          <div className="relative pt-7 pb-6">
            {/* Background Track with Zones */}
            <div className="h-4 rounded-full overflow-hidden flex border border-ink-border/80 bg-ink-panel">
              {/* Zone A: Authentic (< 40%) */}
              <div 
                className="h-full bg-gradient-to-r from-emerald-600/40 via-teal-500/40 to-cyan-500/40 relative"
                style={{ width: '40%' }}
              >
                <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono text-emerald-300 font-bold tracking-wider">
                  AUTHENTIC ZONE (0% - 40%)
                </span>
              </div>

              {/* Zone B: Forged (>= 40%) */}
              <div 
                className="h-full bg-gradient-to-r from-amber-500/30 via-red-500/40 to-red-600/50 relative flex-1"
              >
                <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono text-red-300 font-bold tracking-wider">
                  ELEVATED FORGERY ZONE (40% - 100%)
                </span>
              </div>
            </div>

            {/* Threshold Line at 40% */}
            <div 
              className="absolute top-4 bottom-2 w-0.5 bg-brand z-10"
              style={{ left: '40%' }}
            >
              <div className="absolute -top-6 -translate-x-1/2 whitespace-nowrap bg-brand text-white text-[10px] font-mono font-bold px-1.5 py-0.5 rounded shadow">
                T = 40.0%
              </div>
            </div>

            {/* Document Score Pin */}
            {scorePercent !== null && (
              <div
                className="absolute top-2 -translate-x-1/2 z-20 flex flex-col items-center"
                style={{ left: `${markerPosition}%` }}
              >
                <div
                  className={`w-4 h-4 rounded-full border-2 shadow-lg animate-bounce ${
                    isAboveThreshold
                      ? 'bg-red-500 border-white ring-4 ring-red-500/20'
                      : 'bg-emerald-400 border-white ring-4 ring-emerald-500/20'
                  }`}
                />
                <div className="mt-5 text-[10px] font-mono font-bold bg-ink-panel border border-ink-border px-2 py-0.5 rounded text-white shadow">
                  This Document: {scorePercent}%
                </div>
              </div>
            )}
          </div>

          {/* Scale labels */}
          <div className="flex justify-between text-[10px] font-mono text-gray-500 px-1 pt-2 border-t border-ink-border/50">
            <span>0% (Clean Substrate)</span>
            <span>20%</span>
            <span className="text-brand font-bold">40% Threshold</span>
            <span>60%</span>
            <span>80%</span>
            <span>100% (High Anomaly)</span>
          </div>
        </div>

        {/* Bottom: Plain-English interpretation box */}
        <div className="p-4 bg-ink-base rounded-xl border border-ink-border text-xs space-y-2">
          <p className="text-gray-200 leading-relaxed font-sans">
            {scorePercent !== null ? (
              isAboveThreshold ? (
                <>
                  <strong className="text-red-400">Classification Interpretation:</strong> The model's screening score of{' '}
                  <strong>{scorePercent}%</strong> falls above the configured decision threshold of{' '}
                  <strong>40.0%</strong>, yielding a raw classification of <strong className="text-red-400">FORGED</strong>. 
                  Substrate features show abnormal variance compared to training specimens.
                </>
              ) : (
                <>
                  <strong className="text-emerald-400">Classification Interpretation:</strong> The model's screening score of{' '}
                  <strong>{scorePercent}%</strong> falls below the configured decision threshold of{' '}
                  <strong>40.0%</strong>, yielding a raw classification of <strong className="text-emerald-400">AUTHENTIC</strong>. 
                  Extracted physical features align with authentic reference medians.
                </>
              )
            ) : (
              'Raw model classification probability is not available.'
            )}
          </p>

          <p className="text-[11px] text-gray-400 leading-relaxed italic border-t border-ink-border/50 pt-2">
            Evidentiary Note: This is an automated machine learning screening classification based on 18 physical substrate characteristics. It represents probabilistic decision support and should not be construed as definitive legal proof of authenticity.
          </p>
        </div>
      </div>
    </section>
  );
}
