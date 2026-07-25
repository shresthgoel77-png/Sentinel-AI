import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Key, Plus, Shield, Activity, Copy, Check } from 'lucide-react';
import { useState, useEffect } from 'react';
import api from '../api';
import Skeleton from '../components/ui/Skeleton';
import { AreaChart, Area, XAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function ApplicationDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [app, setApp] = useState<any>(null);
    const [keys, setKeys] = useState<any[]>([]);
    const [copiedKeyId, setCopiedKeyId] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isGenerating, setIsGenerating] = useState(false);

    const fetchAppDetails = async () => {
        setIsLoading(true);
        try {
            const { data } = await api.get(`/applications/${id}`);
            setApp(data);
            if (data.api_keys) setKeys(data.api_keys);
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchAppDetails();
    }, [id]);

    const handleGenerateKey = async () => {
        setIsGenerating(true);
        try {
            const { data } = await api.post(`/applications/${id}/keys`);
            await fetchAppDetails();
        } catch (e) {
            console.error(e);
        } finally {
            setIsGenerating(false);
        }
    };

    const copyKey = (keyString: string, keyId: number) => {
        navigator.clipboard.writeText(keyString);
        setCopiedKeyId(keyId);
        setTimeout(() => setCopiedKeyId(null), 2000);
    }

    return (
        <div className="flex flex-col gap-6">
            <div className="flex justify-between items-start">
                <button onClick={() => navigate('/dashboard/applications')} className="p-2 bg-[#1C2128] border border-[#2D333B] rounded-lg text-gray-400 hover:text-white hover:border-gray-500 transition-all">
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                    {isLoading ? (
                        <>
                            <Skeleton className="h-[36px] w-48 mb-2" />
                            <Skeleton className="h-[20px] w-64" />
                        </>
                    ) : (
                        <>
                            <h1 className="text-3xl font-bold text-white tracking-tight">{app?.name}</h1>
                            <p className="text-sm text-gray-400 mt-1">ID: {id} • {app?.description}</p>
                        </>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-[#1C2128] rounded-2xl border border-[#2D333B] p-6 shadow-sm">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-lg font-semibold text-white flex items-center gap-2"><Key className="w-5 h-5 text-blue-500" /> API Keys</h2>
                            <button onClick={handleGenerateKey} disabled={isGenerating || isLoading} className="text-sm bg-[#2D333B] hover:bg-[#3D444D] text-white px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-2 disabled:opacity-50">
                                <Plus className="w-4 h-4" /> {isGenerating ? "Generating..." : "Generate Key"}
                            </button>
                        </div>

                        <div className="space-y-3">
                            {isLoading ? (
                                <Skeleton className="h-[70px] w-full" />
                            ) : keys.map(k => (
                                <div key={k.id} className="bg-[#0E1116] border border-[#2D333B] rounded-xl p-4 flex justify-between items-center group">
                                    <div>
                                        <p className="font-mono text-sm text-emerald-400">{k.hashed_key || k.key || 'sk_sentinel_*******'}</p>
                                        <p className="text-xs text-gray-500 mt-1">Status: Active</p>
                                    </div>
                                    <button onClick={() => copyKey(k.hashed_key || k.key || '', k.id)} className="p-2 text-gray-400 hover:text-white hover:bg-[#1C2128] rounded-lg transition-colors focus:outline-none">
                                        {copiedKeyId === k.id ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                                    </button>
                                </div>
                            ))}
                            {!isLoading && keys.length === 0 && (
                                <p className="text-gray-500 text-sm italic">No API keys found for this application. Generate one to get started.</p>
                            )}
                        </div>
                    </div>

                    <div className="bg-[#1C2128] rounded-2xl border border-[#2D333B] p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-6"><Activity className="w-5 h-5 text-amber-500" /> App Traffic</h2>
                        <div className="flex items-center justify-center p-8 bg-[#0E1116] border border-[#2D333B] rounded-xl text-gray-500 text-sm italic shadow-inner">
                            Traffic telemetry aggregation pending baseline activity.
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="bg-[#1C2128] rounded-2xl border border-[#2D333B] p-6 shadow-sm flex flex-col h-full">
                        <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4"><Shield className="w-5 h-5 text-emerald-500" /> Linked Policy</h2>
                        <div className="bg-[#0E1116] border border-[#2D333B] rounded-xl p-4 flex-grow">
                            <div className="flex justify-between items-center mb-4">
                                <span className="text-sm font-medium text-white">Default Strict</span>
                                <span className="text-xs bg-emerald-500/10 text-emerald-500 px-2 py-0.5 rounded border border-emerald-500/20">Active</span>
                            </div>
                            <div className="space-y-2 text-xs text-gray-400">
                                <div className="flex justify-between border-b border-[#2D333B] pb-2">
                                    <span>Max Risk Score</span>
                                    <span className="text-white">80</span>
                                </div>
                                <div className="flex justify-between pt-1">
                                    <span>Data Masking</span>
                                    <span className="text-white">Enabled</span>
                                </div>
                            </div>
                        </div>
                        <button className="w-full mt-4 text-sm bg-[#2D333B] hover:bg-[#3D444D] text-white px-4 py-2 rounded-lg font-medium transition-colors">Change Policy</button>
                    </div>
                </div>
            </div>
        </div>
    )
}
