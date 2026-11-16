export type Verdict = "AUTHENTIC" | "LIKELY_AUTHENTIC" | "SUSPICIOUS" | "LIKELY_FORGED" | "FORGED";

export interface DetectorHealth {
  detector_name: string;
  status: "EXECUTED" | "SKIPPED" | "FAILED" | "UNAVAILABLE";
  reason: string | null;
}

export interface EvidenceContribution {
  category: string;
  base_weight: number;
  effective_weight: number;
  risk_shift: number;
}

export interface RiskBreakdown {
  prior_risk: number;
  posterior_risk: number;
  contributors: EvidenceContribution[];
}

export interface Recommendation {
  action: string;
  reason: string;
}

export interface DecisionTraceStep {
  stage: string;
  description: string;
  value_change: string;
  current_posterior: number;
}

export interface DecisionTrace {
  steps: DecisionTraceStep[];
}

export interface FinalForensicAssessment {
  verdict: Verdict;
  calibrated_risk: number;
  breakdown: RiskBreakdown;
  recommendations: Recommendation[];
  decision_trace: DecisionTrace;
  detector_health: DetectorHealth[];
  execution_time_ms?: number;
  overall_confidence?: number;
  sensitivity_profile?: string;
  document_name?: string;
  document_type?: string;
}

export interface Region {
  id: string;
  evidence_id?: string | null;
  type: string; // 'LOGO', 'SIGNATURE', 'OCR', 'COPY_MOVE', etc.
  detector?: string;
  points: [number, number][]; // Polygon/BBox
  confidence: number;
  severity: number;
  description: string;
  page_index?: number;
  associated_recommendations?: string[];
}
