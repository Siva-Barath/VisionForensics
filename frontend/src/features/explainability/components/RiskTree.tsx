import React from 'react';
import type { DecisionTraceItem } from '@/types';
import Card from '@/components/ui/Card';

interface Props {
  trace: DecisionTraceItem[];
}

export const RiskTree: React.FC<Props> = ({ trace }) => {
  return (
    <Card title="Decision Trace (Synthesis Audit Trail)">
      <div className="p-6 h-full overflow-y-auto max-h-[500px]">
        {(!trace || trace.length === 0) ? (
          <div className="p-6 text-center text-xs text-muted font-mono bg-ink-base border border-ink-border rounded-sm">
            No decision trace steps recorded.
          </div>
        ) : (
          <div className="relative border-l-2 border-ink-border ml-3 space-y-6">
            {trace.map((step, idx) => {
              const isTrack1 = step.track.toLowerCase().includes('track 1') || step.track.toLowerCase().includes('ml');
              const isTrack2 = step.track.toLowerCase().includes('track 2') || step.track.toLowerCase().includes('symbolic');
              const isSynthesis = step.track.toLowerCase().includes('arbiter') || step.track.toLowerCase().includes('synthesis');

              let dotClass = 'bg-brand';
              let badgeBg = 'bg-brand/10 text-brand border-brand/30';
              if (isTrack1) {
                dotClass = 'bg-cyan-500';
                badgeBg = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
              } else if (isTrack2) {
                dotClass = 'bg-amber-500';
                badgeBg = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
              } else if (isSynthesis) {
                dotClass = 'bg-emerald-500';
                badgeBg = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
              }

              return (
                <div key={idx} className="ml-6 relative">
                  {/* Step Dot */}
                  <span
                    className={`absolute -left-[31px] top-1 h-3.5 w-3.5 rounded-full ${dotClass} ring-4 ring-ink-base`}
                  ></span>

                  {/* Step Card */}
                  <div className="bg-ink-base p-4 rounded-sm border border-ink-border space-y-2">
                    <div className="flex justify-between items-center gap-2">
                      <span className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded-sm border ${badgeBg}`}>
                        {step.track}
                      </span>
                    </div>

                    <h4 className="font-mono text-xs font-bold text-gray-200">
                      {step.finding}
                    </h4>

                    {step.description && (
                      <p className="text-xs text-gray-400 font-sans leading-relaxed">
                        {step.description}
                      </p>
                    )}

                    {step.features_considered && (
                      <div className="text-[10px] text-muted font-mono bg-ink-panel p-2 rounded-sm border border-ink-border">
                        <strong className="text-gray-300">Features Evaluated:</strong> {step.features_considered}
                      </div>
                    )}

                    {step.evidence_items && step.evidence_items.length > 0 && (
                      <div className="mt-2 space-y-1.5 pt-2 border-t border-ink-border">
                        <p className="text-[10px] font-bold text-muted uppercase tracking-wider">
                          Granular Evidence Items ({step.evidence_items.length})
                        </p>
                        {step.evidence_items.map((item, itemIdx) => (
                          <div 
                            key={itemIdx} 
                            className="text-xs font-mono bg-ink-panel/70 p-2 rounded-sm border border-ink-border flex justify-between items-start gap-2"
                          >
                            <div>
                              <span className="text-brand font-bold mr-2">[{item.category || 'FINDING'}]</span>
                              <span className="text-gray-300">{item.description || 'Evidence detail'}</span>
                            </div>
                            {item.severity !== undefined && (
                              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-sm bg-ink-border text-gray-300">
                                Sev: {item.severity}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
};
