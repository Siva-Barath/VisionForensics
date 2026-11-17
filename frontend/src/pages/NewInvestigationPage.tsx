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
        }, 650);
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
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-2 border-b border-[#E6E5F0]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#7045E8] bg-[#F0EBFF] px-2.5 py-0.5 rounded-full border border-[#DDD5F9]">
              Forensic Evidence Intake
            </span>
            <span className="text-[11px] font-mono text-[#73758B]">T=0.40 Locked Protocol</span>
          </div>
          <h1 className="text-2xl font-bold text-[#17172F] tracking-tight">New Document Investigation</h1>
          <p className="text-xs text-[#73758B] mt-0.5">
            Submit a physical or digital document exhibit for automated tamper detection, ELA, and ML classification.
          </p>
        </div>
        <button
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
          return (
            <div
              key={s.num}
              className={`p-3.5 rounded-2xl border transition-all ${
                isActive
                  ? 'bg-[#F0EBFF] border-[#7045E8] text-[#7045E8] shadow-sm'
                  : isDone
                  ? 'bg-[#EBF9F1] border-[#D1F2DE] text-[#159B55]'
                  : 'bg-white border-[#E6E5F0] text-[#73758B]'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <span
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    isActive
                      ? 'bg-[#7045E8] text-white'
                      : isDone
                      ? 'bg-[#159B55] text-white'
                      : 'bg-[#F4F5FB] text-[#73758B]'
                  }`}
                >
                  {isDone ? '✓' : s.num}
                </span>
                <span className="text-xs font-bold">{s.title}</span>
              </div>
              <p className="text-[11px] text-[#73758B] mt-1 pl-8 hidden sm:block">{s.desc}</p>
            </div>
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
            role="button"
            tabIndex={0}
            aria-label="Choose a document to investigate"
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                document.getElementById('file-upload-input')?.click();
              }
            }}
            className={`border-2 border-dashed rounded-2xl p-10 text-center transition-all cursor-pointer relative ${
              file 
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
                {previewUrl ? (
                  <div className="relative group">
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
                  <div className="w-24 h-24 rounded-2xl bg-[#F0EBFF] border border-[#DDD5F9] flex flex-col items-center justify-center text-[#7045E8]">
                    <FileCode2 size={36} />
                    <span className="text-[10px] font-mono uppercase font-bold text-[#7045E8] mt-1">PDF Doc</span>
                  </div>
                )}

                <div className="text-left space-y-1.5">
                  <div className="flex items-center gap-2">
                    <FileCheck size={18} className="text-[#159B55]" />
                    <span className="text-xs font-bold uppercase tracking-wider text-[#159B55]">
                      Exhibit Staged for Intake
                    </span>
                  </div>
                  <p className="text-sm font-bold text-[#17172F] max-w-sm truncate">{file.name}</p>
                  <p className="text-xs text-[#73758B] font-mono">
                    {(file.size / 1024 / 1024).toFixed(2)} MB • {file.name.split('.').pop()?.toUpperCase()} Document
                  </p>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      document.getElementById('file-upload-input')?.click();
                    }}
                    className="text-xs text-[#7045E8] hover:underline font-bold block pt-1"
                  >
                    Replace with another file
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="w-14 h-14 rounded-2xl bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center mx-auto shadow-sm">
                  <Upload size={24} />
                </div>
                <div>
                  <p className="text-sm font-bold text-[#17172F]">
                    Drag and drop your document exhibit here, or <span className="text-[#7045E8] underline">browse files</span>
                  </p>
                  <p className="text-xs text-[#73758B] mt-1 max-w-md mx-auto">
                    Accepts contracts, identity documents, bank statements, certificates, receipts, and invoices.
                  </p>
                </div>
                <div className="flex items-center justify-center gap-3 text-xs font-mono text-[#73758B] pt-2">
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
            <div className="p-3.5 bg-[#FDF2F2] border border-[#FAD8D8] rounded-xl text-xs text-[#DC4545] flex items-center gap-2">
              <AlertTriangle size={16} className="text-[#DC4545] shrink-0" />
              <span>{clientError}</span>
            </div>
          )}

          {/* Bottom Actions */}
          <div className="flex justify-between items-center pt-2 border-t border-[#E6E5F0]">
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 text-xs font-bold text-[#73758B] hover:text-[#17172F] transition-colors"
            >
              Cancel
            </button>
            <button
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

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-[#17172F] uppercase tracking-wider mb-1.5">
                Case Title / Exhibit Reference
              </label>
              <input
                type="text"
                value={caseTitle}
                onChange={(e) => setCaseTitle(e.target.value)}
                placeholder="e.g. Investigation-2026-004 / Employment Verification"
                className="w-full px-3.5 py-2.5 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl text-sm text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] font-sans shadow-sm"
              />
              {/* Quick Presets */}
              <div className="flex flex-wrap items-center gap-1.5 mt-2">
                <span className="text-[11px] text-[#73758B] flex items-center gap-1 mr-1 font-semibold">
                  <Sparkles size={11} className="text-[#7045E8]" /> Presets:
                </span>
                {CASE_PRESETS.map((preset) => (
                  <button
                    key={preset}
                    type="button"
                    onClick={() => setCaseTitle(preset)}
                    className="text-[11px] bg-[#F8F9FF] hover:bg-[#F0EBFF] hover:text-[#7045E8] border border-[#E6E5F0] px-2.5 py-0.5 rounded-lg text-[#73758B] font-medium transition-colors"
                  >
                    {preset}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#17172F] uppercase tracking-wider mb-1.5">
                Investigation Priority
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setPriority('routine')}
                  className={`py-3 px-4 rounded-xl border text-xs font-semibold text-left transition-all ${
                    priority === 'routine'
                      ? 'border-[#7045E8] bg-[#F0EBFF] text-[#7045E8] shadow-sm'
                      : 'border-[#E6E5F0] bg-white text-[#73758B] hover:text-[#17172F]'
                  }`}
                >
                  <div className="font-bold text-sm">Standard Examination</div>
                  <div className="text-[11px] text-[#73758B] mt-0.5 font-normal">Normal caseload triage</div>
                </button>
                <button
                  type="button"
                  onClick={() => setPriority('urgent')}
                  className={`py-3 px-4 rounded-xl border text-xs font-semibold text-left transition-all ${
                    priority === 'urgent'
                      ? 'border-[#E9A12A] bg-[#FFF8EC] text-[#E9A12A] shadow-sm'
                      : 'border-[#E6E5F0] bg-white text-[#73758B] hover:text-[#17172F]'
                  }`}
                >
                  <div className="font-bold text-sm">Urgent Priority</div>
                  <div className="text-[11px] text-[#73758B] mt-0.5 font-normal">High priority forensic inspection</div>
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#17172F] uppercase tracking-wider mb-1.5">
                Examiner Notes & Suspicion Rationale (Optional)
              </label>
              <textarea
                value={caseNotes}
                onChange={(e) => setCaseNotes(e.target.value)}
                rows={3}
                placeholder="State specific concerns if any: e.g. modified numbers, questionable signature stamp, mismatched typography, inconsistent font sizing..."
                className="w-full px-3.5 py-2.5 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl text-xs text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] font-sans resize-none shadow-sm"
              />
            </div>
          </div>

          {/* Document Summary Strip */}
          {file && (
            <div className="p-3.5 bg-[#F8F9FF] rounded-xl border border-[#E6E5F0] flex items-center justify-between text-xs">
              <div className="flex items-center gap-3 text-[#17172F]">
                <div className="w-8 h-8 rounded-lg bg-[#F0EBFF] text-[#7045E8] flex items-center justify-center">
                  <FileText size={16} />
                </div>
                <div>
                  <span className="font-bold">{file.name}</span>
                  <div className="text-[#73758B] font-mono text-[11px]">
                    {(file.size / 1024 / 1024).toFixed(2)} MB • {file.name.split('.').pop()?.toUpperCase()}
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setStep(1)}
                className="text-xs text-[#7045E8] hover:underline font-bold"
              >
                Change Document
              </button>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between items-center pt-2 border-t border-[#E6E5F0]">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 text-xs font-bold text-[#73758B] hover:text-[#17172F] transition-colors flex items-center gap-1.5"
            >
              <ArrowLeft size={14} /> Back
            </button>
            <button
              onClick={startAnalysis}
              className="px-6 py-2.5 bg-[#7045E8] hover:bg-[#5F33DB] text-white rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-md shadow-violet-200"
            >
              <Search size={14} /> Start Forensic Analysis
            </button>
          </div>
        </Card>
      )}

      {/* STEP 3: Analysis Execution Progress */}
      {step === 3 && (
        <Card variant="evidence" className="p-10 text-center space-y-6">
          {!apiError ? (
            <div className="space-y-6 max-w-lg mx-auto">
              <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
                <Loader2 size={96} className="text-[#7045E8] animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center font-mono text-base font-extrabold text-[#17172F]">
                  {uploadProgress}%
                </div>
              </div>

              <div className="space-y-1">
                <h3 className="text-xl font-bold text-[#17172F] tracking-tight">
                  Forensic Examination in Progress
                </h3>
                <p className="text-xs text-[#7045E8] font-mono font-bold">
                  {stages[activeStageIndex]?.label || 'Processing exhibit...'}
                </p>
                <p className="text-xs text-[#73758B]">
                  {stages[activeStageIndex]?.desc}
                </p>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2.5 bg-[#F0EBFF] rounded-full overflow-hidden border border-[#DDD5F9]">
                <div
                  className="h-full bg-[#7045E8] transition-all duration-300 rounded-full"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>

              {/* Forensic Execution Stages List */}
              <div className="bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl p-4 text-left space-y-2.5">
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#73758B] font-bold block pb-1 border-b border-[#E6E5F0]">
                  Execution Stages Checklist
                </span>
                {stages.map((stg, idx) => {
                  const isCurrent = activeStageIndex === idx;
                  const isComplete = activeStageIndex > idx || uploadProgress >= 100;
                  return (
                    <div key={stg.label} className="flex items-center gap-2.5 text-xs">
                      {isComplete ? (
                        <CheckCircle2 size={16} className="text-[#159B55] shrink-0" />
                      ) : isCurrent ? (
                        <Loader2 size={16} className="text-[#7045E8] animate-spin shrink-0" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-[#DDD5F9] shrink-0" />
                      )}
                      <span className={isComplete ? 'text-[#73758B] line-through' : isCurrent ? 'text-[#17172F] font-bold' : 'text-[#73758B]'}>
                        {stg.label}
                      </span>
                    </div>
                  );
                })}
              </div>

              <div className="text-xs text-[#73758B]">
                Exhibit is retained in isolated storage with immutable SHA-256 custody digest.
              </div>
            </div>
          ) : (
            <div className="space-y-4 max-w-md mx-auto">
              <div className="w-14 h-14 bg-[#FDF2F2] border border-[#FAD8D8] rounded-2xl flex items-center justify-center mx-auto text-[#DC4545]">
                <AlertTriangle size={28} />
              </div>
              <h3 className="text-base font-bold text-[#17172F]">Forensic Analysis Interrupted</h3>
              <p className="text-xs text-[#DC4545] bg-[#FDF2F2] border border-[#FAD8D8] p-3.5 rounded-xl leading-relaxed text-left font-mono">
                {apiError}
              </p>
              <div className="flex justify-center gap-3 pt-2">
                <button
                  onClick={() => setStep(1)}
                  className="px-4 py-2 bg-white hover:bg-[#F8F9FF] border border-[#E6E5F0] text-[#17172F] rounded-xl text-xs font-semibold"
                >
                  Choose Different Exhibit
                </button>
                <button
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
