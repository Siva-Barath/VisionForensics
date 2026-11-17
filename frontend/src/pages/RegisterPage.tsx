import AuthShell from '@/components/AuthShell';
import { useState, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import {
  Lock,
  Mail,
  User as UserIcon,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import { extractApiError } from '@/utils/helpers';

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Password rules validation
  const rules = useMemo(() => {
    return {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
      special: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password),
    };
  }, [password]);

  const allRulesPassed = useMemo(() => {
    return Object.values(rules).every(Boolean);
  }, [rules]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!fullName.trim() || !email.trim() || !password) {
      setErrorMessage('Please complete all required fields.');
      return;
    }

    if (!allRulesPassed) {
      setErrorMessage('Please ensure your password meets all complexity standards.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    try {
      await register({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
      });
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const parsed = extractApiError(err);
      setErrorMessage(parsed);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell registration>
      <div className="bg-white rounded-3xl p-8 sm:p-10 shadow-xl border border-[#E6E5F0] w-full space-y-5">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#F0EBFF] text-[#6D35E8] border border-[#DDD5F9] text-xs font-semibold mb-1">
            <span>Institutional Provisioning</span>
          </div>
          <h1 className="text-3xl font-extrabold text-[#17172F] tracking-tight">
            Create Analyst Profile
          </h1>
          <p className="text-xs sm:text-sm text-[#73758B] mt-0.5">
            Provision your examiner credentials to access the workspace
          </p>
        </div>

        {errorMessage && (
          <div className="p-3.5 bg-[#FDF2F2] border border-[#FAD8D8] rounded-xl flex items-start gap-3 text-xs text-[#DC4545]">
            <AlertCircle size={18} className="text-[#DC4545] shrink-0 mt-0.5" />
            <div className="flex-1 font-medium leading-relaxed">{errorMessage}</div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="registerpage-field-1" className="block text-xs font-bold text-[#17172F] uppercase tracking-wider mb-1.5">
              Full Name & Title
            </label>
            <div className="relative">
              <UserIcon size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#73758B]" />
              <input
                id="registerpage-field-1"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Dr. Eleanor Vance, Forensic Examiner"
                required
                autoFocus
                className="w-full bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] shadow-sm transition-all"
              />
            </div>
          </div>

          <div>
            <label htmlFor="registerpage-field-2" className="block text-xs font-bold text-[#17172F] uppercase tracking-wider mb-1.5">
              Official Analyst Email
            </label>
            <div className="relative">
              <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#73758B]" />
              <input
                id="registerpage-field-2"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.vance@pilot.visionforensics.local"
                required
                className="w-full bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] shadow-sm transition-all"
              />
            </div>
          </div>

          <div>
            <label htmlFor="registerpage-field-3" className="block text-xs font-bold text-[#17172F] uppercase tracking-wider mb-1.5">
              Master Password
            </label>
            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#73758B]" />
              <input
                id="registerpage-field-3"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                className="w-full bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl pl-10 pr-10 py-2.5 text-sm text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] shadow-sm transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#73758B] hover:text-[#17172F] transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            {/* Password complexity checklist */}
            <div className="mt-2.5 p-3 bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl grid grid-cols-2 gap-2 text-[11px]">
              <div className={`flex items-center gap-1.5 ${rules.length ? 'text-[#159B55] font-semibold' : 'text-[#73758B]'}`}>
                {rules.length ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
                <span>Min 8 characters</span>
              </div>
              <div className={`flex items-center gap-1.5 ${rules.uppercase ? 'text-[#159B55] font-semibold' : 'text-[#73758B]'}`}>
                {rules.uppercase ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
                <span>Uppercase [A-Z]</span>
              </div>
              <div className={`flex items-center gap-1.5 ${rules.lowercase ? 'text-[#159B55] font-semibold' : 'text-[#73758B]'}`}>
                {rules.lowercase ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
                <span>Lowercase [a-z]</span>
              </div>
              <div className={`flex items-center gap-1.5 ${rules.number ? 'text-[#159B55] font-semibold' : 'text-[#73758B]'}`}>
                {rules.number ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
                <span>Number [0-9]</span>
              </div>
              <div className={`flex items-center gap-1.5 col-span-2 ${rules.special ? 'text-[#159B55] font-semibold' : 'text-[#73758B]'}`}>
                {rules.special ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
                <span>Special character (!@#$%^&*)</span>
              </div>
            </div>
          </div>

          <div>
            <label htmlFor="registerpage-field-4" className="block text-xs font-bold text-[#17172F] uppercase tracking-wider mb-1.5">
              Confirm Password
            </label>
            <div className="relative">
              <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#73758B]" />
              <input
                id="registerpage-field-4"
                type={showPassword ? 'text' : 'password'}
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm password"
                required
                className="w-full bg-[#F8F9FF] border border-[#E6E5F0] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#17172F] placeholder-[#9E9FB1] focus:outline-none focus:border-[#7045E8] shadow-sm transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !allRulesPassed || password !== confirmPassword}
            className="w-full py-2.5 px-4 bg-[#7045E8] hover:bg-[#5F33DB] disabled:opacity-50 text-white font-bold text-sm rounded-xl shadow-md shadow-violet-200 transition-all flex items-center justify-center gap-2 mt-2"
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>Registering Account...</span>
              </>
            ) : (
              <>
                <span>Create Analyst Account</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        {/* Login link */}
        <div className="text-center text-xs text-[#73758B] pt-1">
          Already credentialed?{' '}
          <Link to="/login" className="text-[#7045E8] hover:underline font-bold">
            Sign In to Existing Account
          </Link>
        </div>
      </div>
    </AuthShell>
  );
}
