import type { DocumentAnalysisResponse } from '@/types';

export function rawModelSummary(analysis: Pick<DocumentAnalysisResponse, 'raw_ml'>): string {
  const raw = analysis.raw_ml;
  const value = raw?.forgery_probability;
  if (!raw?.available || value == null || !Number.isFinite(value) || value < 0 || value > 1) {
    return 'Unmodified raw model result unavailable. No probability has been inferred from the document assessment.';
  }
  const source = raw.source_page_index == null ? 'Aggregate feature fallback' : `Page ${raw.source_page_index + 1}`;
  const method = raw.selection_method === 'maximum_page_probability' ? ' Highest scoring page; heuristic selection, not a document-wide probability.' : '';
  return `${source}: ${(value * 100).toFixed(1)}% screening score at T=0.40. Raw class: ${raw.predicted_class ?? 'unavailable'}.${method}`;
}
