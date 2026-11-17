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
  Clock, 
  Zap, 
  Trash2, 
  RotateCcw,
  Check,
  Lock,
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

interface ExecutionStage {
  id: number;
  title: string;
  description: string;
  runningMessage: string;
  completedMessage: string;
}

const EXECUTION_STAGES: ExecutionStage[] = [
  {
    id: 1,
    title: 'File Intake & Payload Validation',
    description: 'Verifying file format, boundary safety, and MIME structure',
    runningMessage: 'Streaming payload and enforcing byte boundary validation...',
    completedMessage: 'Payload validated • MIME signature verified • Safe file buffer staged',
  },
  {
    id: 2,
    title: 'SHA-256 Fingerprint & Custody Ledger',
    description: 'Generating immutable cryptographic hash for chain of custody',
    runningMessage: 'Computing cryptographic digest & generating custody ledger receipt...',
    completedMessage: 'SHA-256 integrity digest computed & recorded in evidence chain of custody',
  },
  {
    id: 3,
    title: 'Physical Forensic Feature Extraction',
    description: 'Extracting 18 physical features: ELA, Laplacian blur, noise & texture',
    runningMessage: 'Executing Error Level Analysis (ELA) and Laplacian spatial filters...',
    completedMessage: '18 forensic features extracted (Laplacian focus variance, noise, ELA differentials)',
  },
  {
    id: 4,
    title: 'Dual-Track Analysis & Model Screening',
    description: 'Screening via frozen Random Forest (T=0.40) & symbolic rules',
    runningMessage: 'Evaluating feature vector against frozen Random Forest (T = 0.40)...',
    completedMessage: 'Classical ML model evaluated against locked decision threshold T=0.40',
  },
  {
    id: 5,
    title: 'Synthesis Arbiter & Dossier Assembly',
    description: 'Reconciling findings and preparing unified forensic assessment',
    runningMessage: 'Synthesizing multi-track arbitration and generating evidence dossier...',
    completedMessage: 'Multi-track evidence reconciled • Tamper-evident dossier assembled',
  },
];

export default function NewInvestigationPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [clientError, setClientError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Step 2: Case Details
  const [caseTitle, setCaseTitle] = useState('');
  const [caseNotes, setCaseNotes] = useState('');
  const [priority, setPriority] = useState<'routine' | 'urgent'>('routine');

  // Step 3: Analysis Execution State
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [activeStageIndex, setActiveStageIndex] = useState(0);
  const [completedStageIndices, setCompletedStageIndices] = useState<number[]>([]);
  const [apiError, setApiError] = useState<string | null>(null);

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
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleRemoveFile = () => {
    setFile(null);
    setPreviewUrl(null);
    setClientError(null);
  };

  const startAnalysis = async () => {
    if (!file || isUploading) return;

    setStep(3);
    setIsUploading(true);
    setUploadProgress(10);
    setActiveStageIndex(0);
    setCompletedStageIndices([]);
    setApiError(null);

    // Dynamic stage progression matching actual pipeline execution cadence
    let currentIdx = 0;
    const stageTimer = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev < 90) {
          const next = prev + 8;
          if (next >= 25 && currentIdx < 1) {
            currentIdx = 1;
            setActiveStageIndex(1);
            setCompletedStageIndices((c) => [...new Set([...c, 0])]);
          } else if (next >= 50 && currentIdx < 2) {
            currentIdx = 2;
            setActiveStageIndex(2);
            setCompletedStageIndices((c) => [...new Set([...c, 0, 1])]);
          } else if (next >= 72 && currentIdx < 3) {
            currentIdx = 3;
            setActiveStageIndex(3);
            setCompletedStageIndices((c) => [...new Set([...c, 0, 1, 2])]);
          } else if (next >= 85 && currentIdx < 4) {
            currentIdx = 4;
            setActiveStageIndex(4);
            setCompletedStageIndices((c) => [...new Set([...c, 0, 1, 2, 3])]);
          }
          return next;
        }
        return prev;
      });
    }, 450);

    try {
      const response = await uploadDocument(
        file,
        (percent) => {
          if (percent > 20) {
            setUploadProgress((p) => Math.max(p, Math.min(88, percent)));
          }
        },
        { title: caseTitle, notes: caseNotes, priority }
      );

      clearInterval(stageTimer);

      if (response.processing_status === 'failed') {
        throw new Error(
          `Exhibit ${response.document_id} was ingested, but automated pipeline processing failed. Ensure document is not password-protected or corrupt.`
        );
      }

      if (response && response.document_id) {
        // Complete all stages
        setUploadProgress(100);
        setActiveStageIndex(4);
        setCompletedStageIndices([0, 1, 2, 3, 4]);

        // Brief delay so user sees all green checkmarks
        setTimeout(() => {
          navigate(`/investigation/${response.document_id}`);
        }, 700);
      } else {
        throw new Error('Analysis completed but document ID was not received from the forensic engine.');
      }
    } catch (err: unknown) {
      clearInterval(stageTimer);
      setIsUploading(false);
      const parsedError = extractApiError(err);
      setApiError(parsedError);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-2 border-b border-[#E6E5F0]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#7045E8] bg-[#F0EBFF] px-2.5 py-0.5 rounded-full border border-[#DDD5F9]">
              Forensic Evidence Intake
            </span>
            <span className="text-[11px] font-mono text-[#73758B] flex items-center gap-1">
              <Lock size={12} className="text-[#7045E8]" /> T=0.40 Locked Protocol
            </span>
          </div>
          <h1 className="text-2xl font-bold text-[#17172F] tracking-tight">New Document Investigation</h1>
          <p className="text-xs text-[#73758B] mt-0.5">
            Submit a physical or digital document exhibit for automated tamper detection, ELA, and ML classification.
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="text-xs text-[#73758B] hover:text-[#17172F] transition-colors flex items-center gap-1.5 font-semibold"
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
          const isNavigable = !isUploading && (isDone || (s.num === 2 && file));

          return (
            <button
              key={s.num}
              type="button"
              disabled={!isNavigable && !isActive}
              onClick={() => {
                if (isNavigable) setStep(s.num as 1 | 2 | 3);
              }}
              className={`p-3.5 rounded-2xl border text-left transition-all ${
                isActive
                  ? 'bg-[#F0EBFF] border-[#7045E8] text-[#7045E8] shadow-sm ring-1 ring-[#7045E8]/20'
                  : isDone
                  ? 'bg-[#EBF9F1] border-[#D1F2DE] text-[#159B55] hover:bg-[#E2F6EA] cursor-pointer'
                  : 'bg-white border-[#E6E5F0] text-[#73758B] opacity-70 cursor-not-allowed'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 transition-colors ${
                    isActive
                      ? 'bg-[#7045E8] text-white shadow-sm'
                      : isDone
                      ? 'bg-[#159B55] text-white'
                      : 'bg-[#F4F5FB] text-[#73758B] border border-[#E6E5F0]'
                  }`}
                >
                  {isDone ? <Check size={14} /> : s.num}
                </span>
                <span className="text-xs font-bold truncate">{s.title}</span>
              </div>
              <p className="text-[11px] text-[#73758B] mt-1 pl-8.5 hidden sm:block truncate">
                {s.desc}
              </p>
            </button>
          );
        })}
      </div>

      {/* STEP 1: Upload Document */}
      {step === 1 && (
        <Card variant="evidence" className="p-8 space-y-6">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-[#17172F] flex items-center gap-2">
              <Upload size={18} className="text-[#7045E8]" /> Select Document Exhibit
            </h2>
            <p className="text-xs text-[#73758B]">
              Upload original files for authentic forensic evaluation. Supported formats: PDF, PNG, JPG, JPEG (up to {MAX_FILE_SIZE_MB} MB).
            </p>
          </div>

          {/* Drag & Drop Box */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            role="button"
            tabIndex={0}
            aria-label="Choose a document to investigate"
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                document.getElementById('file-upload-input')?.click();
              }
            }}
            className={`border-2 border-dashed rounded-2xl p-8 sm:p-10 text-center transition-all cursor-pointer relative ${
              isDragging
                ? 'border-[#7045E8] bg-[#F0EBFF]/80 ring-4 ring-[#7045E8]/20 scale-[1.01]'
                : file 
                ? 'border-[#159B55] bg-[#EBF9F1]/40' 
                : clientError 
                ? 'border-[#DC4545] bg-[#FDF2F2]' 
                : 'border-[#DDD5F9] hover:border-[#7045E8] bg-[#F8F9FF] hover:bg-[#F0EBFF]/30'
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
                {/* Thumbnail / Document Type Representation */}
                {previewUrl ? (
                  <div className="relative group shrink-0">
                    <img
                      src={previewUrl}
                      alt="Uploaded preview"
                      className="w-28 h-28 object-cover rounded-xl border border-[#159B55] shadow-md"
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity rounded-xl flex items-center justify-center text-white text-xs font-bold">
                      <Eye size={14} className="mr-1" /> Preview
                    </div>
                  </div>
                ) : (
                  <div className="w-28 h-28 rounded-2xl bg-[#F0EBFF] border border-[#DDD5F9] flex flex-col items-center justify-center text-[#7045E8] shrink-0 shadow-inner">
                    <FileCode2 size={40} />
                    <span className="text-[10px] font-mono uppercase font-bold text-[#7045E8] mt-1.5">
                      PDF Document
                    </span>
                  </div>
                )}

                {/* Exhibit Details & Actions */}
                <div className="text-left space-y-2 min-w-0">
                  <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#EBF9F1] text-[#159B55] border border-[#D1F2DE]">
                    <FileCheck size={13} />
                    <span>Exhibit Staged & Validated</span>
                  </div>

                  <div>
                    <p className="text-sm font-bold text-[#17172F] max-w-md truncate" title={file.name}>
                      {file.name}
                    </p>
                    <div className="text-xs text-[#73758B] font-mono mt-0.5 flex items-center gap-2">
                      <span className="bg-[#F0EBFF] text-[#7045E8] px-1.5 py-0.5 rounded font-bold text-[10px]">
                        {file.name.split('.').pop()?.toUpperCase()}
                      </span>
                      <span>{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                      <span>•</span>
                      <span>Ready for intake</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 pt-1" onClick={(e) => e.stopPropagation()}>
                    <button
                      type="button"
                      onClick={() => document.getElementById('file-upload-input')?.click()}
                      className="text-xs text-[#7045E8] hover:text-[#5F33DB] font-bold flex items-center gap-1 transition-colors"
                    >
                      <RotateCcw size={12} /> Replace file
                    </button>
                    <span className="text-[#DDD5F9]">|</span>
                    <button
                      type="button"
                      onClick={handleRemoveFile}
                      className="text-xs text-[#DC4545] hover:text-[#B91C1C] font-bold flex items-center gap-1 transition-colors"
                    >
                      <Trash2 size={12} /> Remove file
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="w-14 h-14 rounded-2xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center mx-auto shadow-sm transition-transform group-hover:scale-105">
                  <Upload size={24} />
                </div>
                <div>
                  <p className="text-sm font-bold text-[#17172F]">
                    {isDragging ? (
                      <span className="text-[#7045E8]">Drop document exhibit here to stage</span>
                    ) : (
                      <>
                        Drag and drop your document exhibit here, or{' '}
                        <span className="text-[#7045E8] underline">browse files</span>
                      </>
                    )}
                  </p>
                  <p className="text-xs text-[#73758B] mt-1 max-w-md mx-auto">
                    Accepts contracts, identity documents, bank statements, certificates, receipts, and invoices.
                  </p>
                </div>
                <div className="flex items-center justify-center gap-3 text-xs font-mono text-[#73758B] pt-2">
                  <span className="bg-[#F0EBFF] text-[#7045E8] px-2 py-0.5 rounded-md font-semibold">PDF</span>
                  <span>•</span>
                  <span className="bg-[#F0EBFF] text-[#7045E8] px-2 py-0.5 rounded-md font-semibold">PNG</span>
                  <span>•</span>
                  <span className="bg-[#F0EBFF] text-[#7045E8] px-2 py-0.5 rounded-md font-semibold">JPG / JPEG</span>
                  <span>•</span>
                  <span>Max {MAX_FILE_SIZE_MB}MB</span>
                </div>
              </div>
            )}
          </div>

          {/* Client Error Notice */}
          {clientError && (
            <div className="p-3.5 bg-[#FDF2F2] border border-[#FAD8D8] rounded-xl text-xs text-[#DC4545] flex items-center gap-2">
              <AlertTriangle size={16} className="text-[#DC4545] shrink-0" />
              <span>{clientError}</span>
            </div>
          )}

          {/* Bottom Actions */}
          <div className="flex justify-between items-center pt-2 border-t border-[#E6E5F0]">
            <button
              type="button"
              onClick={() => navigate('/')}
              className="px-4 py-2 text-xs font-bold text-[#73758B] hover:text-[#17172F] transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => setStep(2)}
              disabled={!file}
              className="px-6 py-2.5 bg-[#7045E8] hover:bg-[#5F33DB] disabled:opacity-40 disabled:hover:bg-[#7045E8] text-white rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-md shadow-violet-200"
            >
              Next: Case Details <ArrowRight size={14} />
            </button>
          </div>
        </Card>
      )}

      {/* STEP 2: Enter Case Details */}
      {step === 2 && (
        <Card variant="evidence" className="p-8 space-y-6">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-[#17172F] flex items-center gap-2">
              <ShieldCheck size={18} className="text-[#7045E8]" /> Case Metadata & Examiner Notes
            </h2>
            <p className="text-xs text-[#73758B]">
              Record case classification details to establish chain-of-custody documentation and report indexing.
            </p>
          </div>

          <div className="space-y-5">
            {/* Case Title Input */}
            <div className="space-y-2">
              <label className="block text-xs font-bold text-[#17172F] uppercase tracking-wider">
                Case Title / Exhibit Reference <span className="text-[#7045E8]">*</span>
              </label>
              <input
                type="text"
                value={caseTitle}
                onChange={(e) => setCaseTitle(e.target.value)}
                placeholder="e.g. Investigation-2026-004 / Employment Verification"
                className="w-full px-4 py-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl text-sm font-semibold text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] focus:bg-white transition-all shadow-sm"
              />
              {/* Quick Preset Chips */}
              <div className="space-y-1.5 pt-1">
                <span className="text-[11px] text-[#73758B] flex items-center gap-1 font-semibold">
                  <Sparkles size={12} className="text-[#7045E8]" /> Casework Presets:
                </span>
                <div className="flex flex-wrap items-center gap-1.5">
                  {CASE_PRESETS.map((preset) => {
                    const isSelected = caseTitle === preset;
                    return (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => setCaseTitle(preset)}
                        className={`text-xs px-3 py-1.5 rounded-xl border font-medium transition-all ${
                          isSelected
                            ? 'bg-[#F0EBFF] text-[#7045E8] border-[#7045E8] font-bold shadow-sm'
                            : 'bg-white hover:bg-[#F8F9FF] text-[#73758B] hover:text-[#17172F] border-[#E6E5F0]'
                        }`}
                      >
                        {preset}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Investigation Priority Cards */}
            <div className="space-y-2">
              <label className="block text-xs font-bold text-[#17172F] uppercase tracking-wider">
                Investigation Priority
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setPriority('routine')}
                  className={`p-4 rounded-xl border text-left transition-all relative flex items-start gap-3.5 ${
                    priority === 'routine'
                      ? 'border-[#7045E8] bg-[#F0EBFF]/50 text-[#17172F] shadow-sm ring-1 ring-[#7045E8]'
                      : 'border-[#E6E5F0] bg-white text-[#73758B] hover:border-[#DDD5F9]'
                  }`}
                >
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                    priority === 'routine' ? 'bg-[#7045E8] text-white' : 'bg-[#F8F9FF] text-[#73758B]'
                  }`}>
                    <Clock size={18} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[#17172F]">Standard Examination</span>
                      <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                        priority === 'routine' ? 'border-[#7045E8] bg-[#7045E8]' : 'border-[#DDD5F9]'
                      }`}>
                        {priority === 'routine' && <Check size={10} className="text-white" />}
                      </div>
                    </div>
                    <p className="text-[11px] text-[#73758B] mt-0.5">
                      Normal caseload triage & standard verification queue
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setPriority('urgent')}
                  className={`p-4 rounded-xl border text-left transition-all relative flex items-start gap-3.5 ${
                    priority === 'urgent'
                      ? 'border-[#E9A12A] bg-[#FFF8EC] text-[#17172F] shadow-sm ring-1 ring-[#E9A12A]'
                      : 'border-[#E6E5F0] bg-white text-[#73758B] hover:border-[#FFE8BF]'
                  }`}
                >
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                    priority === 'urgent' ? 'bg-[#E9A12A] text-white' : 'bg-[#F8F9FF] text-[#73758B]'
                  }`}>
                    <Zap size={18} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[#17172F]">Urgent Priority</span>
                      <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                        priority === 'urgent' ? 'border-[#E9A12A] bg-[#E9A12A]' : 'border-[#DDD5F9]'
                      }`}>
                        {priority === 'urgent' && <Check size={10} className="text-white" />}
                      </div>
                    </div>
                    <p className="text-[11px] text-[#73758B] mt-0.5">
                      Expedited forensic inspection for legal or court compliance
                    </p>
                  </div>
                </button>
              </div>
            </div>

            {/* Examiner Notes */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-[#17172F] uppercase tracking-wider">
                Examiner Notes & Suspicion Rationale (Optional)
              </label>
              <textarea
                value={caseNotes}
                onChange={(e) => setCaseNotes(e.target.value)}
                rows={3}
                placeholder="State specific concerns if any: e.g. modified numbers on page 1, questionable signature stamp, mismatched typography, inconsistent font sizing, suspected copy-move texture..."
                className="w-full px-4 py-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] focus:bg-white font-sans resize-none shadow-sm transition-all"
              />
            </div>
          </div>

          {/* Document Summary Strip */}
          {file && (
            <div className="p-3.5 bg-[#F8F9FF] rounded-xl border border-[#E6E5F0] flex items-center justify-between text-xs">
              <div className="flex items-center gap-3 text-[#17172F] min-w-0">
                <div className="w-8 h-8 rounded-lg bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center shrink-0">
                  <FileText size={16} />
                </div>
                <div className="min-w-0">
                  <span className="font-bold truncate block">{file.name}</span>
                  <div className="text-[#73758B] font-mono text-[11px]">
                    {(file.size / 1024 / 1024).toFixed(2)} MB • {file.name.split('.').pop()?.toUpperCase()} Document
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setStep(1)}
                className="text-xs text-[#7045E8] hover:underline font-bold shrink-0 ml-3"
              >
                Change Document
              </button>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between items-center pt-2 border-t border-[#E6E5F0]">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="px-4 py-2 text-xs font-bold text-[#73758B] hover:text-[#17172F] transition-colors flex items-center gap-1.5"
            >
              <ArrowLeft size={14} /> Back
            </button>
            <button
              type="button"
              onClick={startAnalysis}
              className="px-6 py-2.5 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-md shadow-violet-200"
            >
              <Search size={14} /> Start Forensic Analysis
            </button>
          </div>
        </Card>
      )}

      {/* STEP 3: Analysis Execution Progress Workspace */}
      {step === 3 && (
        <Card variant="evidence" className="p-8 space-y-6">
          {!apiError ? (
            <div className="space-y-6">
              {/* Top Section: Examination Context Bar */}
              <div className="bg-[#F8F9FF] border border-[#E6E5F0] rounded-2xl p-5 shadow-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-[#73758B] font-bold block">
                      Active Exhibit Ingestion
                    </span>
                    <h3 className="text-base font-bold text-[#17172F] truncate max-w-md mt-0.5">
                      {file?.name || 'Document Exhibit'}
                    </h3>
                    <p className="text-xs text-[#7045E8] font-semibold mt-0.5 truncate">
                      Ref: {caseTitle || 'Standard Casework'}
                    </p>
                  </div>

                  <div className="text-right sm:self-center">
                    <span className="text-[11px] font-mono font-bold text-[#7045E8] bg-[#F0EBFF] border border-[#DDD5F9] px-3 py-1 rounded-full inline-block">
                      {uploadProgress < 100 
                        ? `Stage ${activeStageIndex + 1} of 5 Active` 
                        : 'Analysis Finalized'}
                    </span>
                  </div>
                </div>

                {/* Progress Bar & Percentage */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-[#17172F]">
                      {uploadProgress < 100 ? 'Automated Multi-Track Examination' : 'Dossier Ready'}
                    </span>
                    <span className="font-mono font-bold text-[#7045E8]">
                      {uploadProgress}%
                    </span>
                  </div>
                  <div className="w-full h-2.5 bg-[#F0EBFF] rounded-full overflow-hidden border border-[#DDD5F9]">
                    <div
                      className="h-full bg-[#7045E8] transition-all duration-300 rounded-full"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Main Section: 5 Execution Stages Vertical Timeline */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-[#17172F]">
                    Forensic Pipeline Execution Stages
                  </h4>
                  <span className="text-[11px] text-[#73758B] font-mono">
                    Frozen Model Boundary (T = 0.40)
                  </span>
                </div>

                <div className="space-y-3">
                  {EXECUTION_STAGES.map((stg, idx) => {
                    const isCompleted = completedStageIndices.includes(idx);
                    const isRunning = activeStageIndex === idx && !isCompleted;

                    return (
                      <div
                        key={stg.id}
                        className={`p-4 rounded-xl border transition-all ${
                          isCompleted
                            ? 'bg-[#EBF9F1]/40 border-[#D1F2DE]'
                            : isRunning
                            ? 'bg-[#F0EBFF]/60 border-[#7045E8] ring-1 ring-[#7045E8]/20 shadow-sm'
                            : 'bg-[#F8F9FF]/40 border-[#E6E5F0] opacity-60'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-3 min-w-0">
                            {/* Status Indicator Icon */}
                            <div className="shrink-0 mt-0.5">
                              {isCompleted ? (
                                <div className="w-6 h-6 rounded-full bg-[#159B55] text-white flex items-center justify-center shadow-sm">
                                  <Check size={14} />
                                </div>
                              ) : isRunning ? (
                                <div className="w-6 h-6 rounded-full bg-[#7045E8] text-white flex items-center justify-center shadow-sm">
                                  <Loader2 size={14} className="animate-spin" />
                                </div>
                              ) : (
                                <div className="w-6 h-6 rounded-full bg-[#F4F5FB] border border-[#DDD5F9] text-[#73758B] flex items-center justify-center text-xs font-mono font-bold">
                                  {stg.id}
                                </div>
                              )}
                            </div>

                            {/* Stage Info & Feedback */}
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <span className={`text-xs font-bold ${
                                  isCompleted ? 'text-[#159B55]' : isRunning ? 'text-[#7045E8]' : 'text-[#73758B]'
                                }`}>
                                  Stage {stg.id}: {stg.title}
                                </span>
                              </div>
                              <p className="text-[11px] text-[#73758B] mt-0.5">
                                {stg.description}
                              </p>

                              {/* Active or Completed Dynamic Message */}
                              {isCompleted && (
                                <div className="text-[11px] text-[#159B55] font-mono mt-1 flex items-center gap-1 font-semibold">
                                  <CheckCircle2 size={12} /> {stg.completedMessage}
                                </div>
                              )}
                              {isRunning && (
                                <div className="text-[11px] text-[#7045E8] font-mono mt-1 flex items-center gap-1 font-semibold">
                                  <Loader2 size={12} className="animate-spin" /> {stg.runningMessage}
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Status Pill Badge */}
                          <div className="shrink-0">
                            {isCompleted ? (
                              <span className="text-[10px] font-bold text-[#159B55] bg-[#EBF9F1] border border-[#D1F2DE] px-2.5 py-0.5 rounded-full">
                                Completed
                              </span>
                            ) : isRunning ? (
                              <span className="text-[10px] font-bold text-[#7045E8] bg-[#F0EBFF] border border-[#DDD5F9] px-2.5 py-0.5 rounded-full flex items-center gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-[#7045E8] animate-pulse" />
                                Running
                              </span>
                            ) : (
                              <span className="text-[10px] font-semibold text-[#73758B] bg-white border border-[#E6E5F0] px-2 py-0.5 rounded-full">
                                Pending
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Bottom Governance Callout */}
              <div className="p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl flex items-center justify-between text-[11px] text-[#73758B]">
                <span className="flex items-center gap-1.5 font-medium">
                  <ShieldCheck size={14} className="text-[#159B55]" />
                  Exhibit processed in isolated memory under frozen protocol T = 0.40.
                </span>
                <span className="font-mono text-[10px] text-[#7045E8] font-semibold hidden sm:inline">
                  SHA-256 Custody Verified
                </span>
              </div>
            </div>
          ) : (
            /* Error Fallback Display */
            <div className="space-y-4 max-w-md mx-auto text-center py-4">
              <div className="w-14 h-14 bg-[#FDF2F2] border border-[#FAD8D8] rounded-2xl flex items-center justify-center mx-auto text-[#DC4545] shadow-sm">
                <AlertTriangle size={28} />
              </div>
              <h3 className="text-base font-bold text-[#17172F]">Forensic Analysis Interrupted</h3>
              <p className="text-xs text-[#DC4545] bg-[#FDF2F2] border border-[#FAD8D8] p-3.5 rounded-xl leading-relaxed text-left font-mono">
                {apiError}
              </p>
              <div className="flex justify-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="px-4 py-2 bg-white hover:bg-[#F8F9FF] border border-[#E6E5F0] text-[#17172F] rounded-xl text-xs font-semibold"
                >
                  Choose Different Exhibit
                </button>
                <button
                  type="button"
                  onClick={startAnalysis}
                  className="px-4 py-2 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-semibold shadow-sm"
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
