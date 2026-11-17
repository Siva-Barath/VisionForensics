import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Upload, 
  FileText, 
  AlertTriangle, 
  Loader2, 
  ArrowLeft, 
  ArrowRight,
  FileCheck,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  Search,
  Eye,
  FileCode2,
} from 'lucide-react';
import Card from '@/components/ui/Card';
import { uploadDocument } from '@/services/api';
import { extractApiError } from '@/utils/helpers';
import { MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from '@/utils/constants';

const ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg'];

const CASE_PRESETS = [
  'Employment Contract Audit',
  'Identity Document Check',
  'Commercial Invoice Audit',
  'Financial Statement Review',
  'Official Certificate Verification',
];

export default function NewInvestigationPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [clientError, setClientError] = useState<string | null>(null);

  // Step 2: Case Details
  const [caseTitle, setCaseTitle] = useState('');
  const [caseNotes, setCaseNotes] = useState('');
  const [priority, setPriority] = useState<'routine' | 'urgent'>('routine');

  // Step 3: Analysis Execution State
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [activeStageIndex, setActiveStageIndex] = useState(0);
  const [apiError, setApiError] = useState<string | null>(null);

  const stages = [
    { label: 'File Intake & Payload Validation', desc: 'Verifying file format, boundary safety, and MIME structure' },
    { label: 'SHA-256 Fingerprint & Custody Ledger', desc: 'Generating immutable cryptographic hash for chain of custody' },
    { label: 'Physical Forensic Feature Extraction', desc: 'Extracting 18 physical features: ELA, Laplacian blur, noise & texture' },
    { label: 'Dual-Track Analysis & Model Screening', desc: 'Screening via frozen Random Forest (T=0.40) & symbolic rules' },
    { label: 'Synthesis Arbiter & Dossier Assembly', desc: 'Reconciling findings and preparing unified forensic assessment' },
  ];

  // Cleanup thumbnail preview URL on unmount or file change
  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    if (['png', 'jpg', 'jpeg'].includes(ext)) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setPreviewUrl(null);
    }
  }, [file]);

  const validateAndSetFile = (selectedFile: File) => {
    setClientError(null);
    const ext = selectedFile.name.split('.').pop()?.toLowerCase() || '';

    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setClientError(
        `Unsupported file format (.${ext || 'unknown'}). Supported formats are PDF, PNG, and JPEG documents.`
      );
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      setClientError(
        `File exceeds maximum allowed upload size of ${MAX_FILE_SIZE_MB} MB (${(selectedFile.size / 1024 / 1024).toFixed(1)} MB provided).`
      );
      return;
    }

    setFile(selectedFile);
    if (!caseTitle) {
      const baseName = selectedFile.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');
      setCaseTitle(baseName);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const startAnalysis = async () => {
    if (!file || isUploading) return;

    setStep(3);
    setIsUploading(true);
    setUploadProgress(15);
    setActiveStageIndex(0);
    setApiError(null);

    // Staged progression timer simulation while backend processes
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev < 30) {
          setActiveStageIndex(1);
          return prev + 5;
        }
        if (prev < 55) {
          setActiveStageIndex(2);
          return prev + 4;
        }
        if (prev < 80) {
          setActiveStageIndex(3);
          return prev + 3;
        }
        if (prev < 92) {
          setActiveStageIndex(4);
          return prev + 1;
        }
        return prev;
      });
    }, 400);

    try {
      const response = await uploadDocument(
        file,
        (percent) => {
          if (percent > 30) {
            setUploadProgress((p) => Math.max(p, Math.min(88, percent)));
          }
        },
        { title: caseTitle, notes: caseNotes, priority }
      );

      clearInterval(progressInterval);
      setActiveStageIndex(4);
      setUploadProgress(100);

      if (response.processing_status === 'failed') {
        throw new Error(
          `Exhibit ${response.document_id} was retained, but automated processing encountered an error. Check file structure or try another document.`
        );
      }

      if (response && response.document_id) {
        setTimeout(() => {
          navigate(`/investigation/${response.document_id}`);
        }, 750);
      } else {
        throw new Error('Analysis completed but document ID was not received from the forensic engine.');
      }
    } catch (err: unknown) {
      clearInterval(progressInterval);
      setIsUploading(false);
      const parsedError = extractApiError(err);
      setApiError(parsedError);
    }
  };

  return (
    <div className="investigation-intake max-w-4xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="border-b border-ink-border pb-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono uppercase tracking-wider text-brand font-semibold bg-brand/10 px-2 py-0.5 rounded-sm border border-brand/20">
              Forensic Evidence Intake
            </span>
            <span className="text-[11px] font-mono text-gray-500">T=0.40 Locked Protocol</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight mt-1">New Document Investigation</h1>
          <p className="text-sm text-gray-400 mt-1">
            Submit a physical or digital document exhibit for automated tamper detection, ELA, and ML classification.
          </p>
        </div>
        <button
          onClick={() => navigate('/')}
          className="text-xs text-gray-400 hover:text-gray-200 transition-colors flex items-center gap-1.5"
        >
          <ArrowLeft size={14} /> Back to Overview
        </button>
      </div>

      {/* 3-Step Wizard Navigation */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { num: 1, title: 'Upload Exhibit', desc: 'Select PDF or image' },
          { num: 2, title: 'Case Metadata', desc: 'Reference & priority' },
          { num: 3, title: 'Forensic Examination', desc: 'Multi-track analysis' },
        ].map((s) => {
          const isActive = step === s.num;
          const isDone = step > s.num;
          return (
            <div
              key={s.num}
              className={`p-3 rounded-sm border transition-all ${
                isActive
                  ? 'bg-brand/15 border-brand text-brand shadow-sm shadow-brand/10'
                  : isDone
                  ? 'bg-ink-panel border-emerald-800/80 text-emerald-400'
                  : 'bg-ink-base border-ink-border text-gray-400'
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                    isActive
                      ? 'bg-brand text-white'
                      : isDone
                      ? 'bg-emerald-500 text-black'
                      : 'bg-ink-border text-gray-400'
                  }`}
                >
                  {isDone ? '✓' : s.num}
                </span>
                <span className="text-xs font-bold">{s.title}</span>
              </div>
              <p className="text-[10px] text-gray-400 mt-1 pl-7 hidden sm:block">{s.desc}</p>
            </div>
          );
        })}
      </div>

      {/* STEP 1: Upload Document */}
      {step === 1 && (
        <Card variant="evidence" className="p-6 space-y-6">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Upload size={18} className="text-brand" /> Select Document Exhibit
            </h2>
            <p className="text-xs text-gray-400">
              Upload original files for authentic forensic evaluation. Supported formats: PDF, PNG, JPG, JPEG (up to {MAX_FILE_SIZE_MB} MB).
            </p>
          </div>

          {/* Drag & Drop Box */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            role="button"
            tabIndex={0}
            aria-label="Choose a document to investigate"
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                document.getElementById('file-upload-input')?.click();
              }
            }}
            className={`upload-dropzone border-2 border-dashed rounded-md p-8 text-center transition-all cursor-pointer relative ${
              file 
                ? 'border-emerald-500/70 bg-emerald-950/20' 
                : clientError 
                ? 'border-red-500/70 bg-red-950/20' 
                : 'border-ink-border hover:border-brand/70 hover:bg-ink-hover/40 bg-ink-base/80'
            }`}
            onClick={() => document.getElementById('file-upload-input')?.click()}
          >
            <input
              id="file-upload-input"
              type="file"
              className="hidden"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileInput}
            />

            {file ? (
              <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
                {previewUrl ? (
                  <div className="relative group">
                    <img
                      src={previewUrl}
                      alt="Uploaded preview"
                      className="w-28 h-28 object-cover rounded-md border border-emerald-500/50 shadow-md"
                    />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-md flex items-center justify-center text-white text-[11px] font-semibold">
                      <Eye size={14} className="mr-1" /> Preview
                    </div>
                  </div>
                ) : (
                  <div className="w-24 h-24 rounded-md bg-ink-panel border border-ink-border flex flex-col items-center justify-center text-brand">
                    <FileCode2 size={36} />
                    <span className="text-[10px] font-mono uppercase font-bold text-gray-400 mt-1">PDF Doc</span>
                  </div>
                )}

                <div className="text-left space-y-1.5">
                  <div className="flex items-center gap-2">
                    <FileCheck size={18} className="text-emerald-400" />
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                      Exhibit Staged for Intake
                    </span>
                  </div>
                  <p className="text-sm font-bold text-white max-w-sm truncate">{file.name}</p>
                  <p className="text-xs text-gray-400 font-mono">
                    {(file.size / 1024 / 1024).toFixed(2)} MB • {file.name.split('.').pop()?.toUpperCase()} Document
                  </p>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      document.getElementById('file-upload-input')?.click();
                    }}
                    className="text-[11px] text-brand hover:underline font-semibold block pt-1"
                  >
                    Replace with another file
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="w-14 h-14 rounded-full bg-brand/10 border border-brand/30 flex items-center justify-center mx-auto text-brand">
                  <Upload size={24} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-200">
                    Drag and drop your document exhibit here, or <span className="text-brand underline">browse files</span>
                  </p>
                  <p className="text-xs text-gray-400 mt-1 max-w-md mx-auto">
                    Accepts contracts, identity documents, bank statements, certificates, receipts, and invoices.
                  </p>
                </div>
                <div className="flex items-center justify-center gap-4 text-[11px] font-mono text-gray-400 pt-2">
                  <span>PDF (multi-page)</span>
                  <span>•</span>
                  <span>PNG</span>
                  <span>•</span>
                  <span>JPG / JPEG</span>
                  <span>•</span>
                  <span>Max {MAX_FILE_SIZE_MB}MB</span>
                </div>
              </div>
            )}
          </div>

          {/* Client Error Notice */}
          {clientError && (
            <div className="p-3 bg-red-950/30 border border-red-800/60 rounded-md text-xs text-red-300 flex items-center gap-2">
              <AlertTriangle size={16} className="text-red-400 shrink-0" />
              <span>{clientError}</span>
            </div>
          )}

          {/* Bottom Actions */}
          <div className="flex justify-between items-center pt-2 border-t border-ink-border">
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 text-xs font-semibold text-gray-400 hover:text-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={() => setStep(2)}
              disabled={!file}
              className="px-5 py-2 bg-brand hover:bg-brand-hover disabled:opacity-40 disabled:hover:bg-brand text-white rounded-md text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
            >
              Next: Case Details <ArrowRight size={14} />
            </button>
          </div>
        </Card>
      )}

      {/* STEP 2: Enter Case Details */}
      {step === 2 && (
        <Card variant="evidence" className="p-6 space-y-6">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck size={18} className="text-brand" /> Case Metadata & Examiner Notes
            </h2>
            <p className="text-xs text-gray-400">
              Record case classification details to establish chain-of-custody documentation and report indexing.
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Case Title / Exhibit Reference
              </label>
              <input
                type="text"
                value={caseTitle}
                onChange={(e) => setCaseTitle(e.target.value)}
                placeholder="e.g. Investigation-2026-004 / Employment Verification"
                className="w-full px-3 py-2 bg-ink-base border border-ink-border rounded-md text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand font-sans"
              />
              {/* Quick Presets */}
              <div className="flex flex-wrap items-center gap-1.5 mt-2">
                <span className="text-[11px] text-gray-400 flex items-center gap-1 mr-1">
                  <Sparkles size={11} className="text-brand" /> Presets:
                </span>
                {CASE_PRESETS.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setCaseTitle(preset)}
                    className="text-[10px] bg-ink-panel hover:bg-ink-hover border border-ink-border px-2 py-0.5 rounded text-gray-300 transition-colors"
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Investigation Priority
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setPriority('routine')}
                  className={`py-2.5 px-3 rounded-md border text-xs font-semibold text-left transition-all ${
                    priority === 'routine'
                      ? 'border-brand bg-brand/10 text-brand shadow-sm'
                      : 'border-ink-border bg-ink-base text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <div className="font-bold">Standard Examination</div>
                  <div className="text-[10px] text-gray-400 mt-0.5 font-normal">Normal caseload triage</div>
                </button>
                <button
                  type="button"
                  onClick={() => setPriority('urgent')}
                  className={`py-2.5 px-3 rounded-md border text-xs font-semibold text-left transition-all ${
                    priority === 'urgent'
                      ? 'border-amber-500 bg-amber-950/30 text-amber-300 shadow-sm'
                      : 'border-ink-border bg-ink-base text-gray-400 hover:text-gray-200'
                  }`}
                >
                  <div className="font-bold">Urgent Priority</div>
                  <div className="text-[10px] text-amber-400/70 mt-0.5 font-normal">High priority forensic inspection</div>
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Examiner Notes & Suspicion Rationale (Optional)
              </label>
              <textarea
                value={caseNotes}
                onChange={(e) => setCaseNotes(e.target.value)}
                rows={3}
                placeholder="State specific concerns if any: e.g. modified numbers, questionable signature stamp, mismatched typography, inconsistent font sizing..."
                className="w-full px-3 py-2 bg-ink-base border border-ink-border rounded-md text-xs text-white placeholder-gray-500 focus:outline-none focus:border-brand font-sans resize-none"
              />
            </div>
          </div>

          {/* Document Summary Strip */}
          {file && (
            <div className="p-3 bg-ink-base rounded-md border border-ink-border flex items-center justify-between text-xs">
              <div className="flex items-center gap-3 text-gray-300">
                <div className="w-8 h-8 rounded bg-brand/10 border border-brand/30 flex items-center justify-center text-brand">
                  <FileText size={16} />
                </div>
                <div>
                  <span className="font-semibold text-white">{file.name}</span>
                  <div className="text-gray-400 font-mono text-[11px]">
                    {(file.size / 1024 / 1024).toFixed(2)} MB • {file.name.split('.').pop()?.toUpperCase()}
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setStep(1)}
                className="text-[11px] text-brand hover:underline font-semibold"
              >
                Change Document
              </button>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between items-center pt-2 border-t border-ink-border">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 text-xs font-semibold text-gray-400 hover:text-gray-200 transition-colors flex items-center gap-1.5"
            >
              <ArrowLeft size={14} /> Back
            </button>
            <button
              onClick={startAnalysis}
              className="px-6 py-2.5 bg-brand hover:bg-brand-hover text-white rounded-md text-xs font-bold transition-all flex items-center gap-2 shadow-md shadow-brand/20"
            >
              <Search size={14} /> Start Forensic Analysis
            </button>
          </div>
        </Card>
      )}

      {/* STEP 3: Analysis Execution Progress */}
      {step === 3 && (
        <Card variant="evidence" className="p-8 text-center space-y-6">
          {!apiError ? (
            <div className="space-y-6 max-w-lg mx-auto">
              <div className="relative w-20 h-20 mx-auto">
                <Loader2 size={80} className="text-brand animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center font-mono text-sm font-bold text-white">
                  {uploadProgress}%
                </div>
              </div>

              <div className="space-y-1">
                <h3 className="text-lg font-bold text-white tracking-tight">
                  Forensic Examination in Progress
                </h3>
                <p className="text-xs text-brand font-mono">
                  {stages[activeStageIndex]?.label || 'Processing exhibit...'}
                </p>
                <p className="text-[11px] text-gray-400">
                  {stages[activeStageIndex]?.desc}
                </p>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2.5 bg-ink-base rounded-full overflow-hidden border border-ink-border">
                <div
                  className="h-full bg-gradient-to-r from-brand to-cyan-400 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>

              {/* Forensic Execution Stages List */}
              <div className="bg-ink-base/80 border border-ink-border rounded-md p-3 text-left space-y-2">
                <span className="text-[10px] font-mono uppercase tracking-wider text-gray-400 block pb-1 border-b border-ink-border">
                  Execution Stages Checklist
                </span>
                {stages.map((stg, idx) => {
                  const isCurrent = activeStageIndex === idx;
                  const isComplete = activeStageIndex > idx || uploadProgress >= 100;
                  return (
                    <div key={stg.label} className="flex items-center gap-2.5 text-xs">
                      {isComplete ? (
                        <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
                      ) : isCurrent ? (
                        <Loader2 size={14} className="text-brand animate-spin shrink-0" />
                      ) : (
                        <div className="w-3.5 h-3.5 rounded-full border border-ink-border shrink-0" />
                      )}
                      <span className={isComplete ? 'text-gray-300 line-through opacity-75' : isCurrent ? 'text-white font-bold' : 'text-gray-500'}>
                        {stg.label}
                      </span>
                    </div>
                  );
                })}
              </div>

              <div className="text-[11px] text-gray-400 pt-1">
                Exhibit is retained in isolated storage with immutable SHA-256 custody digest.
              </div>
            </div>
          ) : (
            <div className="space-y-4 max-w-md mx-auto">
              <div className="w-14 h-14 bg-red-950/40 border border-red-800 rounded-md flex items-center justify-center mx-auto text-red-400">
                <AlertTriangle size={28} />
              </div>
              <h3 className="text-base font-bold text-white">Forensic Analysis Interrupted</h3>
              <p className="text-xs text-red-300 bg-red-950/20 border border-red-800/40 p-3 rounded-md leading-relaxed text-left font-mono">
                {apiError}
              </p>
              <div className="flex justify-center gap-3 pt-2">
                <button
                  onClick={() => setStep(1)}
                  className="px-4 py-2 bg-ink-panel hover:bg-ink-hover border border-ink-border text-gray-300 rounded-md text-xs font-semibold"
                >
                  Choose Different Exhibit
                </button>
                <button
                  onClick={startAnalysis}
                  className="px-4 py-2 bg-brand hover:bg-brand-hover text-white rounded-md text-xs font-semibold"
                >
                  Retry Analysis
                </button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}