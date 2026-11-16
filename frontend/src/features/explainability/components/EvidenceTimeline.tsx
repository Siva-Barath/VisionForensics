import React from 'react';
import Card from '@/components/ui/Card';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
}

export const EvidenceTimeline: React.FC<Props> = ({ analysis }) => {
  const steps = [
    { name: 'Document Ingestion & Validation', status: 'Completed', color: 'text-severity-low' },
    { 
      name: 'Physical Substrate Feature Extraction', 
      status: analysis.track_1_ml.feature_completeness >= 0.8 ? 'Completed (18 features)' : 'Degraded (imputed)', 
      color: analysis.track_1_ml.feature_completeness >= 0.8 ? 'text-severity-low' : 'text-severity-high' 
    },
    { 
      name: 'Random Forest Inference (T=0.40)', 
      status: analysis.track_1_ml.status === 'SUCCESS' 
        ? `${analysis.track_1_ml.predicted_class} (P=${(analysis.track_1_ml.forgery_probability! * 100).toFixed(1)}%)` 
        : analysis.track_1_ml.status, 
      color: analysis.track_1_ml.predicted_class === 'FORGED' ? 'text-severity-critical' : 'text-severity-low' 
    },
    { 
      name: 'Track 2 Symbolic Rule Inspection', 
      status: `${analysis.track_2_symbolic.symbolic_evidence.length} findings evaluated`, 
      color: 'text-brand' 
    },
    { 
      name: 'Two-Track Risk Synthesis Arbiter', 
      status: analysis.overall_verdict, 
      color: analysis.unified_risk_tier === 'HIGH_RISK' 
        ? 'text-severity-critical' 
        : analysis.unified_risk_tier === 'SUSPICIOUS' 
        ? 'text-severity-high' 
        : 'text-severity-low' 
    },
  ];

  return (
    <Card title="Forensic Pipeline Execution Timeline">
      <div className="p-6">
        <div className="flex flex-col space-y-4">
          {steps.map((step, idx) => (
            <div key={idx} className="flex items-center">
              <div className="w-8 flex flex-col items-center">
                <div className="w-3 h-3 bg-brand rounded-full"></div>
                {idx < steps.length - 1 && <div className="w-0.5 h-full bg-ink-border absolute mt-3"></div>}
              </div>
              <div className="ml-4 flex-1 bg-ink-base border border-ink-border p-2.5 rounded-sm text-xs flex justify-between items-center font-mono">
                <span className="font-medium text-gray-200">{step.name}</span>
                <span className={`font-bold ${step.color}`}>{step.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};
