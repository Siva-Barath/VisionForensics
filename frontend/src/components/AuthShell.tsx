import type { ReactNode } from 'react';
import { 
  ShieldCheck, 
  Cpu, 
  Layers, 
  FileText, 
  Microscope, 
  Zap, 
  Fingerprint
} from 'lucide-react';

interface Props {
  children: ReactNode;
  registration?: boolean;
}

export default function AuthShell({ children }: Props) {
  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-[#F8F9FF] relative overflow-x-hidden font-sans">
      {/* ========================================================================= */}
      {/* LEFT SECTION: Brand & Product Presentation Panel (50% on Desktop)         */}
      {/* ========================================================================= */}
      <aside 
        className="w-full lg:w-[50%] min-h-screen bg-[#17102F] relative flex flex-col justify-between p-8 sm:p-12 lg:p-14 overflow-hidden z-10 shrink-0"
        aria-label="VisionForensics AI Presentation"
      >
        {/* Ambient Glows */}
        <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-[#6D35E8]/25 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-1/3 left-10 w-72 h-72 bg-[#5023D9]/20 rounded-full blur-[90px] pointer-events-none" />

        {/* Decorative Wave Ribbon Accents at bottom-left */}
        <div className="absolute -bottom-24 -left-20 w-96 h-96 rounded-full border border-violet-500/10 pointer-events-none" />
        <div className="absolute -bottom-12 -left-10 w-80 h-80 rounded-full border border-violet-500/15 pointer-events-none" />
        <div className="absolute -bottom-36 left-40 w-96 h-96 rounded-full border border-violet-500/10 pointer-events-none" />

        {/* Organic S-Curve Divider (visible on desktop) */}
        <svg
          viewBox="0 0 100 1000"
          preserveAspectRatio="none"
          className="absolute top-0 right-0 h-full w-16 lg:w-24 text-[#F8F9FF] fill-current pointer-events-none hidden lg:block translate-x-[1px]"
          aria-hidden="true"
        >
          <path d="M 100,0 C 0,320 0,680 100,1000 L 100,0 Z" />
        </svg>

        {/* TOP: Brand Header */}
        <div className="flex items-center gap-3.5 relative z-10">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-[#7045E8] to-[#4D24BF] border border-white/20 text-white flex items-center justify-center shadow-lg shadow-violet-950/50 shrink-0">
            <ShieldCheck size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight leading-tight">
              VisionForensics AI
            </h1>
            <p className="text-xs text-[#B6B2D8] font-normal leading-tight mt-0.5">
              Document Forgery Analysis
            </p>
          </div>
        </div>

        {/* MIDDLE CONTENT: Heading, Description, Illustration & Feature Cards */}
        <div className="my-auto py-8 space-y-6 max-w-xl relative z-10">
          {/* Main Headings */}
          <div className="space-y-2">
            <h2 className="text-3xl sm:text-4xl lg:text-[38px] font-extrabold text-white leading-tight tracking-tight">
              Forensic Intelligence for <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#A78BFA] via-[#C4B5FD] to-[#DDD6FE]">
                Document Investigation
              </span>
            </h2>
            <p className="text-xs sm:text-sm text-[#B6B2D8] leading-relaxed max-w-md pt-1">
              Detect manipulation, analyze authenticity, and generate court-ready evidence with AI and scientific forensics.
            </p>
          </div>

          {/* Central Forensic Examination Illustration */}
          <div className="py-2 flex items-center justify-center">
            <div className="relative w-64 h-48 flex items-center justify-center">
              {/* Radial Glow */}
              <div className="absolute inset-0 bg-[#6D35E8]/30 rounded-full blur-2xl" />

              {/* Tilted Back Document */}
              <div className="absolute w-40 h-32 bg-white/10 border border-white/15 rounded-xl shadow-lg -rotate-6 transform -translate-x-4 -translate-y-2 backdrop-blur-xs flex flex-col p-3 space-y-2">
                <div className="w-12 h-2 bg-white/20 rounded-full" />
                <div className="w-24 h-1.5 bg-white/15 rounded-full" />
                <div className="w-20 h-1.5 bg-white/15 rounded-full" />
              </div>

              {/* Front Document */}
              <div className="relative w-44 h-36 bg-gradient-to-br from-[#F5F2FF] to-[#E9E4F9] border border-white/40 rounded-xl shadow-xl p-3.5 space-y-2">
                {/* Header line */}
                <div className="flex items-center justify-between pb-1 border-b border-violet-200/50">
                  <div className="w-14 h-2 bg-violet-400/50 rounded-full" />
                  <div className="w-4 h-4 rounded-full bg-violet-300/40" />
                </div>
                {/* Content lines */}
                <div className="space-y-1.5 pt-1">
                  <div className="w-full h-1.5 bg-violet-300/40 rounded-full" />
                  <div className="w-28 h-1.5 bg-violet-300/35 rounded-full" />
                  <div className="w-32 h-1.5 bg-violet-300/35 rounded-full" />
                  <div className="w-20 h-1.5 bg-violet-300/30 rounded-full" />
                </div>
              </div>

              {/* Magnifying Glass & Scanner Reticle Over Document */}
              <div className="absolute right-6 bottom-2 z-20 flex items-center justify-center pointer-events-none">
                {/* Lens Circle with Purple Glow */}
                <div className="w-24 h-24 rounded-full border-4 border-[#7045E8] bg-[#2E1A66]/40 backdrop-blur-sm shadow-xl flex items-center justify-center relative shadow-violet-900/60">
                  {/* Scanner Corner Brackets */}
                  <div className="absolute inset-2 pointer-events-none">
                    <div className="absolute top-0 left-0 w-2.5 h-2.5 border-t-2 border-l-2 border-[#C4B5FD]" />
                    <div className="absolute top-0 right-0 w-2.5 h-2.5 border-t-2 border-r-2 border-[#C4B5FD]" />
                    <div className="absolute bottom-0 left-0 w-2.5 h-2.5 border-b-2 border-l-2 border-[#C4B5FD]" />
                    <div className="absolute bottom-0 right-0 w-2.5 h-2.5 border-b-2 border-r-2 border-[#C4B5FD]" />
                  </div>

                  {/* Glowing Fingerprint Icon */}
                  <Fingerprint size={38} className="text-[#DDD6FE] animate-pulse" />

                  {/* Magnifying Handle */}
                  <div 
                    className="absolute -bottom-4 -right-4 w-5 h-10 bg-gradient-to-b from-[#7045E8] to-[#4D24BF] rounded-full border-2 border-white/20 shadow-md transform rotate-[-45deg]" 
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Three Feature Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            {/* Card 1 */}
            <div className="bg-white/[0.05] border border-white/10 rounded-2xl p-3.5 backdrop-blur-sm space-y-1.5 shadow-sm">
              <div className="w-7 h-7 rounded-lg bg-violet-600/30 border border-violet-500/40 text-violet-300 flex items-center justify-center">
                <Cpu size={15} />
              </div>
              <h3 className="text-xs font-bold text-white tracking-tight">ML Screening</h3>
              <p className="text-[10px] text-[#A29EBC] leading-tight">
                Random Forest <br />(18 Features)
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-white/[0.05] border border-white/10 rounded-2xl p-3.5 backdrop-blur-sm space-y-1.5 shadow-sm">
              <div className="w-7 h-7 rounded-lg bg-violet-600/30 border border-violet-500/40 text-violet-300 flex items-center justify-center">
                <Layers size={15} />
              </div>
              <h3 className="text-xs font-bold text-white tracking-tight">ELA & Copy-Move</h3>
              <p className="text-[10px] text-[#A29EBC] leading-tight">
                Expose editing and <br />duplicate regions
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-white/[0.05] border border-white/10 rounded-2xl p-3.5 backdrop-blur-sm space-y-1.5 shadow-sm">
              <div className="w-7 h-7 rounded-lg bg-violet-600/30 border border-violet-500/40 text-violet-300 flex items-center justify-center">
                <ShieldCheck size={15} />
              </div>
              <h3 className="text-xs font-bold text-white tracking-tight">Evidence Governance</h3>
              <p className="text-[10px] text-[#A29EBC] leading-tight">
                SHA-256 custody <br />with audit logs
              </p>
            </div>
          </div>
        </div>

        {/* BOTTOM: Trust Indicators Capsule */}
        <div className="relative z-10 pt-2">
          <div className="bg-white/[0.04] border border-white/10 rounded-full px-5 py-2.5 flex items-center justify-between text-xs text-[#B6B2D8] font-medium w-full max-w-lg shadow-inner">
            <div className="flex items-center gap-1.5">
              <FileText size={14} className="text-[#A78BFA]" />
              <span>Trusted Analysis</span>
            </div>
            <span className="text-white/20">|</span>
            <div className="flex items-center gap-1.5">
              <Microscope size={14} className="text-[#A78BFA]" />
              <span>Forensic-Grade</span>
            </div>
            <span className="text-white/20">|</span>
            <div className="flex items-center gap-1.5">
              <Zap size={14} className="text-amber-400" />
              <span>Fast & Reliable</span>
            </div>
          </div>
        </div>
      </aside>

      {/* ========================================================================= */}
      {/* RIGHT SECTION: Clean Authentication Panel (50% on Desktop)               */}
      {/* ========================================================================= */}
      <main className="w-full lg:w-[50%] min-h-screen bg-[#F8F9FF] flex items-center justify-center p-6 sm:p-10 lg:p-14 z-10">
        <div className="w-full max-w-[520px]">
          {children}
        </div>
      </main>
    </div>
  );
}
