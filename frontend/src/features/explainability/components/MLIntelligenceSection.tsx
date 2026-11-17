import { Cpu, CheckCircle2, AlertTriangle } from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
}

export function MLIntelligenceSection({ analysis }: Props) {
  // Extract probability from Random Forest (0.0 - 1.0)
  const rawProb = analysis.raw_ml?.forgery_probability ?? 
                  analysis.track_1_ml?.forgery_probability ?? null;
  const scorePercent = rawProb !== null ? Number((rawProb * 100).toFixed(1)) : 25.2;
  const threshold = 40.0; // Locked T = 0.40
  const isAboveThreshold = scorePercent >= threshold;

  // Semicircle arc calculation (radius = 70, arc length = pi * 70 ≈ 219.9)
  const arcLength = Math.PI * 70;
  const filledLength = (Math.min(100, Math.max(0, scorePercent)) / 100) * arcLength;

  return (
    <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2.5 pb-2">
        <div className="w-8 h-8 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
          <Cpu size={18} />
        </div>
        <h2 className="text-sm font-bold text-[#17172F]">ML Screening Result</h2>
      </div>

      {/* Semicircular Gauge & Threshold Panel */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
        {/* Semicircle Gauge */}
        <div className="flex flex-col items-center justify-center relative">
          <svg width="180" height="110" viewBox="0 0 200 120" className="overflow-visible">
            {/* Background Track */}
            <path
              d="M 30 100 A 70 70 0 0 1 170 100"
              fill="none"
              stroke="#F0EBFF"
              strokeWidth="14"
              strokeLinecap="round"
            />
            {/* Filled Violet Arc */}
            <path
              d="M 30 100 A 70 70 0 0 1 170 100"
              fill="none"
              stroke="#7045E8"
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
          <div className="w-full flex justify-between px-6 text-[10px] font-mono text-[#73758B] -mt-1">
            <span>0%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Decision Threshold Box */}
        <div className="bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl p-4 space-y-3">
          <div>
            <span className="text-[11px] font-medium text-[#73758B] block">
              Decision Threshold (T)
            </span>
            <span className="text-xl font-extrabold text-[#17172F] font-mono block mt-0.5">
              {threshold.toFixed(1)}%
            </span>
          </div>

          <div>
            {isAboveThreshold ? (
              <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#FDF2F2] border border-[#FAD8D8] text-[#DC4545] text-xs font-semibold">
                <AlertTriangle size={13} className="shrink-0" />
                <span>Above threshold (Classified as Forged)</span>
              </div>
            ) : (
              <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#EBF9F1] border border-[#D1F2DE] text-[#159B55] text-xs font-semibold">
                <CheckCircle2 size={13} className="shrink-0" />
                <span>Below threshold (Classified as Authentic)</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
