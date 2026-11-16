import type { ReactNode } from 'react';
import { ScanLine, ShieldCheck, Fingerprint, ArrowUpRight } from 'lucide-react';

export default function AuthShell({ children, registration = false }: { children: ReactNode; registration?: boolean }) {
  return (
    <div className="auth-shell">
      <aside className="auth-story" aria-label="About VisionForensics">
        <div className="flex items-center gap-3"><div className="brand-symbol"><ShieldCheck size={23} /></div><span className="font-semibold text-lg text-white tracking-tight">VisionForensics<span className="text-brand">.</span></span></div>
        <div className="auth-story-content">
          <p className="eyebrow"><span /> Document intelligence, elevated</p>
          <h2>Look closer.<br />See the <span>whole story.</span></h2>
          <p className="auth-story-description">Bring clarity to complex documents with forensic analysis, visual evidence, and a connected investigation workspace.</p>
          <div className="document-art" aria-hidden="true">
            <div className="art-document"><div className="art-document-heading"><Fingerprint size={30} /><span>DOCUMENT EXAMINATION</span></div><div className="art-line long" /><div className="art-line" /><div className="art-line long" /><div className="art-region"><ScanLine size={26} /><span>Every detail tells a story</span></div><div className="art-line" /><div className="art-line short" /><div className="art-document-footer">VISIONFORENSICS <ArrowUpRight size={16} /></div></div>
            <div className="art-caption"><ScanLine size={18} /><div><p>Evidence in focus</p><span>From first inspection to final report</span></div></div>
          </div>
        </div>
        <p className="text-xs text-muted">Built for careful examination. Designed for clear decisions.</p>
      </aside>
      <main className="auth-form-side">
        <div className="auth-mobile-brand"><ShieldCheck size={24} /> VisionForensics.</div>
        <div className="auth-form-intro"><p className="eyebrow">Your investigation workspace</p><h1>{registration ? 'Create your account' : 'Welcome back'}</h1><p>{registration ? 'Set up your analyst profile to get started.' : 'Sign in to continue your investigations.'}</p></div>
        {children}
        <p className="auth-footnote"><ShieldCheck size={13} /> VisionForensics · Document examination workspace</p>
      </main>
    </div>
  );
}
