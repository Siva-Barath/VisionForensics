import React from 'react';
import { Crosshair } from 'lucide-react';
import Card from '@/components/ui/Card';
import type { DocumentAnalysisResponse } from '@/types';
import type { Region } from '../types';

interface Props {
  analysis: DocumentAnalysisResponse;
  selectedEvidenceId?: string | null;
  hoveredEvidenceId?: string | null;
  onSelectEvidence?: (evidenceId: string | null) => void;
  onHoverEvidence?: (evidenceId: string | null) => void;
  regions?: Region[];
}

export const EvidenceExplorer: React.FC<Props> = ({
  analysis,
  selectedEvidenceId,
  hoveredEvidenceId,
  onSelectEvidence,
  onHoverEvidence,
  regions = [],
}) => {
  const { track_1_ml: t1, track_2_symbolic: t2 } = analysis;
  const topFeatures = Object.entries(t1.top_contributing_features || {});
  const imputedFeatures = Object.entries(t1.imputed_features || {});
  const symbolicEvidence = t2.symbolic_evidence || [];

  return (
    <div className="space-y-6">
      {/* Section 1: Detected Visual Regions on Substrate */}
      <Card title="Detected Visual Forensic Regions">
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-ink-border">
            <span className="text-xs font-mono text-muted uppercase">Detected Overlays:</span>
            <span className={`text-xs font-mono px-2 py-0.5 rounded-sm border ${
              regions.length > 0
                ? 'bg-severity-critical/10 text-severity-critical border-severity-critical/30 font-bold'
                : 'bg-severity-low/10 text-severity-low border-severity-low/30'
            }`}>
              {regions.length} visual region{regions.length === 1 ? '' : 's'} identified
            </span>
          </div>

          {regions.length === 0 ? (
            <div className="p-5 text-center text-xs text-muted font-mono bg-ink-base border border-ink-border rounded-sm">
              No visual tampering regions or localized bounding boxes detected. Substrate appearance is consistent.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-ink-border text-xs font-mono">
                <thead className="bg-ink-base text-muted uppercase">
                  <tr>
                    <th className="px-3 py-2 text-left">Region ID</th>
                    <th className="px-3 py-2 text-left">Category</th>
                    <th className="px-3 py-2 text-left">Finding Description</th>
                    <th className="px-3 py-2 text-center">Page</th>
                    <th className="px-3 py-2 text-right">Severity</th>
                    <th className="px-3 py-2 text-center">Canvas Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-border">
                  {regions.map((reg) => {
                    const isSelected = selectedEvidenceId === reg.id || selectedEvidenceId === reg.evidence_id;
                    const isHovered = hoveredEvidenceId === reg.id || hoveredEvidenceId === reg.evidence_id;

                    return (
                      <tr
                        key={reg.id}
                        onClick={() => onSelectEvidence?.(isSelected ? null : reg.id)}
                        onMouseEnter={() => onHoverEvidence?.(reg.id)}
                        onMouseLeave={() => onHoverEvidence?.(null)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-brand/20 border-l-4 border-l-brand'
                            : isHovered
                            ? 'bg-ink-hover/80'
                            : 'hover:bg-ink-hover/50'
                        }`}
                      >
                        <td className="px-3 py-2 font-bold text-gray-200">{reg.id}</td>
                        <td className="px-3 py-2 text-brand font-bold">{reg.type}</td>
                        <td className="px-3 py-2 text-gray-300 font-sans">{reg.description}</td>
                        <td className="px-3 py-2 text-center">
                          <span className="px-2 py-0.5 bg-ink-base border border-ink-border text-gray-300 rounded-sm text-[10px] font-mono">
                            Page {(reg.page_index ?? 0) + 1}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right font-bold text-severity-critical">
                          {reg.severity.toFixed(1)}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-[10px] font-bold uppercase ${
                            isSelected ? 'bg-brand text-white' : 'bg-ink-base border border-ink-border text-muted'
                          }`}>
                            <Crosshair size={10} /> Focus
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>

      {/* Section 2: Track 2 Symbolic & Semantic Integrity */}
      <Card title="Track 2: Symbolic & Semantic Integrity Findings">
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-ink-border">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono text-muted uppercase">Symbolic Severity Score:</span>
              <span className="text-xs font-mono font-bold text-gray-200">
                {t2.symbolic_severity_score.toFixed(1)} / 100
              </span>
            </div>
            <span className="text-xs font-mono text-muted">
              {symbolicEvidence.length} findings evaluated
            </span>
          </div>

          {symbolicEvidence.length === 0 ? (
            <div className="p-6 text-center text-xs text-muted font-mono bg-ink-base border border-ink-border rounded-sm">
              No symbolic or semantic rule violations detected.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-ink-border text-xs font-mono">
                <thead className="bg-ink-base text-muted uppercase">
                  <tr>
                    <th className="px-4 py-2 text-left">Category</th>
                    <th className="px-4 py-2 text-left">Finding Description</th>
                    <th className="px-4 py-2 text-right">Severity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-border">
                  {symbolicEvidence.map((ev, i) => {
                    const evId = (ev.id as string) || `sym_${i}`;
                    const isSelected = selectedEvidenceId === evId;
                    const isHovered = hoveredEvidenceId === evId;

                    return (
                      <tr
                        key={i}
                        onClick={() => onSelectEvidence?.(isSelected ? null : evId)}
                        onMouseEnter={() => onHoverEvidence?.(evId)}
                        onMouseLeave={() => onHoverEvidence?.(null)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-brand/20 border-l-4 border-l-brand'
                            : isHovered
                            ? 'bg-ink-hover/80'
                            : 'hover:bg-ink-hover/50'
                        }`}
                      >
                        <td className="px-4 py-2 font-bold text-brand">{ev.category || 'RULE'}</td>
                        <td className="px-4 py-2 text-gray-300 font-sans">{ev.description}</td>
                        <td className="px-4 py-2 text-right font-bold text-gray-200">
                          {typeof ev.severity === 'number' ? ev.severity.toFixed(1) : String(ev.severity || 0)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>

      {/* Section 3: Track 1 Physical ML Substrate Indicators */}
      <Card title="Track 1: Physical Substrate Features & ML Indicators">
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-ink-border">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono text-muted uppercase">Feature Extraction:</span>
              <span className="text-xs font-mono font-bold text-brand">
                {(t1.feature_completeness * 100).toFixed(0)}% Complete
              </span>
            </div>
            <span className={`text-xs font-mono px-2 py-0.5 rounded-sm border ${
              t1.status === 'SUCCESS' 
                ? 'bg-severity-low/10 text-severity-low border-severity-low/30' 
                : t1.status === 'DEGRADED' 
                ? 'bg-severity-high/10 text-severity-high border-severity-high/30' 
                : 'bg-severity-critical/10 text-severity-critical border-severity-critical/30'
            }`}>
              Status: {t1.status}
            </span>
          </div>

          <div>
            <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-2">
              Top Contributing Physical Indicators
            </h4>
            {topFeatures.length === 0 ? (
              <p className="text-xs text-muted font-mono bg-ink-base p-3 rounded-sm border border-ink-border">
                No significant substrate feature anomalies detected.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-ink-border text-xs font-mono">
                  <thead className="bg-ink-base text-muted uppercase">
                    <tr>
                      <th className="px-4 py-2 text-left">Substrate Feature Key</th>
                      <th className="px-4 py-2 text-right">Observed Value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-ink-border">
                    {topFeatures.map(([name, val]) => (
                      <tr key={name} className="hover:bg-ink-hover/50">
                        <td className="px-4 py-2 text-gray-200">{name}</td>
                        <td className="px-4 py-2 text-right text-brand font-bold">
                          {typeof val === 'number' ? val.toFixed(2) : String(val)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <p className="text-[10px] text-muted mt-2 italic">
              Note: Top features represent highest statistical deviations from authentic training-set medians. These are decision-support indicators, not SHAP values or proof of causation.
            </p>
          </div>

          {/* Imputed Features Audit */}
          {imputedFeatures.length > 0 && (
            <div className="pt-3 border-t border-ink-border">
              <h4 className="text-xs font-bold text-severity-high uppercase tracking-wider mb-2">
                Imputed Features Audit ({imputedFeatures.length})
              </h4>
              <div className="bg-ink-base border border-ink-border p-3 rounded-sm">
                <p className="text-[10px] text-muted mb-2">
                  The following non-critical features were missing during extraction and replaced strictly with authentic training-set medians:
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-[10px] font-mono">
                  {imputedFeatures.map(([featName, val]) => (
                    <div key={featName} className="text-gray-300">
                      <span className="text-muted">{featName}:</span> {val.toFixed(2)}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
