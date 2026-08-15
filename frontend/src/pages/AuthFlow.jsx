import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { authApi } from '../services/api';
import { 
  HeartPulse, 
  ShieldCheck, 
  Lock, 
  Mail, 
  ChevronRight, 
  UserCircle, 
  Users, 
  ArrowLeft, 
  Smartphone, 
  Pill, 
  Activity, 
  Mic, 
  LockKeyhole, 
  Globe, 
  Heart,
  Eye,
  EyeOff
} from 'lucide-react';
import BrandLogo from '../components/BrandLogo';

// A warm, inclusive family animation using abstract/stylized soft shapes
const FamilyAnimation = () => {
  return (
    <div className="relative w-full max-w-md aspect-square mx-auto flex items-center justify-center">
      {/* Background glow */}
      <motion.div 
        animate={{ scale: [1, 1.05, 1], opacity: [0.5, 0.8, 0.5] }} 
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        className="absolute inset-0 bg-gradient-to-tr from-purple-400/20 to-blue-400/20 blur-3xl rounded-full" 
      />
      
      <div className="relative w-64 h-64 flex items-end justify-center pb-8">
        {/* Grandmother (Soft Purple) */}
        <motion.div 
          initial={{ x: -60, opacity: 0 }} animate={{ x: -20, opacity: 1 }} transition={{ duration: 1.5, ease: "easeOut" }}
          className="absolute z-10 flex flex-col items-center"
        >
          <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-300 to-purple-500 shadow-lg" />
          <div className="w-20 h-24 rounded-t-[40px] bg-gradient-to-br from-purple-400 to-purple-600 shadow-lg -mt-4" />
        </motion.div>

        {/* Grandfather (Calm Blue) */}
        <motion.div 
          initial={{ x: 60, opacity: 0 }} animate={{ x: 20, opacity: 1 }} transition={{ duration: 1.5, ease: "easeOut" }}
          className="absolute z-10 flex flex-col items-center"
        >
          <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-300 to-blue-500 shadow-lg" />
          <div className="w-24 h-28 rounded-t-[40px] bg-gradient-to-br from-blue-400 to-blue-600 shadow-lg -mt-4" />
        </motion.div>

        {/* Girl Child (Warm Pink) */}
        <motion.div 
          initial={{ x: -100, y: 50, opacity: 0 }} animate={{ x: -45, y: 10, opacity: 1 }} transition={{ delay: 1, duration: 1.5, ease: "easeOut" }}
          className="absolute z-20 flex flex-col items-center"
        >
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-300 to-pink-500 shadow-lg" />
          <div className="w-14 h-16 rounded-t-[30px] bg-gradient-to-br from-pink-400 to-pink-600 shadow-lg -mt-2" />
        </motion.div>

        {/* Boy Child (Cyan/Teal) */}
        <motion.div 
          initial={{ x: 100, y: 50, opacity: 0 }} animate={{ x: 45, y: 10, opacity: 1 }} transition={{ delay: 1.2, duration: 1.5, ease: "easeOut" }}
          className="absolute z-20 flex flex-col items-center"
        >
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-300 to-teal-500 shadow-lg" />
          <div className="w-16 h-18 rounded-t-[30px] bg-gradient-to-br from-teal-400 to-teal-600 shadow-lg -mt-2" />
        </motion.div>

        {/* Glowing Hearts appearing after family gathers */}
        <motion.div 
          initial={{ scale: 0, opacity: 0 }} animate={{ scale: [0, 1.2, 1], opacity: [0, 1, 0.8] }} transition={{ delay: 2.5, duration: 1 }}
          className="absolute -top-4 right-10 text-pink-500"
        >
          <Heart className="w-8 h-8 fill-current drop-shadow-[0_0_15px_rgba(236,72,153,0.8)]" />
        </motion.div>
        
        <motion.div 
          initial={{ scale: 0, opacity: 0 }} animate={{ scale: [0, 1.2, 1], opacity: [0, 1, 0.6] }} transition={{ delay: 2.8, duration: 1 }}
          className="absolute -top-10 left-12 text-purple-400"
        >
          <Heart className="w-6 h-6 fill-current drop-shadow-[0_0_10px_rgba(168,85,247,0.8)]" />
        </motion.div>
      </div>
    </div>
  );
};

export default function AuthFlow({ onLogin, onBack }) {
  const [view, setView] = useState('login'); // 'login', 'phone', 'otp', 'role', 'signup'
  const [role, setRole] = useState('');
  const [formData, setFormData] = useState({ name: '', email: '', password: '' });
  const [phoneData, setPhoneData] = useState({ phone: '', otp: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [showSignupPassword, setShowSignupPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Scroll to top on mount
  useEffect(() => { window.scrollTo(0, 0); }, [view]);

  const getAuthErrorMessage = (err) => {
    if (err.code === 'ECONNABORTED' || err.message?.includes('timeout') || !err.response) {
      return 'Unable to reach ORMA. Please try again.';
    }
    if (err.response.status === 401) {
      return 'Incorrect email or password.';
    }
    if (err.response.status === 409) {
      return 'An account with this email already exists.';
    }
    if (err.response.status >= 500) {
      return 'Something went wrong while signing in.';
    }
    return err.response?.data?.detail || 'Authentication failed. Please try again.';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (loading) return;
    setError('');
    setLoading(true);
    try {
      if (view === 'login') {
        const res = await authApi.login(formData.email, formData.password);
        localStorage.setItem('orma_token', res.access_token);
        onLogin(res.user);
      } else {
        const res = await authApi.signup({ ...formData, role });
        localStorage.setItem('orma_token', res.access_token);
        onLogin(res.user);
      }
    } catch (err) {
      const endpoint = view === 'login' ? '/api/auth/login' : '/api/auth/signup';
      const status = err.response?.status;
      const detail = err.response?.data?.detail || err.message;
      console.log(`[AUTH FRONTEND] endpoint: ${endpoint}, status: ${status}, detail: ${detail}`);
      setError(getAuthErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };


  const [googleLoading, setGoogleLoading] = useState(false);

  const handleGoogleLogin = () => {
    setError('');
    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

    if (!googleClientId || googleClientId === 'your_google_client_id.apps.googleusercontent.com' || googleClientId === 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com') {
      setError('Google Client ID is not configured. Please set VITE_GOOGLE_CLIENT_ID in your frontend .env file.');
      return;
    }

    if (!window.google?.accounts?.id) {
      setError('Google Sign-In SDK is loading. Please try again in a moment.');
      return;
    }

    setGoogleLoading(true);

    try {
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response) => {
          if (!response?.credential) {
            setError('Google authentication failed: No credential received from Google.');
            setGoogleLoading(false);
            return;
          }

          try {
            const res = await authApi.googleLogin({ 
              id_token: response.credential, 
              role: role || null 
            });
            localStorage.setItem('orma_token', res.access_token);
            onLogin(res.user);
          } catch (err) {
            console.error("Google Verification Error:", err.response?.data || err.message);
            setError(err.response?.data?.detail || "Google authentication failed. Please try again.");
          } finally {
            setGoogleLoading(false);
          }
        },
        auto_select: false,
        cancel_on_tap_outside: true
      });

      // Prompt Google Account Chooser
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed()) {
          const reason = notification.getNotDisplayedReason();
          console.warn("Google One-Tap prompt not displayed:", reason);
          setGoogleLoading(false);
          setError('Google Sign-In prompt was suppressed or closed by browser. Please allow popups or check session.');
        } else if (notification.isDismissedMoment()) {
          const dismissReason = notification.getDismissedReason();
          if (dismissReason !== 'credential_returned') {
            setError('Google sign-in was cancelled or closed.');
            setGoogleLoading(false);
          }
        }
      });
    } catch (err) {
      setError('Failed to launch Google Sign-In: ' + err.message);
      setGoogleLoading(false);
    }
  };

  const handlePhoneRequest = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await authApi.requestOtp(phoneData.phone);
      setView('otp');
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send OTP.");
    } finally {
      setLoading(false);
    }
  };

  const handlePhoneVerify = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await authApi.verifyOtp(phoneData.phone, phoneData.otp, role || 'elderly');
      localStorage.setItem('orma_token', res.access_token);
      onLogin(res.user);
    } catch (err) {
      setError(err.response?.data?.detail || "Invalid OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });

  const features = [
    { icon: Mic, label: 'Voice AI' },
    { icon: Users, label: 'Family Connect' },
    { icon: Pill, label: 'Smart Reminders' },
    { icon: HeartPulse, label: 'Emotional Wellness' },
    { icon: LockKeyhole, label: 'Secure & Private' },
    { icon: Globe, label: 'Multilingual' },
  ];

  return (
    <div className="min-h-screen bg-[#FDFBF7] text-slate-800 font-sans flex flex-col lg:flex-row overflow-hidden selection:bg-purple-200 selection:text-purple-900">
      
      {/* Left Column: Branding & Emotion */}
      <div className="lg:w-5/12 bg-gradient-to-br from-purple-50 via-[#FDFBF7] to-blue-50 relative flex flex-col justify-between p-8 md:p-16 border-b lg:border-b-0 lg:border-r border-slate-200">
        <div className="relative z-10 flex items-center justify-between w-full">
          {onBack && (
            <button onClick={onBack} className="text-slate-500 hover:text-purple-600 transition-colors p-2 -ml-2 rounded-full hover:bg-purple-100">
              <ArrowLeft className="w-6 h-6" />
            </button>
          )}
          <BrandLogo 
            className="h-10" 
            textClassName="text-2xl" 
            textColor="text-slate-800" 
            accentColor="text-purple-600" 
          />
        </div>

        <div className="relative z-10 my-12 lg:my-0 flex-1 flex flex-col justify-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <h1 className="text-4xl md:text-5xl font-extrabold text-slate-800 tracking-tight leading-tight mb-6">
              Care. Connect. <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-blue-600">
                Remember.
              </span>
            </h1>
            <p className="text-lg text-slate-600 max-w-md leading-relaxed mb-10">
              Supporting families with intelligent care. Experience a warm, inclusive healthcare companion designed to bring generations closer together safely.
            </p>
          </motion.div>

          <FamilyAnimation />
        </div>

        <div className="relative z-10 hidden lg:grid grid-cols-3 gap-4">
          {features.map((feat, idx) => (
            <div key={idx} className="flex flex-col items-center justify-center p-3 rounded-2xl bg-white/50 backdrop-blur-sm border border-slate-100 shadow-sm text-slate-600">
              <feat.icon className="w-5 h-5 mb-2 text-purple-500" />
              <span className="text-[10px] font-bold uppercase tracking-wider text-center">{feat.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Right Column: Authentication */}
      <div className="lg:w-7/12 flex flex-col justify-center items-center p-8 md:p-16 relative bg-white">
        {/* Subtle background elements */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-50 rounded-full blur-[100px] opacity-50 pointer-events-none" />
        
        <div className="w-full max-w-md relative z-10">
          <AnimatePresence mode="wait">
            
            {/* VIEW: LOGIN */}
            {view === 'login' && (
              <motion.div key="login" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <div className="text-center mb-10">
                  <h2 className="text-3xl font-bold text-slate-800 mb-2">Welcome Back</h2>
                  <p className="text-slate-500">Sign in to monitor wellness and stay connected.</p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm text-center font-medium">
                    {error}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div>
                    <label className="block text-sm font-bold text-slate-900 mb-2 ml-1">Email Address</label>
                    <div className="relative flex items-center group">
                      <Mail className="absolute left-4 w-5 h-5 text-slate-500 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type="email" 
                        name="email" 
                        value={formData.email} 
                        onChange={handleChange} 
                        className="w-full h-14 bg-[#F1F5F9] border-2 border-slate-300 rounded-2xl pl-12 pr-4 text-[#172033] font-semibold text-base placeholder:text-slate-500 focus:outline-none focus:border-purple-600 focus:ring-4 focus:ring-purple-500/15 transition-all orma-light-input" 
                        placeholder="you@family.com" 
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-900 mb-2 ml-1">Password</label>
                    <div className="relative flex items-center group">
                      <Lock className="absolute left-4 w-5 h-5 text-slate-500 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type={showPassword ? "text" : "password"} 
                        name="password" 
                        value={formData.password} 
                        onChange={handleChange} 
                        className="w-full h-14 bg-[#F1F5F9] border-2 border-slate-300 rounded-2xl pl-12 pr-12 text-[#172033] font-semibold text-base placeholder:text-slate-500 focus:outline-none focus:border-purple-600 focus:ring-4 focus:ring-purple-500/15 transition-all orma-light-input" 
                        placeholder="••••••••" 
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3.5 p-2 rounded-xl text-slate-500 hover:text-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-500/30 transition-colors cursor-pointer z-10"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? (
                          <EyeOff className="w-5 h-5 text-purple-600" />
                        ) : (
                          <Eye className="w-5 h-5 text-slate-500 group-focus-within:text-purple-600" />
                        )}
                      </button>
                    </div>
                  </div>
                  <button disabled={loading} type="submit" className="w-full bg-slate-800 hover:bg-slate-900 text-white font-bold py-4 rounded-2xl transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 flex items-center justify-center gap-2 cursor-pointer">
                    {loading ? 'Authenticating...' : 'Sign In Securely'}
                  </button>
                </form>

                <div className="mt-8 flex items-center gap-4">
                  <div className="flex-1 h-px bg-slate-200" />
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">or continue with</span>
                  <div className="flex-1 h-px bg-slate-200" />
                </div>

                <div className="mt-8 grid grid-cols-2 gap-4">
                  <button 
                    type="button" 
                    disabled={loading || googleLoading}
                    onClick={handleGoogleLogin} 
                    className="flex items-center justify-center gap-2.5 py-3 px-4 border border-slate-200 hover:bg-slate-50 rounded-2xl transition-colors font-medium text-slate-600 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {googleLoading ? (
                      <>
                        <Globe className="w-5 h-5 text-purple-600 animate-spin" />
                        <span className="text-xs font-semibold text-purple-700">Connecting...</span>
                      </>
                    ) : (
                      <>
                        <Globe className="w-5 h-5 text-slate-700" />
                        <span>Google</span>
                      </>
                    )}
                  </button>
                  <button type="button" onClick={() => setView('phone')} className="flex items-center justify-center gap-3 py-3 px-4 border border-slate-200 hover:bg-slate-50 rounded-2xl transition-colors font-medium text-slate-600 cursor-pointer">
                    <Smartphone className="w-5 h-5 text-slate-700" /> Phone
                  </button>
                </div>

                <div className="mt-10 text-center">
                  <p className="text-slate-500">
                    New to Orma AI?{' '}
                    <button onClick={() => setView('role')} className="text-purple-600 font-bold hover:underline decoration-2 underline-offset-4 cursor-pointer">
                      Create an account
                    </button>
                  </p>
                </div>
              </motion.div>
            )}

            {/* VIEW: PHONE NUMBER */}
            {view === 'phone' && (
              <motion.div key="phone" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <div className="text-center mb-10">
                  <h2 className="text-3xl font-bold text-slate-800 mb-2">Phone Login</h2>
                  <p className="text-slate-500">We'll send a secure OTP to this number.</p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm text-center font-medium">
                    {error}
                  </div>
                )}

                <form onSubmit={handlePhoneRequest} className="space-y-5">
                  <div>
                    <label className="block text-sm font-bold text-slate-900 mb-2 ml-1">Phone Number</label>
                    <div className="relative flex items-center group">
                      <Smartphone className="absolute left-4 w-5 h-5 text-slate-500 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type="tel" 
                        value={phoneData.phone} 
                        onChange={(e) => setPhoneData({...phoneData, phone: e.target.value})} 
                        className="w-full h-14 bg-[#F1F5F9] border-2 border-slate-300 rounded-2xl pl-12 pr-4 text-[#172033] font-semibold text-base placeholder:text-slate-500 focus:outline-none focus:border-purple-600 focus:ring-4 focus:ring-purple-500/15 transition-all orma-light-input" 
                        placeholder="+1 (555) 000-0000" 
                      />
                    </div>
                  </div>
                  <button disabled={loading} type="submit" className="w-full bg-slate-800 hover:bg-slate-900 text-white font-bold py-4 rounded-2xl transition-all shadow-lg flex items-center justify-center cursor-pointer">
                    {loading ? 'Sending OTP...' : 'Send OTP'}
                  </button>
                </form>

                <div className="mt-10 text-center">
                  <button onClick={() => setView('login')} className="text-slate-500 font-medium hover:text-slate-800 flex items-center justify-center gap-2 mx-auto cursor-pointer">
                    <ArrowLeft className="w-4 h-4" /> Back to Login
                  </button>
                </div>
              </motion.div>
            )}

            {/* VIEW: OTP */}
            {view === 'otp' && (
              <motion.div key="otp" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <div className="text-center mb-10">
                  <h2 className="text-3xl font-bold text-slate-800 mb-2">Verify Phone</h2>
                  <p className="text-slate-500">Enter the code sent to {phoneData.phone}</p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm text-center font-medium">
                    {error}
                  </div>
                )}

                <form onSubmit={handlePhoneVerify} className="space-y-5">
                  <div>
                    <label className="block text-sm font-bold text-slate-900 mb-2 ml-1">Secure OTP</label>
                    <div className="relative flex items-center group">
                      <Lock className="absolute left-4 w-5 h-5 text-slate-500 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type="text" 
                        maxLength={6} 
                        value={phoneData.otp} 
                        onChange={(e) => setPhoneData({...phoneData, otp: e.target.value})} 
                        className="w-full h-14 bg-[#F1F5F9] border-2 border-slate-300 rounded-2xl pl-12 pr-4 text-[#172033] text-center tracking-[0.5em] focus:outline-none focus:border-purple-600 focus:ring-4 focus:ring-purple-500/15 transition-all font-bold text-lg orma-light-input" 
                        placeholder="123456" 
                      />
                    </div>
                  </div>
                  <button disabled={loading} type="submit" className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold py-4 rounded-2xl transition-all shadow-lg flex items-center justify-center gap-2 cursor-pointer">
                    {loading ? 'Verifying...' : 'Secure Sign In'} <ChevronRight className="w-5 h-5" />
                  </button>
                </form>

                <div className="mt-10 text-center">
                  <button onClick={() => setView('phone')} className="text-slate-500 font-medium hover:text-slate-800 flex items-center justify-center gap-2 mx-auto cursor-pointer">
                    <ArrowLeft className="w-4 h-4" /> Change Number
                  </button>
                </div>
              </motion.div>
            )}

            {/* VIEW: ROLE SELECTION */}
            {view === 'role' && (
              <motion.div key="role" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <div className="text-center mb-10">
                  <h2 className="text-3xl font-bold text-slate-800 mb-2">Join Our Family</h2>
                  <p className="text-slate-500">How will you be using Orma AI?</p>
                </div>

                <div className="space-y-4">
                  <button 
                    onClick={() => { setRole('elderly'); setView('signup'); }}
                    className="w-full p-6 rounded-3xl border-2 border-transparent bg-slate-50 hover:bg-purple-50 hover:border-purple-200 transition-all flex flex-col md:flex-row items-center md:items-start text-center md:text-left gap-6 group cursor-pointer"
                  >
                    <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                      <UserCircle className="w-8 h-8 text-purple-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-slate-800 mb-1 group-hover:text-purple-700 transition-colors">Parent / Elderly</h3>
                      <p className="text-sm text-slate-500 leading-relaxed">I want to use the Orma AI voice assistant for myself to remember medicines and stay connected.</p>
                    </div>
                  </button>

                  <button 
                    onClick={() => { setRole('caregiver'); setView('signup'); }}
                    className="w-full p-6 rounded-3xl border-2 border-transparent bg-slate-50 hover:bg-blue-50 hover:border-blue-200 transition-all flex flex-col md:flex-row items-center md:items-start text-center md:text-left gap-6 group cursor-pointer"
                  >
                    <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                      <ShieldCheck className="w-8 h-8 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-slate-800 mb-1 group-hover:text-blue-700 transition-colors">Child / Caregiver</h3>
                      <p className="text-sm text-slate-500 leading-relaxed">I want to care for my loved one, monitor their wellness, and receive real-time alerts.</p>
                    </div>
                  </button>
                </div>

                <div className="mt-10 text-center">
                  <button onClick={() => setView('login')} className="text-slate-500 font-medium hover:text-slate-800 flex items-center justify-center gap-2 mx-auto cursor-pointer">
                    <ArrowLeft className="w-4 h-4" /> Back to Login
                  </button>
                </div>
              </motion.div>
            )}

            {/* VIEW: SIGNUP */}
            {view === 'signup' && (
              <motion.div key="signup" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <div className="text-center mb-10">
                  <div className="inline-block px-3 py-1 bg-purple-100 text-purple-700 text-xs font-bold rounded-full uppercase tracking-widest mb-4">
                    {role === 'elderly' ? 'Elderly Account' : 'Caregiver Account'}
                  </div>
                  <h2 className="text-3xl font-bold text-slate-800 mb-2">Create Account</h2>
                  <p className="text-slate-500">Let's get you set up in seconds.</p>
                </div>

                {error && (
                  <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-2xl text-red-600 text-sm text-center font-medium">
                    {error}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                  <div>
                    <label className="block text-sm font-bold text-slate-900 mb-2 ml-1">Full Name</label>
                    <div className="relative flex items-center group">
                      <UserCircle className="absolute left-4 w-5 h-5 text-slate-500 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type="text" 
                        name="name" 
                        value={formData.name} 
                        onChange={handleChange} 
                        className="w-full h-14 bg-[#F1F5F9] border-2 border-slate-300 rounded-2xl pl-12 pr-4 text-[#172033] font-semibold text-base placeholder:text-slate-500 focus:outline-none focus:border-purple-600 focus:ring-4 focus:ring-purple-500/15 transition-all orma-light-input" 
                        placeholder="Sarah Jenkins" 
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-900 mb-2 ml-1">Email Address</label>
                    <div className="relative flex items-center group">
                      <Mail className="absolute left-4 w-5 h-5 text-slate-500 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type="email" 
                        name="email" 
                        value={formData.email} 
                        onChange={handleChange} 
                        className="w-full h-14 bg-[#F1F5F9] border-2 border-slate-300 rounded-2xl pl-12 pr-4 text-[#172033] font-semibold text-base placeholder:text-slate-500 focus:outline-none focus:border-purple-600 focus:ring-4 focus:ring-purple-500/15 transition-all orma-light-input" 
                        placeholder="you@family.com" 
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-bold text-slate-900 mb-2 ml-1">Secure Password</label>
                    <div className="relative flex items-center group">
                      <Lock className="absolute left-4 w-5 h-5 text-slate-500 group-focus-within:text-purple-600 transition-colors pointer-events-none z-10" />
                      <input 
                        required 
                        type={showSignupPassword ? "text" : "password"} 
                        name="password" 
                        value={formData.password} 
                        onChange={handleChange} 
                        className="w-full h-14 bg-[#F1F5F9] border-2 border-slate-300 rounded-2xl pl-12 pr-12 text-[#172033] font-semibold text-base placeholder:text-slate-500 focus:outline-none focus:border-purple-600 focus:ring-4 focus:ring-purple-500/15 transition-all orma-light-input" 
                        placeholder="••••••••" 
                      />
                      <button
                        type="button"
                        onClick={() => setShowSignupPassword(!showSignupPassword)}
                        className="absolute right-3.5 p-2 rounded-xl text-slate-500 hover:text-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-500/30 transition-colors cursor-pointer z-10"
                        aria-label={showSignupPassword ? "Hide password" : "Show password"}
                      >
                        {showSignupPassword ? (
                          <EyeOff className="w-5 h-5 text-purple-600" />
                        ) : (
                          <Eye className="w-5 h-5 text-slate-500 group-focus-within:text-purple-600" />
                        )}
                      </button>
                    </div>
                  </div>
                  <button disabled={loading} type="submit" className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-bold py-4 rounded-2xl transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 flex items-center justify-center gap-2 mt-4 cursor-pointer">
                    {loading ? 'Creating...' : 'Create Secure Account'} <ChevronRight className="w-5 h-5" />
                  </button>
                </form>

                <div className="mt-8 text-center">
                  <p className="text-xs text-slate-400 max-w-xs mx-auto">
                    By creating an account, you agree to our privacy policy and healthcare data processing terms.
                  </p>
                </div>

                <div className="mt-8 text-center">
                  <button onClick={() => setView('role')} className="text-slate-500 font-medium hover:text-slate-800 flex items-center justify-center gap-2 mx-auto cursor-pointer">
                    <ArrowLeft className="w-4 h-4" /> Change Role
                  </button>
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
