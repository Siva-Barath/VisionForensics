from pathlib import Path
root = Path(__file__).resolve().parents[1]
def edit(name, fn):
    p=root/name
    p.write_text(fn(p.read_text(encoding='utf-8')), encoding='utf-8')

def cases(s):
    s=s.replace("import { listDocuments }", "import { listDocuments, listCases }")
    s=s.replace("import type { DocumentSummary }", "import type { DocumentSummary, InvestigationCase }")
    s=s.replace("  const [loading,", "  const [cases, setCases] = useState<InvestigationCase[]>([]);\n  const [error, setError] = useState(false);\n  const [loading,",1)
    s=s.replace('    listDocuments(100, 0)', '    setError(false);\n    Promise.all([listDocuments(100, 0), listCases()])')
    s=s.replace('.then((data) => {\n        setDocuments(data || []);', '.then(([data, caseData]) => {\n        setCases(caseData);\n        setDocuments(data || []);')
    s=s.replace('.catch(() => {\n        setLoading(false);', '.catch(() => {\n        setError(true);\n        setLoading(false);')
    s=s.replace('      {/* Header */}', '''      {error && <div role="alert" className="p-4 border border-red-400/30 rounded-xl text-red-300 text-sm">Unable to load the workspace. <button onClick={fetchCases} className="underline">Retry</button></div>}
      {/* Header */}''')
    marker='      {/* Search'
    idx=s.find(marker)
    if idx<0: idx=s.index('      <Card')
    panel='''      <section aria-label="Investigation cases" className="space-y-3">
        <h2 className="text-lg font-semibold">Investigation cases</h2>
        <p className="text-xs text-muted">Latest 100 cases visible to your account. Create a case with New investigation.</p>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{cases.map(item => <article key={item.id} className="p-5 rounded-xl border border-ink-border bg-ink-panel space-y-2">
          <div className="flex justify-between gap-2 text-[10px] text-muted"><span>{item.case_number}</span><span className="uppercase text-brand">{item.priority}</span></div>
          <h3 className="font-semibold text-sm">{item.title}</h3>
          {item.notes && <p className="text-xs text-muted whitespace-pre-wrap">{item.notes}</p>}
          <p className="text-xs text-muted">{item.document_count} exhibit(s) · {item.status}</p>
        </article>)}</div>
        {!loading && !error && cases.length === 0 && <p className="text-sm text-muted">No investigation cases yet.</p>}
      </section>
'''
    s=s[:idx]+panel+s[idx:]
    s=s.replace('const score = Math.round(doc.composite_risk_score || 0);', "const score = doc.composite_risk_score == null ? 'Unavailable' : `${Math.round(doc.composite_risk_score)}/100`;")
    return s.replace('{score}%', '{score}').replace('Browse and inspect all analyzed evidence exhibits and examination findings.', 'Browse your cases and the latest 100 evidence exhibits. Search applies to the loaded exhibits.')
edit('frontend/src/pages/CasesPage.tsx', cases)

def analytics(s):
    s=s.replace("import { listDocuments }", "import ServiceHealthPanel from '@/components/ServiceHealthPanel';\nimport { listDocuments, getWorkspaceStats, checkHealth }")
    s=s.replace("import type { DocumentSummary }", "import type { DocumentSummary, WorkspaceStats, HealthResponse }")
    s=s.replace('  const [loading,', "  const [totals, setTotals] = useState<WorkspaceStats | null>(null);\n  const [health, setHealth] = useState<HealthResponse | null>(null);\n  const [error, setError] = useState(false);\n  const [loading,",1)
    s=s.replace('    listDocuments(100, 0)', '    setError(false);\n    Promise.all([listDocuments(100, 0), getWorkspaceStats(), checkHealth().catch(() => null)])')
    s=s.replace('.then((data) => {\n        setDocuments(data || []);', '.then(([data, counts, healthData]) => {\n        setTotals(counts);\n        setHealth(healthData);\n        setDocuments(data || []);')
    s=s.replace('.catch(() => {\n        setLoading(false);', '.catch(() => {\n        setError(true);\n        setLoading(false);')
    s=s.replace('const total = documents.length;', 'const total = totals?.total_documents ?? 0;')
    for k, v in [('highRisk','high_risk'),('suspicious','requires_review'),('lowRisk','low_risk')]:
        import re
        s=re.sub(r'const '+k+r' = documents.filter\([^\n]+', f'const {k} = totals?.{v} ?? 0;', s)
    s=s.replace('pct: total > 0 ? Math.round((count / total) * 100) : 0,', 'pct: documents.length > 0 ? Math.round((count / documents.length) * 100) : 0,')
    s=s.replace('}, [documents]);','}, [documents, totals]);')
    s=s.replace("'Authentic Baselines'", "'Low Risk Documents'")
    s=s.replace(': stat.value}', ": totals ? stat.value : 'Unavailable'}")
    s=s.replace('title="Analyzed File Formats"', 'title="File formats · latest 100 exhibits"')
    a=s.index('          <div className="p-5 space-y-3 text-xs">', s.index('{/* Active Inspection Capabilities */}'))
    b=s.index('        </Card>',a)
    s=s[:a]+'          <ServiceHealthPanel health={health} />\n'+s[b:]
    s=s.replace('      {/* Key Metrics Grid */}', '      {error && <p role="alert" className="text-sm text-red-300">Analytics could not be loaded. Refresh to retry.</p>}\n      {/* Key Metrics Grid */}')
    return s
edit('frontend/src/pages/AnalyticsPage.tsx', analytics)

def comparison(s):
    s=s.replace('getComparisonArtifactUrl }', 'getComparisonArtifactUrl, listDocuments }')
    s=s.replace('ComparisonResponse, DifferentialRegion }', 'ComparisonResponse, DifferentialRegion, DocumentSummary }')
    s=s.replace('  // Document IDs from query params', "  const [exhibits, setExhibits] = useState<DocumentSummary[]>([]);\n  useEffect(() => { listDocuments(100, 0).then(setExhibits).catch(() => setExhibits([])); }, []);\n\n  // Document IDs from query params")
    s=s.replace('placeholder="Document A UUID..."', 'list="comparison-exhibits" aria-label="First exhibit" placeholder="Select or enter exhibit ID"')
    s=s.replace('placeholder="Document B UUID..."', 'list="comparison-exhibits" aria-label="Second exhibit" placeholder="Select or enter exhibit ID"')
    idx=s.index('      <',s.index('  return ('))
    # Datalist lives in the returned root, before the first child.
    idx=s.index('\n',idx)+1
    s=s[:idx]+'      <datalist id="comparison-exhibits">{exhibits.map(doc => <option key={doc.id} value={doc.id}>{doc.original_filename}</option>)}</datalist>\n'+s[idx:]
    return s
edit('frontend/src/features/comparison/pages/DocumentComparisonPage.tsx', comparison)

def home(s):
    s=s.replace('  const [stats,', '  const [documentsError, setDocumentsError] = useState(false);\n  const [stats,',1)
    s=s.replace('listDocuments(50, 0).catch(() => []),', 'listDocuments(50, 0).catch(() => { if (isMounted) setDocumentsError(true); return []; }),')
    s=s.replace('      {/* Header with Actions */}', '      {documentsError && <p role="alert" className="text-sm text-red-300">Recent exhibits could not be loaded. Refresh the page to retry.</p>}\n      {/* Header with Actions */}')
    return s
edit('frontend/src/pages/HomePage.tsx', home)
