import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Upload, 
  FileText, 
  AlertTriangle, 
  Loader2, 
  ArrowLeft, 
  ArrowRight,
  FileCheck
} from 'lucide-react';
import Card from '@/components/ui/Card';
import { uploadDocument } from '@/services/api';
import { extractApiError } from '@/utils/helpers';
import { MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB } from '@/utils/constants';

const ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg'];

export default function NewInvestigationPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [file, setFile] = useState<File | null>(null);
  const [clientError, setClientError] = useState<string | null>(null);

  // Step 2: Case Details
  const [caseTitle, setCaseTitle] = useState('');
  const [caseNotes, setCaseNotes] = useState('');
  const [priority, setPriority] = useState<'routine' | 'urgent'>('routine');

  // Step 3: Analysis Execution State
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [pipelineMessage, setPipelineMessage] = useState('Uploading document...');
  const [apiError, setApiError] = useState<string | null>(null);

  const validateAndSetFile = (selectedFile: File) => {
    setClientError(null);
    const ext = selectedFile.name.split('.').pop()?.toLowerCase() || '';

    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setClientError(
        `Unsupported file type (.${ext || 'unknown'}). Please upload a PDF, PNG, or JPEG document.`
      );
      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE_BYTES) {
      setClientError(
        `File exceeds maximum allowed size of ${MAX_FILE_SIZE_MB} MB (${(selectedFile.size / 1024 / 1024).toFixed(1)} MB uploaded).`
      );
      return;
    }

    setFile(selectedFile);
    if (!caseTitle) {
      // Auto-populate case title with filename (without extension)
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
    setUploadProgress(10);
    setPipelineMessage('Verifying file integrity and computing SHA-256 fingerprint...');
    setApiError(null);

    try {
      const response = await uploadDocument(file, (percent) => {
        setUploadProgress(Math.min(90, Math.max(15, percent)));
        if (percent >= 100) {
          setPipelineMessage('Running multi-track forgery checks (ML, copy-move, compression)...');
        }
      }, { title: caseTitle, notes: caseNotes, priority });

      setUploadProgress(100);
      if (response.processing_status === 'failed') {
        throw new Error(`Exhibit ${response.document_id} was retained, but its analysis failed. Review the backend processing error before retrying.`);
      }
      setPipelineMessage('Analysis complete. Preparing investigation report...');

      if (response && response.document_id) {
        setTimeout(() => {
          navigate(`/investigation/${response.document_id}`);
        }, 600);
      } else {
        throw new Error('Analysis completed but document ID was not received.');
      }
    } catch (err: unknown) {
      setIsUploading(false);
      const parsedError = extractApiError(err);
      setApiError(parsedError);
    }
  };

  return (
    <div className="investigation-intake max-w-3xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="border-b border-ink-border pb-4">
        <h1 className="text-2xl font-bold text-white tracking-tight">New Document Investigation</h1>
        <p className="text-sm text-gray-400 mt-1">
          Upload a document to check for image manipulation, copy-move duplication, and AI forgery indicators.
        </p>
      </div>

      {/* Simple 3-Step Wizard Progress */}
      <div className="grid grid-cols-3 gap-2 text-center text-xs font-semibold">
        <div className={`p-2.5 rounded-sm border ${
          step === 1 
            ? 'bg-brand/15 border-brand text-brand' 
            : step > 1 
              ? 'bg-ink-panel border-emerald-800 text-emerald-400' 
              : 'bg-ink-base border-ink-border text-gray-400'
        }`}>
          Step 1: Upload Document
        </div>
        <div className={`p-2.5 rounded-sm border ${
          step === 2 
            ? 'bg-brand/15 border-brand text-brand' 
            : step > 2 
              ? 'bg-ink-panel border-emerald-800 text-emerald-400' 
              : 'bg-ink-base border-ink-border text-gray-400'
        }`}>
          Step 2: Case Details
        </div>
        <div className={`p-2.5 rounded-sm border ${
          step === 3 
            ? 'bg-brand/15 border-brand text-brand' 
            : 'bg-ink-base border-ink-border text-gray-400'
        }`}>
          Step 3: Run Analysis
        </div>
      </div>

      {/* STEP 1: Upload Document */}
      {step === 1 && (
        <Card variant="evidence" className="p-6 space-y-6">
          <div className="space-y-1">
            <h2 className="text-base font-bold text-white">Select Document for Analysis</h2>
            <p className="text-xs text-gray-400">
              Supported formats: PDF (single or multi-page), PNG, JPG, or JPEG (up to {MAX_FILE_SIZE_MB} MB).
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
            className={`upload-dropzone border-2 border-dashed rounded-sm p-8 text-center transition-colors cursor-pointer ${
              file 
                ? 'border-emerald-500/60 bg-emerald-950/10' 
                : clientError 
                  ? 'border-red-500/60 bg-red-950/10' 
                  : 'border-ink-border hover:border-brand bg-ink-base/60'
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
              <div className="space-y-3">
                <FileCheck size={40} className="mx-auto text-emerald-400" />
                <div>
                  <p className="text-sm font-bold text-white">{file.name}</p>
                  <p className="text-xs text-gray-400 font-mono mt-1">
                    {(file.size / 1024 / 1024).toFixed(2)} MB | {file.name.split('.').pop()?.toUpperCase()}
                  </p>
                </div>
                <span className="inline-block px-3 py-1 bg-ink-panel border border-ink-border rounded-sm text-xs text-gray-300 font-medium hover:text-white">
                  Click or drag another file to replace
                </span>
              </div>
            ) : (
              <div className="space-y-3">
                <Upload size={36} className="mx-auto text-brand opacity-80" />
                <div>
                  <p className="text-sm font-semibold text-gray-200">
                    Drag and drop your document here, or <span className="text-brand underline">browse files</span>
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    Contracts, certificates, ID cards, receipts, invoices, or official letters
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Error Notice */}
          {clientError && (
            <div className="p-3 bg-red-950/30 border border-red-800/60 rounded-sm text-xs text-red-300 flex items-center gap-2">
              <AlertTriangle size={15} className="text-red-400 shrink-0" />
              <span>{clientError}</span>
            </div>
          )}

          {/* Buttons */}
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
              className="px-5 py-2 bg-brand hover:bg-brand-hover disabled:opacity-40 disabled:hover:bg-brand text-white rounded-sm text-xs font-bold transition-colors flex items-center gap-1.5"
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
            <h2 className="text-base font-bold text-white">Case Reference & Notes</h2>
            <p className="text-xs text-gray-400">
              Provide optional case information to identify this document in your records and final reports.
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Case Name or Reference Number
              </label>
              <input
                type="text"
                value={caseTitle}
                onChange={(e) => setCaseTitle(e.target.value)}
                placeholder="e.g. Investigation-2026-004 / Employment Verification"
                className="w-full px-3 py-2 bg-ink-base border border-ink-border rounded-sm text-sm text-white placeholder-gray-500 focus:outline-none focus:border-brand font-sans"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Priority Level
              </label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setPriority('routine')}
                  className={`flex-1 py-2 px-3 rounded-sm border text-xs font-semibold text-center transition-colors ${
                    priority === 'routine'
                      ? 'border-brand bg-brand/10 text-brand'
                      : 'border-ink-border bg-ink-base text-gray-400 hover:text-gray-200'
                  }`}
                >
                  Standard Examination
                </button>
                <button
                  type="button"
                  onClick={() => setPriority('urgent')}
                  className={`flex-1 py-2 px-3 rounded-sm border text-xs font-semibold text-center transition-colors ${
                    priority === 'urgent'
                      ? 'border-amber-600 bg-amber-950/30 text-amber-300'
                      : 'border-ink-border bg-ink-base text-gray-400 hover:text-gray-200'
                  }`}
                >
                  Urgent / Priority Case
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5">
                Examiner Notes (Optional)
              </label>
              <textarea
                value={caseNotes}
                onChange={(e) => setCaseNotes(e.target.value)}
                rows={3}
                placeholder="Briefly describe reasons for suspicion (e.g. questionable signature, font inconsistency, altered dates)..."
                className="w-full px-3 py-2 bg-ink-base border border-ink-border rounded-sm text-xs text-white placeholder-gray-500 focus:outline-none focus:border-brand font-sans resize-none"
              />
            </div>
          </div>

          {/* Attached Document Summary */}
          {file && (
            <div className="p-3 bg-ink-base rounded-sm border border-ink-border flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-gray-300">
                <FileText size={16} className="text-brand" />
                <span className="font-semibold">{file.name}</span>
                <span className="text-gray-500 font-mono">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
              </div>
              <button
                onClick={() => setStep(1)}
                className="text-[11px] text-brand hover:underline"
              >
                Change Document
              </button>
            </div>
          )}

          {/* Buttons */}
          <div className="flex justify-between items-center pt-2 border-t border-ink-border">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 text-xs font-semibold text-gray-400 hover:text-gray-200 transition-colors flex items-center gap-1.5"
            >
              <ArrowLeft size={14} /> Back
            </button>
            <button
              onClick={startAnalysis}
              className="px-6 py-2 bg-brand hover:bg-brand-hover text-white rounded-sm text-xs font-bold transition-colors flex items-center gap-1.5 shadow-sm"
            >
              Start Analysis Now <ArrowRight size={14} />
            </button>
          </div>
        </Card>
      )}

      {/* STEP 3: Analysis Execution Progress */}
      {step === 3 && (
        <Card variant="evidence" className="p-8 text-center space-y-6">
          {!apiError ? (
            <div className="space-y-6 max-w-md mx-auto">
              <div className="relative w-16 h-16 mx-auto">
                <Loader2 size={64} className="text-brand animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center font-mono text-xs font-bold text-white">
                  {uploadProgress}%
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="text-lg font-bold text-white tracking-tight">
                  Analyzing Document
                </h3>
                <p className="text-xs text-gray-300 font-mono">
                  {pipelineMessage}
                </p>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2 bg-ink-base rounded-full overflow-hidden border border-ink-border">
                <div
                  className="h-full bg-brand transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>

              <div className="text-[11px] text-gray-500 space-y-1">
                <p>Checking image manipulation, copy-move cloning, and PDF structure...</p>
                <p>Results will be displayed automatically when processing finishes.</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4 max-w-md mx-auto">
              <div className="w-14 h-14 bg-red-950/40 border border-red-800 rounded-sm flex items-center justify-center mx-auto text-red-400">
                <AlertTriangle size={28} />
              </div>
              <h3 className="text-base font-bold text-white">Analysis Could Not Complete</h3>
              <p className="text-xs text-red-300 bg-red-950/20 border border-red-800/40 p-3 rounded-sm leading-relaxed text-left font-mono">
                {apiError}
              </p>
              <div className="flex justify-center gap-3 pt-2">
                <button
                  onClick={() => setStep(1)}
                  className="px-4 py-2 bg-ink-panel hover:bg-ink-hover border border-ink-border text-gray-300 rounded-sm text-xs font-semibold"
                >
                  Choose Different File
                </button>
                <button
                  onClick={startAnalysis}
                  className="px-4 py-2 bg-brand hover:bg-brand-hover text-white rounded-sm text-xs font-semibold"
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
