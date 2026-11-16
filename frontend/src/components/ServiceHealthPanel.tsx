import { Database, Cpu, ScanLine, FileText, Type } from 'lucide-react';
import type { HealthResponse } from '@/types';

const services = [
  { key: 'database', label: 'Database & custody', icon: Database },
  { key: 'ml_engine', label: 'Frozen Random Forest', icon: Cpu },
  { key: 'visual_arbiter', label: 'Image forensics', icon: ScanLine },
  { key: 'pdf_processing', label: 'PDF processing', icon: FileText },
  { key: 'ocr_engine', label: 'Text extraction', icon: Type },
];

export default function ServiceHealthPanel({ health }: { health: HealthResponse | null }) {
  return <div className="space-y-4">
    <p className="text-xs text-muted leading-relaxed">Current service availability. Execution results are recorded separately for each exhibit.</p>
    <div className="space-y-2">
      {services.map(({ key, label, icon: Icon }) => {
        const module = health?.modules?.[key];
        const state = module?.status ?? 'unknown';
        const available = ['active', 'connected', 'available'].includes(state);
        return <div key={key} className="flex items-center justify-between gap-3 rounded-lg border border-ink-border bg-ink-base/50 p-3">
          <div className="flex items-center gap-3 min-w-0"><Icon size={16} className="text-brand shrink-0" /><span className="text-xs font-medium">{label}</span></div>
          <span title={module?.reason} className={`text-[10px] font-medium rounded-full px-2 py-1 capitalize ${available ? 'text-emerald-300 bg-emerald-400/10' : state === 'unknown' ? 'text-muted bg-ink-hover' : 'text-amber-300 bg-amber-400/10'}`}>{state === 'unknown' ? 'Not verified' : state}</span>
        </div>;
      })}
    </div>
    <div className="border-t border-ink-border pt-3 flex justify-between text-[10px] text-muted">
      <span>Environment: {health?.environment ?? 'Unavailable'}</span>
      <span>{typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'HTTPS connection' : 'Local HTTP preview'}</span>
    </div>
  </div>;
}
