import { FinalForensicAssessment, Region } from '../types';

export const mockAssessment: FinalForensicAssessment = {
  document_name: "passport_scan_001.pdf",
  document_type: "PASSPORT",
  verdict: "LIKELY_FORGED",
  calibrated_risk: 0.82,
  execution_time_ms: 2800,
  overall_confidence: 0.96,
  sensitivity_profile: "BALANCED",
  breakdown: {
    prior_risk: 0.05,
    posterior_risk: 0.82,
    contributors: [
      { category: "COPY_MOVE", base_weight: 0.30, effective_weight: 0.28, risk_shift: 0.28 },
      { category: "SIGNATURE", base_weight: 0.22, effective_weight: 0.21, risk_shift: 0.21 },
      { category: "LOGO", base_weight: 0.15, effective_weight: 0.16, risk_shift: 0.16 },
      { category: "OCR", base_weight: 0.12, effective_weight: 0.11, risk_shift: 0.11 },
      { category: "CONFLICT", base_weight: 1.0, effective_weight: 1.0, risk_shift: -0.04 }
    ]
  },
  recommendations: [
    { action: "Manual signature verification recommended", reason: "Signature exhibits unnatural mathematical properties." },
    { action: "Review duplicated region", reason: "Copy-Move algorithms found strong evidence of duplicated image patches." },
    { action: "Poor scan quality reduces OCR reliability", reason: "Global blur detected across document." }
  ],
  decision_trace: {
    steps: [
      { stage: "Initialization", description: "Setting base prior risk", value_change: "0%", current_posterior: 0.05 },
      { stage: "COPY_MOVE", description: "Applied normalized evidence 0.95 with weight 0.28", value_change: "+28%", current_posterior: 0.33 },
      { stage: "SIGNATURE", description: "Applied normalized evidence 0.85 with weight 0.21", value_change: "+21%", current_posterior: 0.54 },
      { stage: "LOGO", description: "Applied normalized evidence 0.70 with weight 0.16", value_change: "+16%", current_posterior: 0.70 },
      { stage: "OCR", description: "Applied normalized evidence 0.60 with weight 0.11", value_change: "+11%", current_posterior: 0.81 },
      { stage: "Confidence Calibration", description: "Applied global confidence multiplier 0.95", value_change: "-4%", current_posterior: 0.82 }
    ]
  },
  detector_health: [
    { detector_name: "Logo Verification", status: "EXECUTED", reason: null },
    { detector_name: "Signature Verification", status: "EXECUTED", reason: null },
    { detector_name: "OCR Extraction", status: "EXECUTED", reason: null },
    { detector_name: "Copy-Move Detection", status: "EXECUTED", reason: null },
    { detector_name: "Passport Rules", status: "SKIPPED", reason: "Not Applicable" }
  ]
};

export const mockRegions: Region[] = [
  {
    id: "r1", type: "SIGNATURE", points: [[100, 100], [300, 100], [300, 200], [100, 200]],
    confidence: 0.85, severity: 80, description: "Unnatural uniform stroke width",
    associated_recommendations: ["Manual signature verification recommended"]
  },
  {
    id: "r2", type: "COPY_MOVE", points: [[400, 400], [500, 400], [500, 500], [400, 500]],
    confidence: 0.9, severity: 95, description: "Duplicated block detected",
    associated_recommendations: ["Review duplicated region"]
  },
  {
    id: "r3", type: "LOGO", points: [[50, 50], [90, 50], [90, 90], [50, 90]],
    confidence: 1.0, severity: 10, description: "Authentic logo structure",
    associated_recommendations: []
  }
];
