import { useState, useEffect } from 'react';
import { Shield, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

// Turns a fetch Response's status into a readable message, calling out auth/server failures explicitly.
const messageForStatus = (status: number, fallback: string) => {
    if (status === 401) return "Your session has expired. Please log in again.";
    if (status >= 500) return "Server error. Please try again in a moment.";
    return fallback;
}

export default function OnboardingModal() {
    const [open, setOpen] = useState(false);
    const [step, setStep] = useState(1);
    const navigate = useNavigate();

    useEffect(() => {
        fetch('http://localhost:8000/api/me/onboarding', {
            headers: { 'Authorization': 'Bearer sk_sentinel_demo_key' }
        }).then(res => {
            if (!res.ok) throw new Error(messageForStatus(res.status, "Failed to load onboarding status."));
            return res.json();
        }).then(data => {
            if (!data.onboarding_completed) {
                setOpen(true);
            }
        }).catch((err) => {
            toast.error(err instanceof Error ? err.message : "Unable to verify onboarding status.");
        });
    }, []);

    const finishOnboarding = () => {
        fetch('http://localhost:8000/api/me/onboarding', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer sk_sentinel_demo_key' }
        }).then((res) => {
            if (!res.ok) throw new Error(messageForStatus(res.status, "Failed to complete onboarding setup."));
            setOpen(false);
            navigate('/dashboard/overview');
        }).catch((err) => {
            toast.error(err instanceof Error ? err.message : "Failed to complete onboarding setup.");
        });
    }

    if (!open) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#1C2128] border border-[#2D333B] rounded-2xl w-full max-w-lg p-8 shadow-2xl relative">
                <div className="flex justify-center mb-6">
                    <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center border border-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.2)]">
                        <Shield className="w-8 h-8 text-emerald-500" />
                    </div>
                </div>
                {step === 1 && (
                    <div className="text-center animate-in fade-in zoom-in duration-300">
                        <h2 className="text-2xl font-bold text-white mb-2">Welcome to Sentinel AI</h2>
                        <p className="text-gray-400 mb-8 leading-relaxed">Let's secure your AI pipelines. We'll set up your first application and attach a baseline policy matrix to get you started.</p>
                        <button onClick={() => setStep(2)} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 transition-all shadow-[0_0_15px_rgba(37,99,235,0.3)]">
                            Begin Setup <ArrowRight className="w-4 h-4" />
                        </button>
                    </div>
                )}
                {step === 2 && (
                    <div className="animate-in slide-in-from-right-8 duration-300">
                        <h2 className="text-xl font-bold text-white mb-2">Register Application</h2>
                        <p className="text-sm text-gray-400 mb-6">Create a logical grouping for your proxy intercepts.</p>
                        <input type="text" placeholder="e.g. Production Support Chatbot" className="w-full bg-[#0E1116] border border-[#2D333B] text-gray-200 px-4 py-3 rounded-lg mb-6 outline-none focus:border-blue-500" defaultValue="My First AI App" />
                        <button onClick={() => setStep(3)} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2">
                            Register App <ArrowRight className="w-4 h-4" />
                        </button>
                    </div>
                )}
                {step === 3 && (
                    <div className="animate-in slide-in-from-right-8 duration-300">
                        <h2 className="text-xl font-bold text-white mb-2">Select Protection Baseline</h2>
                        <p className="text-sm text-gray-400 mb-6">Choose default heuristics to block structural anomalies.</p>
                        <div className="space-y-3 mb-6">
                            <div className="p-4 rounded-xl border border-blue-500 bg-blue-500/10 cursor-pointer flex justify-between items-center">
                                <div><h3 className="font-semibold text-white text-sm">Strict Security</h3><p className="text-[12px] text-gray-400 mt-1">Blocks all Jailbreaks, prompt injections, and applies PII redaction.</p></div>
                                <CheckCircle2 className="w-5 h-5 text-blue-500" />
                            </div>
                            <div className="p-4 rounded-xl border border-[#2D333B] bg-[#0E1116] opacity-50 cursor-pointer">
                                <h3 className="font-semibold text-white text-sm">Lenient (Monitor Only)</h3>
                                <p className="text-[12px] text-gray-400 mt-1">Logs all activity without intercepting actual HTTP responses.</p>
                            </div>
                        </div>
                        <button onClick={finishOnboarding} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                            Complete Setup <CheckCircle2 className="w-4 h-4" />
                        </button>
                    </div>
                )}
            </div>

        </div>
    )
}
