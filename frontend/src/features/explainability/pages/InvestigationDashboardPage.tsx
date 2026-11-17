import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  AlertTriangle, 
  RefreshCw, 
  ArrowLeft, 
  Eye
} from 'lucide-react';
import Card from '@/components/ui/Card';
import { DocumentIdentityHeader } from '../components/DocumentIdentityHeader';
import { InvestigationSummaryCard } from '../components/InvestigationSummaryCard';
import { InvestigationTimeline } from '../components/InvestigationTimeline';
import { WhyWeReachedAssessment } from '../components/WhyWeReachedAssessment';
import { MLIntelligenceSection } from '../components/MLIntelligenceSection';
import { FeatureAnalysisSection } from '../components/FeatureAnalysisSection';
import { TwoTrackArbiterSection } from '../components/TwoTrackArbiterSection';
import { AdvancedForensicEvidence } from '../components/AdvancedForensicEvidence';
import { DocumentViewer } from '../components/DocumentViewer';
import { RegionInspector } from '../components/RegionInspector';
import { GenerateReportModal } from '../components/GenerateReportModal';
import { Region } from '../types';
import { getDocumentAnalysis, getDocumentImageUrl, getDocumentCustodyLogs } from '@/services/api';
import { extractApiError } from '@/utils/helpers';
import type { DocumentAnalysisResponse } from '@/types';

export default function InvestigationDashboardPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState<DocumentAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [is404, setIs404] = useState(false);

  // Synchronized evidence and region selection state
  const [selectedRegionId, setSelectedRegionId] = useState<string | null>(null);
  const [hoveredRegionId, setHoveredRegionId] = useState<string | null>(null);

  // Multi-page document navigation state
  const [currentPage, setCurrentPage] = useState<number>(0);

  // Forensic Report Modal State
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  // Evidence Custody Logs
  const [custodyLogs, setCustodyLogs] = useState<Array<any>>([]);
  const [custodyLoading, setCustodyLoading] = useState(false);

  // Active advanced detail tab
  const [advancedTab, setAdvancedTab] = useState<string>('features');

  // Smooth scroll refs
  const mlSectionRef = useRef<HTMLDivElement>(null);
  const visualSectionRef = useRef<HTMLDivElement>(null);
  const advancedSectionRef = useRef<HTMLDivElement>(null);

  const fetchAnalysis = () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    setIs404(false);
    setAnalysis(null);

    getDocumentAnalysis(id)
      .then((data) => {
        setAnalysis(data);
        setLoading(false);
      })
      .catch((err: unknown) => {
        setLoading(false);
        const errMsg = extractApiError(err);
        if (errMsg.toLowerCase().includes('not found') || errMsg.toLowerCase().includes('expired')) {
          setIs404(true);
          setError(`Forensic analysis for document ID '${id}' was not found or has expired.`);
        } else {
          setError(errMsg);
        }
      });
  };

  useEffect(() => {
    fetchAnalysis();
  }, [id]);

  useEffect(() => {
    if (id) {
      setCustodyLoading(true);
      getDocumentCustodyLogs(id)
        .then((logs) => setCustodyLogs(logs || []))
        .catch(() => setCustodyLogs([]))
        .finally(() => setCustodyLoading(false));
    }
  }, [id]);

  const scrollToML = () => {
    mlSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const scrollToVisual = () => {
    visualSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const scrollToAdvancedTab = (tab: string) => {
    setAdvancedTab(tab);
    advancedSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // Loading State
  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-24 text-center space-y-4">
        <div className="w-12 h-12 border-3 border-brand border-t-transparent rounded-full animate-spin mx-auto" />
        <h2 className="text-lg font-bold text-white tracking-tight">Retrieving Forensic Investigation Findings</h2>
        <p className="text-xs text-gray-400 font-mono">
          Loading calibrated analytical outputs for Exhibit: {id}
        </p>
      </div>
    );
  }

  // Error State
  if (error || !analysis) {
    return (
      <div className="max-w-xl mx-auto py-16 space-y-4">
        <Card variant="evidence" className="p-8 text-center space-y-4">
          <div className="w-14 h-14 rounded-full bg-red-950/40 border border-red-800 flex items-center justify-center mx-auto text-red-400">
            <AlertTriangle size={28} />
          </div>
          <h2 className="text-lg font-bold text-white tracking-tight">
            {is404 ? 'Investigation Not Found' : 'Unable to Retrieve Findings'}
          </h2>
          <p className="text-xs text-gray-300 font-mono bg-ink-base border border-ink-border p-3 rounded-lg leading-relaxed text-left">
            {error || 'An unexpected error occurred while communicating with the server.'}
          </p>

          <div className="flex justify-center gap-3 pt-3">
            <button
              onClick={() => navigate('/cases')}
              className="px-4 py-2 bg-ink-panel border border-ink-border hover:bg-ink-hover text-gray-300 rounded-lg text-xs font-semibold flex items-center gap-1.5"
            >
              <ArrowLeft size={14} /> Back to Cases
            </button>
            <button
              onClick={fetchAnalysis}
              className="px-4 py-2 bg-brand hover:bg-brand-hover text-white rounded-lg text-xs font-semibold flex items-center gap-1.5"
            >
              <RefreshCw size={14} /> Retry
            </button>
          </div>
        </Card>
      </div>
    );
  }

  // Genuine Forensic Regions
  const regions: Region[] = (analysis.detected_regions || []).map((r) => ({
    id: r.id,
    evidence_id: r.evidence_id,
    type: r.category,
    detector: r.detector,
    points: r.bounding_box.points,
    confidence: r.confidence ?? 1.0,
    severity: r.severity,
    description: r.description,
    page_index: r.page_index ?? 0,
  }));

  const selectedRegion = regions.find((r) => r.id === selectedRegionId) || null;

  // Reliable image preview URL strictly from backend
  const isPdf = analysis.file_type.toLowerCase() === 'pdf' || analysis.original_filename.toLowerCase().endsWith('.pdf');
  const pageCount = analysis.image_dimensions?.page_count || 1;
  const imageUrl = getDocumentImageUrl(analysis.document_id, currentPage);

  const handleRegionSelected = (region: Region | null) => {
    if (region) {
      setSelectedRegionId(region.id);
      if (region.page_index !== undefined && region.page_index !== currentPage) {
        setCurrentPage(region.page_index);
      }
    } else {
      setSelectedRegionId(null);
    }
  };

  return (
    <div className="space-y-10 pb-16">
      {/* ------------------------------------------------------------- */}
      {/* SECTION A: DOCUMENT IDENTITY (COMPACT PROFESSIONAL HEADER)     */}
      {/* ------------------------------------------------------------- */}
      <DocumentIdentityHeader
        analysis={analysis}
        pageCount={pageCount}
        onOpenReportModal={() => setIsReportModalOpen(true)}
        onNavigateComparison={() => navigate(`/comparison?docA=${analysis.document_id}`)}
      />

      {/* ------------------------------------------------------------- */}
      {/* SECTION B: INTELLIGENT INVESTIGATION SUMMARY                   */}
      {/* (Verdict, Separate ML vs Heuristic Scores, Recommended Action) */}
      {/* ------------------------------------------------------------- */}
      <InvestigationSummaryCard
        analysis={analysis}
        onScrollToML={scrollToML}
        onScrollToEvidence={scrollToVisual}
      />

      {/* ------------------------------------------------------------- */}
      {/* INVESTIGATION WORKFLOW & VERIFICATION TIMELINE                */}
      {/* ------------------------------------------------------------- */}
      <InvestigationTimeline analysis={analysis} />

      {/* ------------------------------------------------------------- */}
      {/* SECTION C: WHY DID WE REACH THIS ASSESSMENT? (INSIGHT CARDS)  */}
      {/* ------------------------------------------------------------- */}
      <WhyWeReachedAssessment
        analysis={analysis}
        onSelectInsightTab={scrollToAdvancedTab}
      />

      {/* ------------------------------------------------------------- */}
      {/* SECTION D: MACHINE LEARNING ANALYSIS (EXPLAIN THE MODEL)      */}
      {/* ------------------------------------------------------------- */}
      <div ref={mlSectionRef}>
        <MLIntelligenceSection analysis={analysis} />
      </div>

      {/* ------------------------------------------------------------- */}
      {/* SECTION E: FEATURE ANALYSIS (UNDERSTANDABLE 18 FEATURES)      */}
      {/* ------------------------------------------------------------- */}
      <FeatureAnalysisSection analysis={analysis} />

      {/* ------------------------------------------------------------- */}
      {/* SECTION F: TWO-TRACK ANALYTICAL ARCHITECTURE & ARBITER        */}
      {/* ------------------------------------------------------------- */}
      <TwoTrackArbiterSection analysis={analysis} />

      {/* ------------------------------------------------------------- */}
      {/* SECTION G: DOCUMENT VISUAL INSPECTION (CANVAS & INSPECTOR)    */}
      {/* ------------------------------------------------------------- */}
      <section ref={visualSectionRef} className="space-y-4" aria-labelledby="visual-inspection-title">
        <div>
          <div className="flex items-center gap-2">
            <Eye size={18} className="text-brand" />
            <h2 id="visual-inspection-title" className="text-lg font-bold text-white tracking-tight">
              Visual Document Inspection
            </h2>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            Interactive high-resolution exhibit canvas with zoom controls, multi-page switcher, and suspicion heatmap toggle.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left: Document Viewer (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            <Card variant="evidence" title="Document Exhibit Viewer" icon={<Eye size={15} />}>
              <DocumentViewer 
                imageUrl={imageUrl}
                heatmapUrl={analysis.heatmap_available_pages?.includes(currentPage) ? `/api/v1/documents/${analysis.document_id}/heatmap?page=${currentPage}` : null}
                regions={regions}
                imageDimensions={analysis.image_dimensions}
                selectedRegionId={selectedRegionId}
                hoveredRegionId={hoveredRegionId}
                onRegionSelected={handleRegionSelected}
                onRegionHovered={setHoveredRegionId}
                isPdf={isPdf}
                originalFilename={analysis.original_filename}
                currentPage={currentPage}
                pageCount={pageCount}
                onPageChange={(newPage) => {
                  setCurrentPage(newPage);
                  setSelectedRegionId(null);
                }}
              />
            </Card>
          </div>

          {/* Right: Region Details & Quick Switcher (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            {/* Selected Region Card */}
            <Card variant="evidence" title="Region Findings Inspector">
              <RegionInspector 
                region={selectedRegion}
                onClearSelection={() => setSelectedRegionId(null)}
              />
            </Card>

            {/* Quick Regions List if any exist */}
            {regions.length > 0 && (
              <Card variant="evidence" title={`Flagged Visual Regions (${regions.length})`}>
                <div className="p-3 max-h-56 overflow-y-auto space-y-2">
                  {regions.map((reg) => (
                    <div
                      key={reg.id}
                      onClick={() => handleRegionSelected(selectedRegionId === reg.id ? null : reg)}
                      className={`p-2.5 rounded-lg border cursor-pointer text-xs flex items-center justify-between transition-colors ${
                        selectedRegionId === reg.id
                          ? 'bg-brand/20 border-brand text-white shadow'
                          : 'bg-ink-base border-ink-border text-gray-300 hover:bg-ink-hover'
                      }`}
                    >
                      <div>
                        <div className="font-semibold text-white capitalize">{reg.type.replace(/_/g, ' ')}</div>
                        <div className="text-[11px] text-gray-400">Page {(reg.page_index ?? 0) + 1} • Severity {reg.severity.toFixed(1)}</div>
                      </div>
                      <span className="text-xs text-brand font-semibold">
                        {selectedRegionId === reg.id ? 'Selected' : 'Focus'}
                      </span>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Multi-Page Quick Switcher (if PDF has multiple pages) */}
            {pageCount > 1 && analysis.pages_ml && analysis.pages_ml.length > 0 && (
              <Card variant="evidence" title={`Multi-Page Index (${pageCount} Pages)`}>
                <div className="p-3">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-ink-base text-gray-400 border-b border-ink-border font-medium">
                      <tr>
                        <th className="py-2 px-3">Page</th>
                        <th className="py-2 px-3">Score</th>
                        <th className="py-2 px-3">Tier</th>
                        <th className="py-2 px-3 text-right">Canvas</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-ink-border">
                      {analysis.pages_ml.map((p) => (
                        <tr 
                          key={p.page_index}
                          className={`hover:bg-ink-hover/50 ${currentPage === p.page_index ? 'bg-brand/10' : ''}`}
                        >
                          <td className="py-2 px-3 font-semibold text-gray-200">
                            Page {p.page_index + 1}
                          </td>
                          <td className="py-2 px-3 text-white font-bold">
                            {p.forgery_probability !== null ? `${Math.round(p.forgery_probability * 100)}%` : 'N/A'}
                          </td>
                          <td className="py-2 px-3">
                            <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                              p.risk_tier === 'HIGH_RISK'
                                ? 'bg-red-950 text-red-400 border border-red-800'
                                : p.risk_tier === 'SUSPICIOUS'
                                  ? 'bg-amber-950 text-amber-300 border border-amber-800'
                                  : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            }`}>
                              {p.risk_tier}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-right">
                            <button
                              onClick={() => {
                                setCurrentPage(p.page_index);
                                setSelectedRegionId(null);
                              }}
                              className="text-xs text-brand hover:underline font-semibold font-sans"
                            >
                              Switch
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION H: ADVANCED FORENSIC EVIDENCE (COLLAPSIBLE TELEMETRY) */}
      {/* ------------------------------------------------------------- */}
      <div ref={advancedSectionRef}>
        <AdvancedForensicEvidence
          analysis={analysis}
          pageCount={pageCount}
          custodyLogs={custodyLogs}
          custodyLoading={custodyLoading}
          activeTab={advancedTab}
          onTabChange={setAdvancedTab}
          onPageSelect={(page) => {
            setCurrentPage(page);
            setSelectedRegionId(null);
            visualSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }}
        />
      </div>

      {/* ------------------------------------------------------------- */}
      {/* FORENSIC PDF REPORT MODAL                                     */}
      {/* ------------------------------------------------------------- */}
      {analysis && (
        <GenerateReportModal
          isOpen={isReportModalOpen}
          onClose={() => setIsReportModalOpen(false)}
          documentId={analysis.document_id}
          documentFilename={analysis.original_filename}
          unifiedRiskTier={analysis.unified_risk_tier}
          compositeScore={analysis.composite_risk_score}
        />
      )}
    </div>
  );
}
