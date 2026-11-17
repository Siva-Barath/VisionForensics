import { 
  CheckCircle2, 
  AlertCircle, 
  FileUp, 
  Lock, 
  Cpu, 
  FileSpreadsheet, 
  ShieldCheck, 
  Scale, 
  Award,
  MinusCircle
} from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
}

export function InvestigationTimeline({ analysis }: Props) {
  const isFailed = analysis.status === 'FAILED';
  const completeness = analysis.track_1_ml?.feature_completeness ?? 1.0;
  const isDegraded = analysis.track_1_ml?.status === 'DEGRADED';

  const stages = [
    {
      id: 1,
      name: 'Document Uploaded',
      desc: `Ingested ${analysis.file_type.toUpperCase()} file (${analysis.original_filename})`,
      status: 'completed',
      icon: FileUp,
    },
    {
      id: 2,
      name: 'Integrity Verified',
      desc: 'Computed & verified SHA-256 fingerprint on disk',
      status: 'completed',
      icon: Lock,
    },
    {
      id: 3,
      name: 'Feature Extraction',
      desc: isDegraded 
        ? `${(completeness * 100).toFixed(0)}% extracted (non-critical medians imputed)`
        : 'All 18 numerical substrate features successfully extracted',
      status: isDegraded ? 'partial' : 'completed',
      icon: FileSpreadsheet,
    },
    {
      id: 4,
      name: 'Random Forest Screening',
      desc: `Classified via frozen model at T=0.40 (${analysis.track_1_ml?.predicted_class || 'COMPLETE'})`,
      status: analysis.track_1_ml?.available ? 'completed' : 'unavailable',
      icon: Cpu,
    },
    {
      id: 5,
      name: 'Symbolic Analysis',
      desc: 'Screened container metadata, ELA layers & keypoint clusters',
      status: analysis.track_2_symbolic?.available ? 'completed' : 'partial',
      icon: ShieldCheck,
    },
    {
      id: 6,
      name: 'Evidence Synthesis',
      desc: 'Corroborated ML probability with deterministic forensic rules',
      status: 'completed',
      icon: Scale,
    },
    {
      id: 7,
      name: 'Final Assessment',
      desc: `Calibrated into ${analysis.unified_risk_tier.replace('_', ' ')} tier`,
      status: isFailed ? 'failed' : 'completed',
      icon: Award,
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 size={16} className="text-emerald-400" />;
      case 'partial':
        return <AlertCircle size={16} className="text-amber-400" />;
      case 'failed':
        return <AlertCircle size={16} className="text-red-400" />;
      default:
        return <MinusCircle size={16} className="text-gray-500" />;
    }
  };

  return (
    <section className="space-y-4" aria-labelledby="timeline-title">
      <div>
        <h2 id="timeline-title" className="text-lg font-bold text-white tracking-tight">
          Investigation Workflow & Verification Timeline
        </h2>
        <p className="text-xs text-gray-400 mt-1">
          Chronological progression through the multi-stage forensic analysis pipeline.
        </p>
      </div>

      <div className="bg-ink-panel border border-ink-border rounded-xl p-5 shadow-md">
        <div className="grid grid-cols-1 md:grid-cols-7 gap-3 relative">
          {stages.map((stage) => {
            const Icon = stage.icon;

            return (
              <div key={stage.id} className="relative flex flex-col justify-between p-3 rounded-lg bg-ink-base border border-ink-border space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-7 h-7 rounded-md bg-ink-panel border border-ink-border flex items-center justify-center text-brand">
                    <Icon size={14} />
                  </div>
                  {getStatusIcon(stage.status)}
                </div>

                <div>
                  <span className="text-[10px] font-mono text-gray-500 block">
                    Step {stage.id}
                  </span>
                  <span className="text-xs font-bold text-white block mt-0.5">
                    {stage.name}
                  </span>
                  <p className="text-[10px] text-gray-400 mt-1 leading-snug">
                    {stage.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
