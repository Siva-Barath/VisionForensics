import React from 'react';
import Card from '@/components/ui/Card';
import type { DocumentAnalysisResponse } from '@/types';

interface Props {
  analysis: DocumentAnalysisResponse;
}

export const DetectorSummary: React.FC<Props> = ({ analysis }) => {
  const { track_1_ml: t1, track_2_symbolic: t2, track_3_visual: t3, compression_qualification: cq, warnings } = analysis;

  const ocrWarning = warnings.find(w => w.toLowerCase().includes('ocr'));
  const hasImputed = Object.keys(t1.imputed_features || {}).length > 0;

  const stages = [
    {
      subsystem: 'Track 1: ML Statistical Classifier',
      module: 'Random Forest Baseline (18 Features, T=0.40)',
      status: t1.status, // SUCCESS | DEGRADED | ML_UNAVAILABLE
      details: t1.status === 'SUCCESS' 
        ? 'All 18 authoritative numerical features extracted directly' 
        : t1.status === 'DEGRADED' 
        ? `${Object.keys(t1.imputed_features).length} non-critical feature(s) imputed with authentic medians`
        : 'Critical substrate features unavailable; inference aborted',
      badgeClass: t1.status === 'SUCCESS'
        ? 'bg-severity-low/10 text-severity-low border-severity-low/30'
        : t1.status === 'DEGRADED'
        ? 'bg-severity-high/10 text-severity-high border-severity-high/30'
        : 'bg-severity-critical/10 text-severity-critical border-severity-critical/30'
    },
    {
      subsystem: 'Physical Substrate Feature Extraction',
      module: 'ELA, Laplacian Blur, Noise Sigma, AKAZE Matches',
      status: t1.feature_completeness >= 0.8 ? 'EXECUTED' : 'PARTIAL',
      details: `${(t1.feature_completeness * 100).toFixed(0)}% completeness (${hasImputed ? 'with medians' : 'direct'})`,
      badgeClass: t1.feature_completeness >= 0.8
        ? 'bg-severity-low/10 text-severity-low border-severity-low/30'
        : 'bg-severity-high/10 text-severity-high border-severity-high/30'
    },
    {
      subsystem: 'Track 2: Symbolic & Semantic Integrity',
      module: 'Metadata, Typographic & Layout Rules',
      status: t2.available ? 'EXECUTED' : 'UNAVAILABLE',
      details: `${t2.symbolic_evidence.length} evidence finding(s) evaluated (Severity: ${t2.symbolic_severity_score.toFixed(1)})`,
      badgeClass: t2.available
        ? 'bg-severity-low/10 text-severity-low border-severity-low/30'
        : 'bg-severity-critical/10 text-severity-critical border-severity-critical/30'
    },
    {
      subsystem: 'Track 3: Visual Evidence Arbiter (REM-03)',
      module: 'ORB Keypoints & Spatial Clone Clustering',
      status: t3?.available ? 'EXECUTED' : 'STANDBY',
      details: t3?.available 
        ? `${t3.detected_clusters} clone cluster(s), ${t3.total_inlier_matches} inlier pair(s) (Visual Tier: ${t3.visual_tier})`
        : 'No prominent clone duplications flagged by visual arbiter',
      badgeClass: t3?.copy_move_confirmed
        ? 'bg-severity-critical/10 text-severity-critical border-severity-critical/30'
        : 'bg-severity-low/10 text-severity-low border-severity-low/30'
    },
    {
      subsystem: 'Track 4: JPEG Compression Qualification (REM-04)',
      module: 'Quantization Table & Quality Factor Estimation',
      status: cq?.is_jpeg ? 'EVALUATED' : 'N/A (NON-JPEG)',
      details: cq?.is_jpeg 
        ? `Estimated Quality: ${cq.estimated_quality?.toFixed(1) || 'N/A'}${cq.is_heavily_compressed ? ' (Heavily compressed warning)' : ''}`
        : 'Exhibit substrate is lossless or rasterized container',
      badgeClass: cq?.is_heavily_compressed
        ? 'bg-severity-high/10 text-severity-high border-severity-high/30'
        : 'bg-severity-low/10 text-severity-low border-severity-low/30'
    },
    {
      subsystem: 'OCR & Typographic Extraction',
      module: 'PaddleOCR / Fallback OCR Engine',
      status: ocrWarning ? 'WARNING' : 'EXECUTED',
      details: ocrWarning || 'OCR text extraction completed with zero fatal warnings',
      badgeClass: ocrWarning
        ? 'bg-severity-high/10 text-severity-high border-severity-high/30'
        : 'bg-severity-low/10 text-severity-low border-severity-low/30'
    },
    {
      subsystem: 'Multi-Track Forensic Synthesis Engine',
      module: 'Statistical, Symbolic & Visual Evidence Fusion',
      status: 'COMPLETED',
      details: `Synthesized Verdict: ${analysis.overall_verdict} (Risk Tier: ${analysis.unified_risk_tier})`,
      badgeClass: 'bg-brand/10 text-brand border-brand/30'
    }
  ];

  return (
    <Card title="Multi-Track Forensic Pipeline Subsystem Health & Status">
      <div className="p-6 overflow-x-auto">
        <table className="min-w-full divide-y divide-ink-border text-xs font-mono">
          <thead className="bg-ink-base text-muted uppercase">
            <tr>
              <th className="px-4 py-2.5 text-left">Subsystem</th>
              <th className="px-4 py-2.5 text-left">Module Specification</th>
              <th className="px-4 py-2.5 text-left">Status</th>
              <th className="px-4 py-2.5 text-left">Execution Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink-border">
            {stages.map((s, idx) => (
              <tr key={idx} className="hover:bg-ink-hover/50">
                <td className="px-4 py-3 font-bold text-gray-200">{s.subsystem}</td>
                <td className="px-4 py-3 text-muted">{s.module}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-sm border font-bold uppercase text-[10px] ${s.badgeClass}`}>
                    {s.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-300 font-sans">{s.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
