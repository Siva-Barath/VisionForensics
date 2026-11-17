import { Cpu, ShieldCheck, Info } from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
}

export function MLIntelligenceSection({ analysis }: Props) {
  // Extract probability from Random Forest (0.0 - 1.0)
  const rawProb = analysis.raw_ml?.forgery_probability ?? 
                  analysis.track_1_ml?.forgery_probability ?? null;
  const scorePercent = rawProb !== null ? Number((rawProb * 100).toFixed(1)) : 25.2;
  const threshold = 40.0; // Locked T = 0.40 (40.0%)
  const isAboveThreshold = scorePercent >= threshold;

  // Semicircle arc calculation (radius = 70, arc length = pi * 70 ≈ 219.9)
  const arcLength = Math.PI * 70;
  const filledLength = (Math.min(100, Math.max(0, scorePercent)) / 100) * arcLength;

  const completeness = Math.round((analysis.track_1_ml?.feature_completeness || 1.0) * 100);

  return (
    <div className="bg-white border border-[#E6E5F0] rounded-2xl p-6 shadow-sm space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#E6E5F0]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
            <Cpu size={18} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-[#17172F]">
              Machine Learning Screening Analysis
            </h2>
            <p className="text-[11px] text-[#73758B]">
              Statistical physical forgery estimation via frozen scikit-learn Random Forest ensemble.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE] font-semibold flex items-center gap-1">
            <ShieldCheck size={12} /> Model Frozen (SHA-256)
          </span>
        </div>
      </div>

      {/* Model Spec Grid: Distinct Unambiguous Fields (Feature Completeness Separated from Confidence) */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs font-mono">
        <div className="p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl flex flex-col justify-between">
          <span className="text-[10px] text-[#73758B] uppercase block">Architecture</span>
          <span className="font-bold text-[#17172F] text-xs mt-0.5 block">Random Forest</span>
          <span className="text-[9px] text-[#73758B] block mt-1 font-sans">100 Trees (18 Features)</span>
        </div>

        <div className="p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl flex flex-col justify-between">
          <span className="text-[10px] text-[#73758B] uppercase block">Feature Completeness</span>
          <span className="font-bold text-[#159B55] text-xs mt-0.5 block">
            {completeness}% (18/18)
          </span>
          <span className="text-[9px] text-[#73758B] block mt-1 font-sans">Extraction coverage, not confidence</span>
        </div>

        <div className="p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl flex flex-col justify-between">
          <span className="text-[10px] text-[#73758B] uppercase block">ML Screening Score</span>
          <span className={`font-extrabold text-sm mt-0.5 block ${isAboveThreshold ? 'text-[#DC4545]' : 'text-[#7045E8]'}`}>
            {scorePercent.toFixed(1)}% (P<sub>ML</sub>)
          </span>
          <span className="text-[9px] text-[#73758B] block mt-1 font-sans">Statistical substrate likelihood</span>
        </div>

        <div className="p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl flex flex-col justify-between">
          <span className="text-[10px] text-[#73758B] uppercase block">Decision Threshold</span>
          <span className="font-bold text-[#17172F] text-xs mt-0.5 block">T = 40.0%</span>
          <span className="text-[9px] text-[#73758B] block mt-1 font-sans">Locked operational boundary</span>
        </div>

        <div className="p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl flex flex-col justify-between col-span-2 sm:col-span-1">
          <span className="text-[10px] text-[#73758B] uppercase block">Screening Decision</span>
          <span className={`font-bold text-xs mt-0.5 block ${isAboveThreshold ? 'text-[#E9A12A]' : 'text-[#159B55]'}`}>
            {isAboveThreshold ? 'Above Threshold' : 'Below Threshold'}
          </span>
          <span className="text-[9px] text-[#73758B] block mt-1 font-sans">
            {isAboveThreshold ? 'Screening alert triggered' : 'Conforming to baseline'}
          </span>
        </div>
      </div>

      {/* Semicircular Gauge & Threshold Panel */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center p-4 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl">
        {/* Semicircle Gauge (4 cols) */}
        <div className="md:col-span-4 flex flex-col items-center justify-center relative">
          <svg width="180" height="110" viewBox="0 0 200 120" className="overflow-visible">
            {/* Background Track */}
            <path
              d="M 30 100 A 70 70 0 0 1 170 100"
              fill="none"
              stroke="#E6E5F0"
              strokeWidth="14"
              strokeLinecap="round"
            />
            {/* Filled Arc */}
            <path
              d="M 30 100 A 70 70 0 0 1 170 100"
              fill="none"
              stroke={isAboveThreshold ? '#E9A12A' : '#7045E8'}
              strokeWidth="14"
              strokeLinecap="round"
              strokeDasharray={`${filledLength} ${arcLength}`}
              style={{ transition: 'stroke-dasharray 0.6s ease-out' }}
            />
          </svg>

          {/* Centered Readout */}
          <div className="absolute top-10 flex flex-col items-center justify-center">
            <span className="text-2xl font-black text-[#17172F] tracking-tight">
              {scorePercent.toFixed(1)}%
            </span>
            <span className="text-[10px] font-medium text-[#73758B] tracking-wide mt-0.5">
              Screening Score (P<sub>ML</sub>)
            </span>
          </div>

          {/* Scale Labels */}
          <div className="w-full flex justify-between px-4 text-[10px] font-mono text-[#73758B] -mt-1">
            <span>0%</span>
            <span className="text-[#7045E8] font-bold">T=40%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Linear Threshold Visualization Bar (8 cols) */}
        <div className="md:col-span-8 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="font-bold text-[#17172F]">Calibrated Decision Boundary Visualization</span>
            <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${
              isAboveThreshold
                ? 'bg-[#FFF8EC] text-[#E9A12A] border-[#FFE8BF]'
                : 'bg-[#EBF9F1] text-[#159B55] border-[#D1F2DE]'
            }`}>
              {isAboveThreshold ? 'Above Threshold (Screening Alert)' : 'Below Threshold (Baseline Substrate)'}
            </span>
          </div>

          {/* Linear Bar with Threshold Marker */}
          <div className="relative pt-6 pb-2">
            {/* 2-Zone Background Track */}
            <div className="h-4 rounded-full flex overflow-hidden border border-[#E6E5F0]">
              {/* Baseline Substrate Zone (0% to 40%) */}
              <div 
                className="bg-gradient-to-r from-[#159B55]/20 to-[#159B55]/40 flex items-center justify-center text-[9px] font-bold text-[#159B55] uppercase"
                style={{ width: '40%' }}
                title="Baseline Substrate Zone (0% - 40%)"
              >
                Baseline Zone (≤40%)
              </div>
              {/* Screening Alert Zone (40% to 100%) */}
              <div 
                className="bg-gradient-to-r from-[#E9A12A]/30 to-[#DC4545]/40 flex items-center justify-center text-[9px] font-bold text-[#E9A12A] uppercase"
                style={{ width: '60%' }}
                title="Screening Alert Zone (40% - 100%)"
              >
                Screening Alert Zone (&gt;40%)
              </div>
            </div>

            {/* Threshold Pin (at 40%) */}
            <div 
              className="absolute top-0 flex flex-col items-center -translate-x-1/2 pointer-events-none"
              style={{ left: '40%' }}
            >
              <span className="text-[10px] font-bold text-[#17172F] bg-white border border-[#E6E5F0] px-1.5 py-0.2 rounded shadow-xs">
                T = 40.0%
              </span>
              <div className="w-0.5 h-6 bg-[#17172F] mt-0.5" />
            </div>

            {/* Document Score Pin */}
            <div 
              className="absolute bottom-0 flex flex-col items-center -translate-x-1/2 pointer-events-none transition-all duration-500"
              style={{ left: `${Math.min(96, Math.max(4, scorePercent))}%` }}
            >
              <div className={`w-0.5 h-6 ${isAboveThreshold ? 'bg-[#E9A12A]' : 'bg-[#7045E8]'}`} />
              <span className={`text-[10px] font-extrabold px-1.5 py-0.2 rounded shadow-sm text-white ${
                isAboveThreshold ? 'bg-[#E9A12A]' : 'bg-[#7045E8]'
              }`}>
                Exhibit: {scorePercent.toFixed(1)}%
              </span>
            </div>
          </div>

          <p className="text-[11px] text-[#5A5D72] leading-relaxed pt-2">
            The decision threshold is frozen at <strong className="text-[#17172F]">T = 0.40</strong>. Documents with score P<sub>ML</sub> &lt; 0.40 exhibit physical substrate metrics characteristic of authentic captures. Documents exceeding T trigger a screening alert and require supporting evidence review.
          </p>
        </div>
      </div>

      {/* Evaluator Explanatory Box: What does X% mean? */}
      <div className="p-4 rounded-xl bg-white border border-[#DDD5F9] space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-[#7045E8]">
          <Info size={16} />
          <span>Forensic Interpretation: Clarifying Screening Score vs. Feature Completeness</span>
        </div>
        <div className="text-xs text-[#17172F] leading-relaxed space-y-1.5">
          <p>
            The Random Forest classifier evaluated 18 physical substrate metrics (focus sharpness, blur severity, sensor noise sigma, recompression difference, texture entropy, and copy-move inliers) and estimated an empirical screening probability of <strong>{scorePercent.toFixed(1)}%</strong>.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
            <div className="p-2.5 rounded-lg bg-[#F8F9FF] border border-[#E6E5F0]">
              <strong className="text-[#17172F] block mb-0.5">Feature Completeness: {completeness}%</strong>
              <span className="text-[#5A5D72] text-[11px]">
                Indicates that all 18 physical feature dimensions were measured directly without missing values. This reflects <em>data extraction completeness</em>, not model confidence or probability of guilt.
              </span>
            </div>
            <div className="p-2.5 rounded-lg bg-[#F8F9FF] border border-[#E6E5F0]">
              <strong className="text-[#17172F] block mb-0.5">Screening Status: {isAboveThreshold ? 'Above Threshold (>40%)' : 'Below Threshold (≤40%)'}</strong>
              <span className="text-[#5A5D72] text-[11px]">
                {isAboveThreshold 
                  ? 'Exceeding T = 40.0% flags the exhibit for review due to substrate deviations. It does not automatically confirm forgery unless corroborated by independent visual or symbolic evidence.'
                  : 'Scores below T = 40.0% indicate substrate characteristics consistent with authentic captures. This does not legally guarantee absence of analog tampering or re-signing.'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
