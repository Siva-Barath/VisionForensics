import { useState } from 'react';
import { 
  Layers, 
  ChevronDown, 
  ChevronUp, 
} from 'lucide-react';
import type { DocumentAnalysisResponse } from '@/types';

interface FeatureDef {
  key: string;
  name: string;
  median: number;
  unit?: string;
  category: 'dimensions' | 'quality' | 'ela' | 'texture' | 'copymove';
  description: string;
  higherMeansAnomaly: boolean;
}

const FEATURE_DEFINITIONS: FeatureDef[] = [
  // 1. Document Dimensions
  {
    key: 'img_width',
    name: 'Substrate Width',
    median: 1080,
    unit: 'px',
    category: 'dimensions',
    description: 'Horizontal pixel dimension of the analyzed document page.',
    higherMeansAnomaly: false,
  },
  {
    key: 'img_height',
    name: 'Substrate Height',
    median: 1920,
    unit: 'px',
    category: 'dimensions',
    description: 'Vertical pixel dimension of the analyzed document page.',
    higherMeansAnomaly: false,
  },
  {
    key: 'img_aspect_ratio',
    name: 'Page Aspect Ratio',
    median: 0.5625,
    category: 'dimensions',
    description: 'Width-to-height ratio verifying standard document geometry.',
    higherMeansAnomaly: false,
  },

  // 2. Image Quality
  {
    key: 'img_laplacian_variance_mean',
    name: 'Laplacian Focus Variance',
    median: 61.15,
    category: 'quality',
    description: 'Measures sharpness and edge focus. Low values indicate blur or artificial smoothing.',
    higherMeansAnomaly: false,
  },
  {
    key: 'img_blur_severity_mean',
    name: 'Blur Severity',
    median: 38.85,
    category: 'quality',
    description: 'Estimated blur level across the document. Deviations may reflect camera focus or scanning artifact.',
    higherMeansAnomaly: true,
  },
  {
    key: 'img_noise_sigma_mean',
    name: 'Substrate Noise Sigma',
    median: 2.97,
    category: 'quality',
    description: 'Sensor noise standard deviation across blank margins. Inconsistent noise indicates spliced content.',
    higherMeansAnomaly: true,
  },
  {
    key: 'img_edge_density_mean',
    name: 'Edge Density',
    median: 0.0177,
    category: 'quality',
    description: 'Proportion of high-gradient edge contours comprising the document text and borders.',
    higherMeansAnomaly: false,
  },

  // 3. Compression and Error Level Analysis
  {
    key: 'img_ela_max_difference_mean',
    name: 'ELA Error Difference',
    median: 14.0,
    category: 'ela',
    description: 'Maximum digital recompression discrepancy across 95% quality resave layers.',
    higherMeansAnomaly: true,
  },
  {
    key: 'img_ela_region_count_mean',
    name: 'ELA Inconsistent Regions',
    median: 1.0,
    category: 'ela',
    description: 'Count of distinct localized blocks exhibiting elevated error levels.',
    higherMeansAnomaly: true,
  },
  {
    key: 'img_illumination_std_mean',
    name: 'Illumination Uniformity',
    median: 50.28,
    category: 'ela',
    description: 'Standard deviation of lighting distribution across the document matrix.',
    higherMeansAnomaly: false,
  },

  // 4. Texture Characteristics
  {
    key: 'img_entropy_score_mean',
    name: 'Shannon Texture Entropy',
    median: 6.36,
    category: 'texture',
    description: 'Information entropy measuring structural complexity and texture consistency.',
    higherMeansAnomaly: false,
  },

  // 5. Copy-Move and Duplicate Detection
  {
    key: 'cm_keypoint_count_akaze',
    name: 'AKAZE Keypoint Density',
    median: 2388.0,
    category: 'copymove',
    description: 'Total invariant spatial keypoints detected for duplicate pattern matching.',
    higherMeansAnomaly: false,
  },
  {
    key: 'cm_descriptor_matches',
    name: 'Descriptor Matches',
    median: 84.0,
    category: 'copymove',
    description: 'Number of pairwise feature descriptors matching across distinct document regions.',
    higherMeansAnomaly: true,
  },
  {
    key: 'cm_inlier_matches',
    name: 'RANSAC Geometric Inliers',
    median: 12.0,
    category: 'copymove',
    description: 'Pairwise matches confirmed by homography transformation to be geometrically consistent.',
    higherMeansAnomaly: true,
  },
  {
    key: 'cm_average_region_size',
    name: 'Cloned Area Size',
    median: 0.0,
    unit: 'px²',
    category: 'copymove',
    description: 'Average spatial area of detected duplicate keypoint clusters.',
    higherMeansAnomaly: true,
  },
  {
    key: 'cm_duplicate_pair_count',
    name: 'Duplicate Pair Count',
    median: 0.0,
    category: 'copymove',
    description: 'Count of validated cloned object pairs (e.g. repeated seals or signatures).',
    higherMeansAnomaly: true,
  },
  {
    key: 'cm_confidence',
    name: 'Clone Spatial Confidence',
    median: 0.0,
    category: 'copymove',
    description: 'Algorithmic confidence in detected copy-move duplication clusters.',
    higherMeansAnomaly: true,
  },
  {
    key: 'cm_inlier_ratio',
    name: 'Inlier Consistency Ratio',
    median: 0.1767,
    category: 'copymove',
    description: 'Ratio of geometrically verified inliers relative to total descriptor candidates.',
    higherMeansAnomaly: false,
  },
];

interface Props {
  analysis: DocumentAnalysisResponse;
}

export function FeatureAnalysisSection({ analysis }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [activeCategory, setActiveCategory] = useState<'all' | 'dimensions' | 'quality' | 'ela' | 'texture' | 'copymove'>('all');

  const vector = analysis.raw_ml?.feature_vector ?? 
                 analysis.track_1_ml?.feature_vector ?? 
                 analysis.track_1_ml?.top_contributing_features ?? {};
  const imputed = analysis.track_1_ml?.imputed_features || {};

  const categories = [
    { id: 'all', label: 'All 18 Features' },
    { id: 'quality', label: 'Image Quality' },
    { id: 'ela', label: 'Compression & ELA' },
    { id: 'copymove', label: 'Copy-Move & Duplication' },
    { id: 'dimensions', label: 'Document Dimensions' },
    { id: 'texture', label: 'Texture Characteristics' },
  ] as const;

  const filteredFeatures = FEATURE_DEFINITIONS.filter((f) => 
    activeCategory === 'all' || f.category === activeCategory
  );

  // Show top 5 features when collapsed, all when expanded
  const displayedFeatures = expanded ? filteredFeatures : filteredFeatures.slice(0, 5);

  const getFeatureStatus = (observed: number | null, median: number, higherMeansAnomaly: boolean) => {
    if (observed === null) return { label: 'Unavailable', color: 'slate' };
    const diff = observed - median;
    const ratio = median !== 0 ? Math.abs(diff / median) : Math.abs(observed);

    if (ratio < 0.25) return { label: 'Within Baseline', color: 'emerald' };
    if (diff > 0 && higherMeansAnomaly) return { label: 'Elevated Variance', color: 'amber' };
    if (diff < 0 && !higherMeansAnomaly) return { label: 'Below Baseline', color: 'blue' };
    return { label: 'Variance Observed', color: 'amber' };
  };

  return (
    <section className="space-y-4" aria-labelledby="features-section-title">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
        <div>
          <div className="flex items-center gap-2">
            <Layers size={18} className="text-brand" />
            <h2 id="features-section-title" className="text-lg font-bold text-white tracking-tight">
              Feature Analysis: Understanding the 18 Substrate Metrics
            </h2>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Physical substrate characteristics evaluated against authentic baseline medians (N=660 reference documents).
          </p>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="px-3.5 py-1.5 bg-ink-panel hover:bg-ink-hover border border-ink-border text-brand rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors self-start sm:self-auto"
        >
          <span>{expanded ? 'Collapse Summary View' : 'View all 18 technical features'}</span>
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      <div className="bg-ink-panel border border-ink-border rounded-xl p-5 space-y-5 shadow-md">
        {/* Category Pills Filter */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
          {categories.map((c) => (
            <button
              key={c.id}
              onClick={() => setActiveCategory(c.id)}
              className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors font-medium ${
                activeCategory === c.id
                  ? 'bg-brand text-white shadow-sm'
                  : 'bg-ink-base border border-ink-border text-gray-400 hover:text-gray-200 hover:bg-ink-hover'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* Features List */}
        <div className="space-y-3">
          {displayedFeatures.map((feat) => {
            const rawVal = vector[feat.key];
            const observedVal = rawVal !== undefined && rawVal !== null ? Number(rawVal) : null;
            const isImputed = feat.key in imputed;
            const status = isImputed 
              ? { label: 'Imputed Median', color: 'amber' }
              : getFeatureStatus(observedVal, feat.median, feat.higherMeansAnomaly);

            // Progress percentage for visualization relative to median
            const pctOfMedian = observedVal !== null && feat.median > 0
              ? Math.min(200, Math.max(10, Math.round((observedVal / feat.median) * 100)))
              : 100;

            return (
              <div
                key={feat.key}
                className="bg-ink-base border border-ink-border rounded-xl p-4 space-y-3 hover:border-brand/30 transition-colors"
              >
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">
                        {feat.name}
                      </span>
                      <span className="text-[10px] font-mono text-gray-500">
                        ({feat.key})
                      </span>
                    </div>
                    <p className="text-xs text-gray-400">
                      {feat.description}
                    </p>
                  </div>

                  {/* Status Badge */}
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border shrink-0 ${
                      status.color === 'emerald'
                        ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800'
                        : status.color === 'amber'
                          ? 'bg-amber-950/80 text-amber-300 border-amber-800'
                          : status.color === 'blue'
                            ? 'bg-blue-950/80 text-blue-300 border-blue-800'
                            : 'bg-slate-900 text-slate-400 border-slate-700'
                    }`}
                  >
                    {status.label}
                  </span>
                </div>

                {/* Values Comparison Row */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 border-t border-ink-border/50 text-xs font-mono">
                  <div>
                    <span className="text-[10px] uppercase text-gray-500 block">Observed Value</span>
                    <span className="font-bold text-white text-sm">
                      {observedVal !== null ? observedVal.toFixed(2) : 'Unavailable'} {feat.unit || ''}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase text-gray-500 block">Authentic Baseline Median</span>
                    <span className="text-gray-300 text-sm">
                      {feat.median.toFixed(2)} {feat.unit || ''}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] uppercase text-gray-500 block">Relative Comparison</span>
                    <div className="w-full bg-ink-panel h-2 rounded-full mt-1.5 overflow-hidden flex border border-ink-border/80">
                      <div
                        className={`h-full ${
                          status.color === 'emerald'
                            ? 'bg-emerald-500'
                            : status.color === 'amber'
                              ? 'bg-amber-500'
                              : 'bg-blue-500'
                        }`}
                        style={{ width: `${Math.min(100, pctOfMedian / 2)}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Expand / Collapse Footer */}
        {!expanded && (
          <div className="pt-2 text-center">
            <button
              onClick={() => setExpanded(true)}
              className="text-xs font-semibold text-brand hover:underline inline-flex items-center gap-1"
            >
              Show all 18 numerical features <ChevronDown size={14} />
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
