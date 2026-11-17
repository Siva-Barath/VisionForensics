import { 
  GitBranch, 
  Check, 
} from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
}

export function InvestigationTimeline({ analysis: _analysis }: Props) {
  const steps = [
    { id: 1, name: 'Upload', desc: 'File Ingested' },
    { id: 2, name: 'Integrity Check', sub: '(SHA-256)' },
    { id: 3, name: 'Feature', sub: 'Extraction' },
    { id: 4, name: 'ML Screening', sub: '(Random Forest)' },
    { id: 5, name: 'Symbolic', sub: 'Analysis' },
    { id: 6, name: 'Synthesis', sub: 'Arbiter' },
    { id: 7, name: 'Final', sub: 'Assessment', isFinal: true },
  ];

  return (
    <div className="bg-white border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2.5 pb-2">
        <div className="w-8 h-8 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
          <GitBranch size={18} />
        </div>
        <h2 className="text-sm font-bold text-[#17172F]">Investigation Workflow</h2>
      </div>

      {/* Stepper Bar */}
      <div className="relative pt-2 pb-1 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[620px] relative">
          {/* Continuous Connecting Line */}
          <div className="absolute top-4 left-6 right-6 h-0.5 bg-[#DDD5F9] -translate-y-1/2 z-0" />

          {/* Stepper Nodes */}
          {steps.map((step) => (
            <div key={step.id} className="relative z-10 flex flex-col items-center text-center px-1">
              {/* Checkmark Node Circle */}
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-white shadow-sm transition-all ${
                  step.isFinal
                    ? 'bg-[#7045E8] ring-4 ring-[#F0EBFF]'
                    : 'bg-[#7045E8]'
                }`}
              >
                <Check size={14} strokeWidth={3} />
              </div>

              {/* Step Label */}
              <div
                className={`mt-2 rounded-lg px-2 py-0.5 ${
                  step.isFinal
                    ? 'bg-[#F0EBFF] text-[#7045E8] font-bold'
                    : 'text-[#17172F] font-semibold'
                }`}
              >
                <span className="text-[11px] block leading-tight">{step.name}</span>
                {step.sub && (
                  <span className="text-[10px] text-[#73758B] block leading-tight mt-0.5 font-normal">
                    {step.sub}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
