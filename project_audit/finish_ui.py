from pathlib import Path

root = Path(__file__).resolve().parents[1]
def edit(name, transform):
    p = root / name
    p.write_text(transform(p.read_text(encoding='utf-8')), encoding='utf-8')

def dashboard(s):
    s = s.replace("import { DocumentViewer }", "import ForensicModules from '../components/ForensicModules';\nimport { DocumentViewer }")
    a = s.index('  // Helper status badge styles')
    b = s.index('  // 9 Modules Evaluated Data', a)
    s = s[:a] + s[b:]
    s = s.replace("  const signatureRegions = regions.filter(r => r.type.toLowerCase().includes('signature') || r.type.toLowerCase().includes('stamp'));", '')
    a = s.index('      <div>', s.index('SECTION B:'))
    b = s.index('      {/* ------------------------------------------------------------- */}', a)
    s = s[:a] + '      <ForensicModules analysis={analysis} onDetails={scrollToAdvancedTab} />\n\n' + s[b:]
    s = s.replace("{isHighRisk ? 'Above Threshold (T=0.40)' : isSuspicious ? 'Borderline Range' : 'Below Threshold (T=0.40)'}", 'Heuristic display score, not a probability')
    s = s.replace('              imageUrl={imageUrl}', '              imageUrl={imageUrl}\n              heatmapUrl={analysis.heatmap_available_pages?.includes(currentPage) ? `/api/v1/documents/${analysis.document_id}/heatmap?page=${currentPage}` : null}')
    s = s.replace('Case ID: {analysis.document_id', 'Exhibit ID: {analysis.document_id')
    s = s.replace('          <button\n            onClick={() => navigate(`/comparison', '          <a href={`/api/v1/documents/${analysis.document_id}/original`} className="text-xs text-brand hover:underline">Download original</a>\n          <button\n            onClick={() => navigate(`/comparison')
    return s
edit('frontend/src/features/explainability/pages/InvestigationDashboardPage.tsx', dashboard)

def viewer(s):
    s = s.replace('  imageUrl: string | null;', '  imageUrl: string | null;\n  heatmapUrl?: string | null;')
    s = s.replace('  imageUrl,', '  imageUrl,\n  heatmapUrl,', 1)
    s = s.replace('  const [showHeatmap', '  const [heatmapError, setHeatmapError] = useState(false);\n  useEffect(() => { setHeatmapError(false); setShowHeatmap(false); }, [heatmapUrl]);\n  const [showHeatmap')
    s = s.replace('Clean substrate', 'No regions flagged')
    s = s.replace('onClick={() => setShowHeatmap(!showHeatmap)}', 'onClick={() => setShowHeatmap(!showHeatmap)}\n            disabled={!heatmapUrl || heatmapError}')
    s = s.replace('title="Toggle Suspicion & ELA Heatmap View"', 'title={heatmapUrl ? "Toggle derived ELA error map" : "No stored ELA map for this page"}')
    a = s.index('            {/* Suspicion / ELA Heatmap Thermal Overlay */}')
    b = s.index('            {/* SVG Genuine Evidence', a)
    s = s[:a] + '''            {imageLoaded && showHeatmap && heatmapUrl && !heatmapError && (
              <img src={heatmapUrl} alt="Derived normalized ELA error map" className="absolute inset-0 w-full h-full opacity-75 pointer-events-none" onError={() => { setHeatmapError(true); setShowHeatmap(false); }} />
            )}
            {heatmapError && <div role="status" className="absolute top-2 left-2 bg-ink-base p-2 text-xs text-amber-300">Stored ELA map could not be loaded.</div>}
            {showHeatmap && !heatmapError && <div className="absolute top-2 right-2 bg-ink-base/95 p-2 text-[10px] z-20 text-gray-200">Normalized ELA error · dark to yellow · not a risk probability</div>}

''' + s[b:]
    return s.replace('Suspicion Heatmap Toggle', 'Stored ELA Map Toggle')
edit('frontend/src/features/explainability/components/DocumentViewer.tsx', viewer)
edit('frontend/src/types/analysis.ts', lambda s: s.replace('export interface DocumentAnalysisResponse {', 'export interface DocumentAnalysisResponse {\n  heatmap_available_pages?: number[];'))

def settings(s):
    s = s.replace("import { useState }", "import { useState, useEffect }")
    s = s.replace("import { Eye, FileText, Fingerprint, Copy, Shield, Cpu, HardDrive }", "import { Shield }")
    s = s.replace("import Card from", "import ServiceHealthPanel from '@/components/ServiceHealthPanel';\nimport { checkHealth } from '@/services/api';\nimport type { HealthResponse } from '@/types';\nimport Card from")
    a = s.index('  const detectors =')
    b = s.index('  const formatRole', a)
    s = s[:a] + "  const [health, setHealth] = useState<HealthResponse | null>(null);\n  useEffect(() => { checkHealth().then(setHealth).catch(() => setHealth(null)); }, []);\n\n" + s[b:]
    a = s.index('              <div className="p-5 space-y-3 text-xs">', s.index("{activeTab === 'modules'"))
    b = s.index('            </Card>', a)
    s = s[:a] + '              <ServiceHealthPanel health={health} />\n' + s[b:]
    s = s.replace('9b26563604f810141f06129851604a3729e1fca9473d09a3bf87ea9bb4716960', 'eaef52167d829396728b78af848acae3ef62097538cb8433de29aa635c45c3dc')
    s = s.replace('Standardized threshold calibrated on held-out evaluation datasets.', 'Existing approved operational threshold. No recalibration was performed in this stabilization.')
    s = s.replace('Mitigates token replay attacks and guarantees automated session revocation.', 'Refresh tokens rotate on use; access tokens expire according to the configured session policy.')
    s = s.replace('Armed & Operational', 'SHA-256 verification on exhibit retrieval')
    return s
edit('frontend/src/pages/SettingsPage.tsx', settings)
