import React from 'react';
import { AlertCircle, AlertTriangle, Info, ShieldCheck } from 'lucide-react';
import Card from '@/components/ui/Card';
import type { ForensicLimitationItem } from '@/types';

interface Props {
  limitations: ForensicLimitationItem[];
  warnings?: string[];
}

export const RecommendationsPanel: React.FC<Props> = ({ limitations = [], warnings = [] }) => {
  return (
    <Card title="Forensic Limitations & Investigator Notices">
      <div className="p-6 space-y-6">
        {/* Forensic Limitation Notices */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">
            Mandatory Decision Support Disclaimers
          </h4>

          {limitations.length === 0 ? (
            <div className="flex items-center gap-2 p-3 bg-ink-base border border-ink-border rounded-sm text-xs text-muted font-mono">
              <ShieldCheck size={16} className="text-severity-low" />
              <span>Standard forensic screening caveats apply.</span>
            </div>
          ) : (
            <div className="space-y-3">
              {limitations.map((lim, idx) => {
                const isWarning = lim.severity === 'WARNING';
                const isCritical = lim.severity === 'CRITICAL';
                
                const borderClass = isCritical 
                  ? 'border-severity-critical/50 bg-severity-critical/10 text-severity-critical' 
                  : isWarning 
                  ? 'border-severity-high/50 bg-severity-high/10 text-severity-high' 
                  : 'border-brand/40 bg-brand/10 text-brand';

                const Icon = isCritical ? AlertCircle : isWarning ? AlertTriangle : Info;

                return (
                  <div key={idx} className={`p-3.5 rounded-sm border ${borderClass} space-y-1`}>
                    <div className="flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider">
                      <Icon size={14} className="shrink-0" />
                      <span>{lim.code}</span>
                      <span className="text-[10px] opacity-75">[{lim.severity}]</span>
                    </div>
                    <p className="text-xs text-gray-300 font-sans leading-relaxed pl-5">
                      {lim.message}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Pipeline Warnings */}
        {warnings && warnings.length > 0 && (
          <div className="space-y-2 pt-4 border-t border-ink-border">
            <h4 className="text-xs font-bold text-severity-high uppercase tracking-wider flex items-center gap-1.5">
              <AlertTriangle size={14} className="text-severity-high" />
              <span>Pipeline Stage Warnings ({warnings.length})</span>
            </h4>
            <div className="space-y-1.5">
              {warnings.map((warn, wIdx) => (
                <div 
                  key={wIdx} 
                  className="text-xs font-mono bg-ink-base border border-ink-border p-2.5 rounded-sm text-gray-300"
                >
                  ⚠ {warn}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
