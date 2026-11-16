import { Cpu, ScanLine, Copy, Type, FileSearch, Fingerprint, Image, Lock, Gauge } from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';
import { rawModelSummary } from '@/utils/analysisPresentation';

const modules = [
  { key: 'ela', name: 'Error level analysis', icon: ScanLine, detail: 'ela' },
  { key: 'random_forest', name: 'Frozen Random Forest', icon: Cpu, detail: 'ml_features' },
  { key: 'image_quality', name: 'Image quality', icon: Gauge, detail: 'ml_features' },
  { key: 'copy_move', name: 'Duplicate regions', icon: Copy, detail: 'copymove' },
  { key: 'ocr', name: 'Text extraction', icon: Type, detail: 'decision_trace' },
  { key: 'metadata', name: 'Embedded metadata', icon: FileSearch, detail: 'metadata' },
  { key: 'signature_visual', name: 'Signature region appearance', icon: Fingerprint, detail: 'decision_trace' },
  { key: 'jpeg_compression', name: 'JPEG compression', icon: Image, detail: 'ela' },
  { key: 'file_integrity', name: 'Exhibit integrity', icon: Lock, detail: 'custody' },
] as const;

export default function ForensicModules({ analysis, onDetails }: {
  analysis: DocumentAnalysisResponse;
  onDetails: (tab: typeof modules[number]['detail']) => void;
}) {
  const vector = analysis.raw_ml?.feature_vector ?? analysis.track_1_ml?.feature_vector;
  const value = (key: string) => vector?.[key] == null ? 'Unavailable' : Number(vector[key]).toFixed(2);
  const findings: Record<string, string> = {
    ela: `Maximum recompression difference: ${value('img_ela_max_difference_mean')}. ELA is a screening signal, not proof of editing.`,
    random_forest: rawModelSummary(analysis),
    image_quality: `Focus variance: ${value('img_laplacian_variance_mean')}. Blur severity: ${value('img_blur_severity_mean')}. Capture quality can affect analysis.`,
    copy_move: analysis.track_3_visual?.available ? `${analysis.track_3_visual.detected_clusters} geometric cluster(s). Repeated patterns require examiner review.` : 'No retained visual summary is available.',
    ocr: 'Extracted text, when available, does not verify the truth of a document’s contents.',
    metadata: analysis.metadata_info ? 'Stored embedded properties are available in the metadata details.' : 'No embedded property results were retained.',
    signature_visual: 'Region appearance is examined without a validated reference signature.',
    jpeg_compression: analysis.compression_qualification?.is_jpeg ? `Estimated JPEG quality: ${analysis.compression_qualification.estimated_quality ?? 'Unavailable'}. Recompression can affect ELA.` : 'JPEG quantization analysis applies only to JPEG source files.',
    file_integrity: 'Review the ingestion and retrieval events in the exhibit custody record.',
  };
  return <section className="space-y-4" aria-labelledby="modules-title">
    <div><h2 id="modules-title" className="text-lg font-semibold text-white">Forensic examination</h2><p className="text-sm text-muted mt-1">Recorded execution for this exhibit. A completed check does not establish authenticity.</p></div>
    <div className="rounded-xl border border-brand/25 bg-brand/5 p-5 space-y-2">
      <h3 className="text-sm font-semibold text-brand">Unmodified raw model result</h3>
      <p className="text-sm text-gray-200 leading-relaxed">{rawModelSummary(analysis)}</p>
      <p className="text-xs text-muted">The document assessment above includes the existing JPEG and multi-page heuristics. It is separate from the raw model result.</p>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {modules.map(({ key, name, icon: Icon, detail }) => {
        const outcome = analysis.module_statuses?.[key];
        const status = outcome?.status ?? 'UNAVAILABLE';
        return <article key={key} className="rounded-xl border border-ink-border bg-ink-panel p-5 flex flex-col gap-4">
          <div className="flex items-start justify-between gap-3"><Icon size={20} className="text-brand" /><span className={`text-[10px] rounded-full px-2 py-1 font-medium ${status === 'COMPLETED' ? 'text-emerald-300 bg-emerald-400/10' : status === 'FAILED' ? 'text-red-300 bg-red-400/10' : 'text-amber-200 bg-amber-400/10'}`}>{status}</span></div>
          <h3 className="text-sm font-semibold text-white">{name}</h3>
          <p className="text-xs text-gray-200 leading-relaxed">{findings[key]}</p>
          <p className="text-xs text-muted leading-relaxed flex-1">{outcome?.reason ?? 'Execution details were not retained for this analysis.'}</p>
          <button onClick={() => onDetails(detail)} className="text-xs font-medium text-brand text-left hover:underline">Inspect evidence →</button>
        </article>;
      })}
    </div>
    <p className="text-xs text-muted">Signature authenticity verification: {analysis.module_statuses?.signature_authenticity?.status ?? 'NOT IMPLEMENTED'}. Visual region checks do not verify a signer’s identity.</p>
  </section>;
}
