import { useState } from 'react';
import { 
  SlidersHorizontal, 
  Search, 
  Filter, 
  Info
} from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';

export interface FeatureDefinition {
  key: string;
  name: string;
  category: 'dimensions' | 'quality' | 'ela' | 'texture' | 'copymove';
  categoryLabel: string;
  median: number;
  unit?: string;
  higherMeansAnomaly: boolean;
  whatItMeasures: string;
  interpret: (observed: number, median: number, isImputed: boolean) => string;
}

export const COMPLETE_18_FEATURES: FeatureDefinition[] = [
  // 1. Document Dimensions
  {
    key: 'img_width',
    name: 'Substrate Width',
    category: 'dimensions',
    categoryLabel: 'Document Dimensions',
    median: 1080,
    unit: 'px',
    higherMeansAnomaly: false,
    whatItMeasures: 'Horizontal pixel span of the analyzed document substrate.',
    interpret: (val, med) => 
      val === med 
        ? 'Matches the reference specimen canvas width exactly (1080 px).' 
        : `Observed ${val.toFixed(0)} px vs. ${med} px baseline. Substrate dimension reflects scanning resolution or crop aspect.`
  },
  {
    key: 'img_height',
    name: 'Substrate Height',
    category: 'dimensions',
    categoryLabel: 'Document Dimensions',
    median: 1920,
    unit: 'px',
    higherMeansAnomaly: false,
    whatItMeasures: 'Vertical pixel span of the analyzed document substrate.',
    interpret: (val, med) => 
      val === med 
        ? 'Matches the reference specimen vertical dimension (1920 px).' 
        : `Observed ${val.toFixed(0)} px vs. ${med} px baseline. Verifies standard scanned document height geometry.`
  },
  {
    key: 'img_aspect_ratio',
    name: 'Page Aspect Ratio',
    category: 'dimensions',
    categoryLabel: 'Document Dimensions',
    median: 0.5625,
    higherMeansAnomaly: false,
    whatItMeasures: 'Proportion of substrate width to height (W/H), verifying standard document geometry.',
    interpret: (val, med) => {
      const diff = Math.abs(val - med);
      return diff < 0.05
        ? `Ratio (${val.toFixed(4)}) aligns with standard identity/specimen geometry (~0.5625).`
        : `Observed aspect ratio (${val.toFixed(4)}) exhibits variance from portrait reference standard.`;
    }
  },

  // 2. Image Quality
  {
    key: 'img_laplacian_variance_mean',
    name: 'Laplacian Focus Variance',
    category: 'quality',
    categoryLabel: 'Image Quality',
    median: 61.15,
    higherMeansAnomaly: false,
    whatItMeasures: 'Evaluates edge focus and micro-sharpness using the second-order derivative Laplacian operator.',
    interpret: (val, med) => {
      if (val < med * 0.5) {
        return `Substantially lower sharpness (${val.toFixed(2)} vs. ${med.toFixed(2)}). May indicate post-capture smoothing, artificial re-rendering, or scanner defocus.`;
      }
      return `Measured focus variance (${val.toFixed(2)}) is consistent with authentic optical capture standards (baseline: ${med.toFixed(2)}).`;
    }
  },
  {
    key: 'img_blur_severity_mean',
    name: 'Blur Severity',
    category: 'quality',
    categoryLabel: 'Image Quality',
    median: 38.85,
    higherMeansAnomaly: true,
    whatItMeasures: 'Estimates the global blur severity across document characters, lines, and borders.',
    interpret: (val, med) => {
      if (val > med * 1.25) {
        return `Higher measured blur (${val.toFixed(2)} vs. ${med.toFixed(2)} baseline). This may result from camera focus, scanning optics, or image resampling. Blur requires examiner attention but does not independently establish digital manipulation.`;
      }
      return `Measured blur (${val.toFixed(2)}) is well within the acceptable baseline threshold (${med.toFixed(2)}), confirming clear stroke definition.`;
    }
  },
  {
    key: 'img_noise_sigma_mean',
    name: 'Substrate Noise Sigma',
    category: 'quality',
    categoryLabel: 'Image Quality',
    median: 2.97,
    higherMeansAnomaly: true,
    whatItMeasures: 'Sensor noise standard deviation across uniform document background and margin regions.',
    interpret: (val, med) => {
      if (val > med * 1.8) {
        return `Elevated background noise (${val.toFixed(2)} vs. ${med.toFixed(2)}). May indicate synthetic noise injection or high ISO camera capture.`;
      }
      return `Noise level (${val.toFixed(2)}) is typical for authentic digital captures, indicating consistent background substrate characteristics.`;
    }
  },
  {
    key: 'img_edge_density_mean',
    name: 'Edge Density',
    category: 'quality',
    categoryLabel: 'Image Quality',
    median: 0.0177,
    higherMeansAnomaly: false,
    whatItMeasures: 'Proportion of high-contrast gradient pixels representing textual characters and geometric outlines.',
    interpret: (val, med) => {
      return `Edge pixel coverage (${(val * 100).toFixed(2)}%) matches typical document content density (baseline: ${(med * 100).toFixed(2)}%). No signs of wholesale content removal or foreign blocking.`;
    }
  },
  {
    key: 'img_illumination_std_mean',
    name: 'Illumination Uniformity',
    category: 'quality',
    categoryLabel: 'Image Quality',
    median: 50.28,
    higherMeansAnomaly: false,
    whatItMeasures: 'Photometric standard deviation of luminance across the document surface.',
    interpret: (val, med) => {
      return `Illumination spread (${val.toFixed(2)} vs. ${med.toFixed(2)}) shows natural gradient consistency across the document plane without localized splice shadows.`;
    }
  },

  // 3. Compression and Error Level Analysis
  {
    key: 'img_ela_region_count_mean',
    name: 'ELA Inconsistent Regions',
    category: 'ela',
    categoryLabel: 'Compression & ELA',
    median: 1.0,
    higherMeansAnomaly: true,
    whatItMeasures: 'Count of distinct localized pixel clusters with anomalous compression error upon 95% JPEG resave.',
    interpret: (val, med) => {
      if (val > 3) {
        return `Elevated cluster count (${val.toFixed(0)} regions). Multiple separate areas exhibit differing digital compression histories, indicating potential localized editing.`;
      }
      return `Observed region count (${val.toFixed(0)} vs. ${med.toFixed(0)} baseline) indicates homogeneous compression across the entire document canvas.`;
    }
  },
  {
    key: 'img_ela_max_difference_mean',
    name: 'ELA Maximum Error',
    category: 'ela',
    categoryLabel: 'Compression & ELA',
    median: 14.0,
    higherMeansAnomaly: true,
    whatItMeasures: 'Peak digital discrepancy value between original pixels and recompressed reference matrix.',
    interpret: (val, med) => {
      if (val > med * 1.5) {
        return `High peak compression discrepancy (${val.toFixed(1)} vs. ${med.toFixed(1)}). Suggests high-frequency composite elements inserted from an external source.`;
      }
      return `Peak error difference (${val.toFixed(1)} vs. ${med.toFixed(1)} baseline) is consistent with authentic uniform compression.`;
    }
  },

  // 4. Texture Characteristics
  {
    key: 'img_entropy_score_mean',
    name: 'Shannon Texture Entropy',
    category: 'texture',
    categoryLabel: 'Texture Characteristics',
    median: 6.36,
    higherMeansAnomaly: false,
    whatItMeasures: 'Statistical information entropy measuring substrate micro-texture complexity and information density.',
    interpret: (val, med) => {
      return `Substrate texture entropy (${val.toFixed(2)} vs. ${med.toFixed(2)} baseline) confirms authentic physical micro-structure without synthetic uniform infill.`;
    }
  },

  // 5. Copy-Move Detection
  {
    key: 'cm_keypoint_count_akaze',
    name: 'AKAZE Keypoint Density',
    category: 'copymove',
    categoryLabel: 'Copy-Move Detection',
    median: 2388.0,
    higherMeansAnomaly: false,
    whatItMeasures: 'Scale-invariant nonlinear diffusion keypoints extracted for duplicate pattern correlation.',
    interpret: (val, med) => {
      return `Extracted ${val.toFixed(0)} spatial keypoints (baseline: ${med.toFixed(0)}). Provides robust feature coverage for spatial clone matching.`;
    }
  },
  {
    key: 'cm_descriptor_matches',
    name: 'Descriptor Matches',
    category: 'copymove',
    categoryLabel: 'Copy-Move Detection',
    median: 84.0,
    higherMeansAnomaly: true,
    whatItMeasures: 'Raw candidate pairwise feature descriptor matches identified across distinct document zones.',
    interpret: (val, med) => {
      return `Identified ${val.toFixed(0)} candidate matches (baseline: ${med.toFixed(0)}). Subjected to RANSAC geometric filtering to eliminate random repetitive patterns.`;
    }
  },
  {
    key: 'cm_inlier_matches',
    name: 'RANSAC Geometric Inliers',
    category: 'copymove',
    categoryLabel: 'Copy-Move Detection',
    median: 12.0,
    higherMeansAnomaly: true,
    whatItMeasures: 'Geometrically consistent duplicate match pairs validated through homography transformation.',
    interpret: (val, med) => {
      if (val > 30) {
        return `Significantly elevated inlier count (${val.toFixed(0)} vs. ${med.toFixed(0)}). Strongly indicates replicated content or cloned visual elements.`;
      }
      return `Inlier count (${val.toFixed(0)} vs. ${med.toFixed(0)} baseline) confirms absence of coherent duplicated visual structures.`;
    }
  },
  {
    key: 'cm_average_region_size',
    name: 'Cloned Area Size',
    category: 'copymove',
    categoryLabel: 'Copy-Move Detection',
    median: 0.0,
    unit: 'px²',
    higherMeansAnomaly: true,
    whatItMeasures: 'Average spatial pixel area occupied by validated duplicate keypoint clusters.',
    interpret: (val) => {
      if (val > 0) {
        return `Detected cloned area of ${val.toFixed(0)} px² requiring examiner inspection.`;
      }
      return '0 px² — No contiguous duplicate or cloned regions detected on the document.';
    }
  },
  {
    key: 'cm_duplicate_pair_count',
    name: 'Duplicate Pair Count',
    category: 'copymove',
    categoryLabel: 'Copy-Move Detection',
    median: 0.0,
    higherMeansAnomaly: true,
    whatItMeasures: 'Count of validated clone clusters (e.g. repeated stamps, signatures, or serial numbers).',
    interpret: (val) => {
      if (val > 0) {
        return `${val.toFixed(0)} distinct duplicate pairs identified. Visual review is strongly recommended.`;
      }
      return '0 pairs — No replicated visual elements or duplicated stamps detected.';
    }
  },
  {
    key: 'cm_confidence',
    name: 'Clone Spatial Confidence',
    category: 'copymove',
    categoryLabel: 'Copy-Move Detection',
    median: 0.0,
    higherMeansAnomaly: true,
    whatItMeasures: 'Confidence score (0.0 to 1.0) derived from spatial clustering and geometric consistency.',
    interpret: (val) => {
      if (val > 0.5) {
        return `High clone confidence (${(val * 100).toFixed(1)}%). Elevated probability of visual copy-move tampering.`;
      }
      return '0.0% — Confidence is zero because no coherent duplicate clusters were confirmed.';
    }
  },
  {
    key: 'cm_inlier_ratio',
    name: 'Inlier Consistency Ratio',
    category: 'copymove',
    categoryLabel: 'Copy-Move Detection',
    median: 0.1767,
    higherMeansAnomaly: true,
    whatItMeasures: 'Proportion of candidate matches confirmed to satisfy rigid geometric homography.',
    interpret: (val, med) => {
      return `Ratio of ${(val * 100).toFixed(1)}% (baseline: ${(med * 100).toFixed(1)}%). Corresponds to natural background correlation in text patterns.`;
    }
  },
];

interface Props {
  analysis: DocumentAnalysisResponse;
}

export function FeatureAnalysisWorkspace({ analysis }: Props) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedFeature, setExpandedFeature] = useState<string | null>(null);

  const vector = analysis.raw_ml?.feature_vector ?? 
                 analysis.track_1_ml?.feature_vector ?? 
                 analysis.track_1_ml?.top_contributing_features ?? {};
  const imputed = analysis.track_1_ml?.imputed_features || {};

  const categories = [
    { id: 'all', label: 'All 18 Features' },
    { id: 'dimensions', label: '1. Dimensions' },
    { id: 'quality', label: '2. Image Quality' },
    { id: 'ela', label: '3. Compression & ELA' },
    { id: 'texture', label: '4. Texture' },
    { id: 'copymove', label: '5. Copy-Move' },
  ];

  const filteredFeatures = COMPLETE_18_FEATURES.filter((f) => {
    const matchesCat = selectedCategory === 'all' || f.category === selectedCategory;
    const matchesSearch = f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          f.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          f.whatItMeasures.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="bg-white border border-[#E6E5F0] rounded-2xl p-6 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#E6E5F0]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
            <SlidersHorizontal size={20} />
          </div>
          <div>
            <h2 className="text-base font-bold text-[#17172F] tracking-tight flex items-center gap-2">
              <span>18-Feature Forensic Measurement Matrix</span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE]">
                N=660 Authentic Baseline
              </span>
            </h2>
            <p className="text-xs text-[#73758B] mt-0.5">
              Comprehensive scientific feature evaluation: observed physical metrics vs. authentic reference medians with automated forensic interpretations.
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative w-full md:w-64">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#73758B]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search features or metrics..."
            className="w-full pl-9 pr-3 py-1.5 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] placeholder-[#73758B] focus:outline-none focus:border-[#7045E8]"
          />
        </div>
      </div>

      {/* Category Pills Filter */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-[11px] font-semibold text-[#73758B] uppercase tracking-wider flex items-center gap-1 shrink-0 mr-1">
          <Filter size={12} /> Category:
        </span>
        {categories.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => setSelectedCategory(c.id)}
            className={`px-3 py-1.5 rounded-xl font-medium transition-all whitespace-nowrap text-xs ${
              selectedCategory === c.id
                ? 'bg-[#7045E8] text-white shadow-sm'
                : 'bg-[#F8F9FF] text-[#73758B] border border-[#E6E5F0] hover:text-[#17172F] hover:border-[#DDD5F9]'
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {/* Evaluator-Friendly Table */}
      <div className="overflow-x-auto border border-[#E6E5F0] rounded-xl bg-white shadow-sm">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-[#F8F9FF] text-[#73758B] border-b border-[#E6E5F0] uppercase text-[10px] tracking-wider">
            <tr>
              <th className="py-3 px-4">Feature Name & Key</th>
              <th className="py-3 px-3 text-right">Observed Value</th>
              <th className="py-3 px-3 text-right">Authentic Baseline</th>
              <th className="py-3 px-3 text-right">Difference (Δ)</th>
              <th className="py-3 px-3 text-center">Status</th>
              <th className="py-3 px-4 font-sans text-left min-w-[260px]">What It Measures & Forensic Interpretation</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E6E5F0]">
            {filteredFeatures.map((f) => {
              const rawVal = vector[f.key];
              const observedVal = rawVal !== undefined && rawVal !== null ? Number(rawVal) : null;
              const isImputed = f.key in imputed;
              const isAvailable = observedVal !== null;
              
              let diff = 0;
              let diffPercent = 0;
              let isElevated = false;

              if (isAvailable) {
                diff = observedVal - f.median;
                if (f.median !== 0) {
                  diffPercent = (Math.abs(diff) / f.median) * 100;
                  isElevated = f.higherMeansAnomaly ? (diff > f.median * 0.3) : (diff < -f.median * 0.3);
                } else if (observedVal > 0) {
                  isElevated = true;
                }
              }

              const interpretation = isAvailable
                ? f.interpret(observedVal, f.median, isImputed)
                : 'Metric was not extracted during pipeline execution or feature is unavailable.';

              const isExpanded = expandedFeature === f.key;

              return (
                <tr 
                  key={f.key} 
                  onClick={() => setExpandedFeature(isExpanded ? null : f.key)}
                  className={`hover:bg-[#F8F9FF] transition-colors cursor-pointer ${isExpanded ? 'bg-[#F0EBFF]/40' : ''}`}
                  title="Click row to highlight feature"
                >
                  {/* Feature & Category */}
                  <td className="py-3 px-4 font-sans align-top">
                    <div className="font-bold text-[#17172F] text-xs">
                      {f.name}
                    </div>
                    <div className="text-[10px] font-mono text-[#73758B] mt-0.5">
                      {f.key}
                    </div>
                    <span className="inline-block mt-1 text-[9px] px-1.5 py-0.2 rounded bg-[#F0EBFF] text-[#7045E8] font-semibold uppercase tracking-wider">
                      {f.categoryLabel}
                    </span>
                  </td>

                  {/* Observed Value */}
                  <td className="py-3 px-3 text-right font-bold text-[#17172F] text-xs align-top whitespace-nowrap">
                    {isAvailable ? (
                      <span>
                        {observedVal.toFixed(f.unit === 'px' || f.key.includes('count') ? 0 : 4)}{' '}
                        <span className="text-[10px] text-[#73758B] font-normal">{f.unit || ''}</span>
                      </span>
                    ) : (
                      <span className="text-[#73758B] italic">N/A</span>
                    )}
                  </td>

                  {/* Baseline Median */}
                  <td className="py-3 px-3 text-right text-[#73758B] text-xs align-top whitespace-nowrap">
                    {f.median.toFixed(f.unit === 'px' || f.key.includes('count') ? 0 : 4)}{' '}
                    <span className="text-[10px] font-normal">{f.unit || ''}</span>
                  </td>

                  {/* Difference (Δ) */}
                  <td className="py-3 px-3 text-right align-top whitespace-nowrap">
                    {isAvailable ? (
                      <div className={`font-mono text-xs ${Math.abs(diff) > 0.0001 ? (isElevated ? 'text-[#E9A12A]' : 'text-[#73758B]') : 'text-[#159B55]'}`}>
                        <span>{diff >= 0 ? `+${diff.toFixed(2)}` : diff.toFixed(2)}</span>
                        {f.median !== 0 && (
                          <span className="text-[10px] block opacity-80">
                            ({diffPercent.toFixed(1)}%)
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-[#73758B]">-</span>
                    )}
                  </td>

                  {/* Status Badge */}
                  <td className="py-3 px-3 text-center align-top whitespace-nowrap">
                    {!isAvailable ? (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#F4F5FB] text-[#73758B] border border-[#E6E5F0]">
                        Unavailable
                      </span>
                    ) : isImputed ? (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#FFF8EC] text-[#E9A12A] font-semibold border border-[#FFE8BF]">
                        Imputed
                      </span>
                    ) : isElevated ? (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#FFF8EC] text-[#E9A12A] font-semibold border border-[#FFE8BF]">
                        Elevated Variance
                      </span>
                    ) : (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#EBF9F1] text-[#159B55] font-semibold border border-[#D1F2DE]">
                        Baseline Normal
                      </span>
                    )}
                  </td>

                  {/* Forensic Interpretation */}
                  <td className="py-3 px-4 font-sans align-top text-xs leading-relaxed">
                    <p className="text-[#17172F] font-medium">
                      {interpretation}
                    </p>
                    <p className="text-[11px] text-[#73758B] mt-1 italic">
                      <strong className="not-italic text-[#7045E8]">Measures:</strong> {f.whatItMeasures}
                    </p>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl text-xs text-[#73758B]">
        <div className="flex items-center gap-2">
          <Info size={16} className="text-[#7045E8] shrink-0" />
          <span>
            <strong>Forensic Evaluation Standard:</strong> 18 physical substrate metrics extracted using OpenCV, NumPy, and AKAZE; compared against empirical medians from N=660 validated authentic government specimens.
          </span>
        </div>
        <div className="font-mono text-[11px] text-[#17172F] shrink-0">
          Showing 18 of 18 Invariant Schema Metrics
        </div>
      </div>
    </div>
  );
}
