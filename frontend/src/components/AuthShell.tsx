import type { ReactNode } from 'react';
import { ShieldCheck, Fingerprint } from 'lucide-react';

export default function AuthShell({ children, registration = false }: { children: ReactNode; registration?: boolean }) {
  return (
    <div className="min-h-screen grid grid-cols-1 lg:grid-cols-2 bg-[#F8F9FF]">
      {/* Left: Deep Navy-Violet Story Side */}
      <aside className="hidden lg:flex flex-col justify-between p-12 bg-gradient-to-br from-[#161234] via-[#1e1545] to-[#18103c] text-white border-r border-[#261B50]" aria-label="About VisionForensics">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-violet-600/30 border border-violet-500/40 text-violet-300 flex items-center justify-center shadow-inner">
            <ShieldCheck size={22} className="text-violet-300" />
          </div>
          <span className="font-bold text-lg text-white tracking-tight">VisionForensics AI</span>
        </div>

        <div className="max-w-md space-y-6 my-auto">
          <span className="text-[11px] font-bold uppercase tracking-wider text-violet-300 bg-violet-900/40 border border-violet-700/50 px-3 py-1 rounded-full">
            Document intelligence, elevated
          </span>
          <h2 className="text-4xl font-extrabold tracking-tight leading-tight text-white">
            Look closer.<br /><span className="text-[#9B7EF0]">See the whole story.</span>
          </h2>
          <p className="text-sm text-[#A29EBC] leading-relaxed">
            Bring clarity to complex documents with machine learning forensics, ELA heatmaps, and a connected investigation workspace.
          </p>

          <div className="p-5 rounded-2xl bg-white/[0.04] border border-white/[0.08] space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono text-[#DDD5F9]">
              <Fingerprint size={18} className="text-[#9B7EF0]" />
              <span>DEFENSE-GRADE DOCUMENT EXAMINATION</span>
            </div>
            <p className="text-xs text-[#A29EBC] leading-relaxed">
              Automated physical substrate screening, copy-move verification, and immutable SHA-256 chain of custody.
            </p>
          </div>
        </div>

        <p className="text-xs text-[#79749A]">Built for careful examination. Designed for clear decisions.</p>
      </aside>

      {/* Right: Clean White Form Side */}
      <main className="flex flex-col justify-center items-center p-8 sm:p-12 bg-white">
        <div className="w-full max-w-md space-y-6">
          {/* Brand header for mobile */}
          <div className="flex lg:hidden items-center gap-2.5 mb-2">
            <div className="w-8 h-8 rounded-lg bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center">
              <ShieldCheck size={18} />
            </div>
            <span className="font-bold text-[#17172F]">VisionForensics AI</span>
          </div>

          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#7045E8] block mb-1">
              Your Investigation Workspace
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-[#17172F]">
              {registration ? 'Create Analyst Profile' : 'Welcome to VisionForensics'}
            </h1>
            <p className="text-xs text-[#73758B] mt-1">
              {registration ? 'Provision your examiner credentials to access the workspace.' : 'Sign in with your authorized institutional email to continue.'}
            </p>
          </div>

          {children}

          <p className="text-center text-xs text-[#73758B] pt-4">
            VisionForensics AI • Document Forgery Detection Platform
          </p>
        </div>
      </main>
    </div>
  );
}
