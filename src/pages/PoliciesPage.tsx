import { useState, useEffect } from 'react';
import { Shield, ShieldAlert, Activity, ShieldCheck, Plus, TerminalSquare, Play } from 'lucide-react';
import toast from 'react-hot-toast';
import api from '../api';
import Skeleton from '../components/ui/Skeleton';

// Maps an axios/fetch error to a readable message, calling out auth/server failures explicitly.
const getErrorMessage = (e: any, fallback: string) => {
    const status = e?.response?.status;
    if (status === 401) return "Your session has expired. Please log in again.";
    if (status && status >= 500) return "Server error. Please try again in a moment.";
    if (e?.request && !e?.response) return "Network error. Check your connection and try again.";
    return fallback;
}

export default function PoliciesPage() {
    const [policies, setPolicies] = useState<any[]>([]);
    const [testPrompt, setTestPrompt] = useState("");
    const [testResult, setTestResult] = useState<any>(null);
    const [testing, setTesting] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchPolicies();
    }, []);

    const fetchPolicies = async () => {
        setIsLoading(true);
        try {
            const { data } = await api.get('/policies');
            if (Array.isArray(data)) setPolicies(data);
        } catch (e) {
            console.error("Failed to fetch policies:", e);
            toast.error(getErrorMessage(e, "Failed to load policies."));
        } finally {
            setIsLoading(false);
        }
    }

    const togglePolicy = async (id: number) => {
        try {
            await api.patch(`/policies/${id}/toggle`);
            await fetchPolicies();
        } catch (e) {
            console.error("Failed to toggle policy:", e);
            toast.error(getErrorMessage(e, "Failed to update policy status."));
        }
    }

    const handleTest = async () => {
        if (!testPrompt.trim()) return;
        setTesting(true);
        setTestResult(null);
        try {
            const { data } = await api.post('/policies/test', { prompt: testPrompt });
            setTestResult(data);
        } catch (e) {
            console.error("Failed to execute test:", e);
            toast.error(getErrorMessage(e, "Failed to run scenario simulation."));
        } finally {
            setTesting(false);
        }
    }

    return (
        <div className="flex flex-col lg:flex-row gap-6 min-h-[calc(100vh-200px)]">
            {/* Left Col: Policies Studio */}
            <div className="flex-1 flex flex-col gap-6">
                <div className="flex justify-between items-center mb-2">
                    <div>
                        <h1 className="text-3xl font-bold text-white tracking-tight">Policy Studio</h1>
                        <p className="text-sm text-gray-400 mt-1">Configure active heuristic bounds and interception matrices.</p>
                    </div>
                    <button className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-lg font-medium flex items-center gap-2 transition-colors">
                        <Plus className="w-4 h-4" /> Create Custom Policy
                    </button>
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                    {isLoading ? (
                        <>
                            <Skeleton className="h-[120px] w-full" />
                            <Skeleton className="h-[120px] w-full" />
                        </>
                    ) : policies.map(p => (
                        <div key={p.id} className={`p-5 rounded-2xl border transition-colors ${p.is_active ? 'bg-[#1C2128] border-[#2D333B] shadow-sm' : 'bg-[#1C2128]/50 border-[#1C2128]/80'}`}>
                            <div className="flex justify-between items-start">
                                <div className="flex gap-3">
                                    <div className={`p-2.5 rounded-lg border ${p.is_active ? 'bg-blue-500/10 border-blue-500/20 text-blue-500' : 'bg-gray-500/5 border-gray-500/10 text-gray-500'}`}>
                                        <Shield className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h3 className={`font-semibold ${p.is_active ? 'text-white' : 'text-gray-500'}`}>{p.name}</h3>
                                        <p className="text-xs text-gray-500 mt-1 uppercase font-medium tracking-wide">{p.type} Template • {p.scope}</p>
                                    </div>
                                </div>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input type="checkbox" checked={p.is_active} onChange={() => togglePolicy(p.id)} className="sr-only peer" />
                                    <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                                </label>
                            </div>
                            <p className={`text-sm mt-4 line-clamp-2 ${p.is_active ? 'text-gray-300' : 'text-gray-600'}`}>{p.description}</p>
                            <div className="mt-5 flex gap-2">
                                <span className="px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider rounded border border-gray-600/30 text-gray-400">Rules: {p.rules ? p.rules.length : 1}</span>
                                {p.is_active && <span className="px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider rounded border border-blue-500/30 text-blue-400 bg-blue-500/10">Engine Active</span>}
                            </div>
                        </div>
                    ))}
                    {!isLoading && policies.length === 0 && (
                        <div className="col-span-2 p-12 text-center border overflow-hidden rounded-xl bg-[#1C2128] border-[#2D333B]">
                            <ShieldAlert className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                            <p className="text-gray-400">No policies found. Strict proxy fallback thresholds globally applied.</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Right Col: Test Bench */}
            <div className="w-full lg:w-[420px] flex-shrink-0 flex flex-col bg-[#161B22] border border-[#2D333B] rounded-2xl h-[calc(100vh-140px)] p-6 shadow-xl sticky top-0 overflow-y-auto">
                <div className="flex items-center gap-2 mb-4">
                    <TerminalSquare className="w-5 h-5 text-gray-400" />
                    <h2 className="text-lg font-bold text-white">Live Policy Bench</h2>
                </div>
                <p className="text-xs text-gray-400 mb-6 leading-relaxed">
                    Test LLM heuristics without persisting events into your active metric tracking or PostgreSQL backend.
                </p>

                <div className="flex-1 flex flex-col gap-4">
                    <label className="text-xs font-medium text-gray-500 uppercase tracking-widest">Injection Payload</label>
                    <textarea
                        className="w-full min-h-[160px] bg-[#0E1116] border border-[#2D333B] rounded-xl p-4 text-sm text-gray-300 focus:outline-none focus:border-blue-500 resize-none font-mono placeholder-gray-600 shadow-inner"
                        placeholder="eval(input('Root Command > '))"
                        value={testPrompt}
                        onChange={(e) => setTestPrompt(e.target.value)}
                    ></textarea>

                    <button onClick={handleTest} disabled={testing || !testPrompt.trim()} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 transition-colors mt-2 shadow-lg shadow-blue-500/10">
                        {testing ? <Activity className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                        {testing ? "Executing Semantic Graph..." : "Run Scenario Simulation"}
                    </button>

                    {testResult && (
                        <div className={`mt-6 p-5 rounded-xl border animate-in slide-in-from-bottom-2 ${testResult.policy_action === 'BLOCKED' ? 'bg-red-500/10 border-red-500/30' : 'bg-emerald-500/10 border-emerald-500/30'}`}>
                            <div className="flex items-center gap-2 mb-4">
                                {testResult.policy_action === 'BLOCKED' ? <ShieldAlert className="w-5 h-5 text-red-500" /> : <ShieldCheck className="w-5 h-5 text-emerald-500" />}
                                <span className={`font-bold ${testResult.policy_action === 'BLOCKED' ? 'text-red-500' : 'text-emerald-500'}`}>
                                    {testResult.policy_action}
                                </span>
                            </div>

                            <div className="space-y-3 mt-4 text-xs font-mono">
                                <div className="flex justify-between border-b border-black/20 pb-2">
                                    <span className="text-gray-400 font-medium">Risk Score</span>
                                    <span className="text-gray-200 font-bold">{testResult.risk_score}%</span>
                                </div>
                                <div className="flex justify-between border-b border-black/20 pb-2">
                                    <span className="text-gray-400 font-medium">Policy</span>
                                    <span className="text-blue-400 truncate max-w-[200px] text-right">{testResult.policy_triggered}</span>
                                </div>
                                {testResult.scanner_payload?.isolated_injection_phrases && (
                                    <div className="flex justify-between pt-1">
                                        <span className="text-gray-400 font-medium">Trace</span>
                                        <span className="text-red-400 truncate max-w-[200px] text-right">"{testResult.scanner_payload.isolated_injection_phrases[0]}"</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
