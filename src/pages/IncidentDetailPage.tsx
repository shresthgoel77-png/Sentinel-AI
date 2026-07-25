import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ShieldAlert, Activity, CheckCircle, XCircle } from 'lucide-react';
import { useState, useEffect } from 'react';
import api from '../api';

export default function IncidentDetailPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [incident, setIncident] = useState<any>(null);
    const [expanded, setExpanded] = useState(false);

    const fetchIncident = () => {
        api.get(`/incidents/${id}`)
            .then(res => setIncident(res.data))
            .catch(err => console.error("Failed to load incident:", err));
    };

    useEffect(() => {
        fetchIncident();
    }, [id]);

    const handleUpdateStatus = (newStatus: string) => {
        api.patch(`/incidents/${id}`, { status: newStatus })
            .then(() => fetchIncident())
            .catch(err => console.error("Failed to update status:", err));
    };

    if (!incident) return <div className="text-white">Loading...</div>;

    return (
        <div className="flex flex-col gap-6">
            <div className="flex justify-between items-start">
                <button onClick={() => navigate('/dashboard/incidents')} className="p-2 bg-[#1C2128] border border-[#2D333B] rounded-lg text-gray-400 hover:text-white hover:border-gray-500 transition-all">
                    <ArrowLeft className="w-5 h-5" />
                </button>
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold text-white tracking-tight">INC-{incident.id.toString().padStart(4, '0')}</h1>
                        <span className="bg-red-500/10 text-red-500 border border-red-500/20 px-2 py-0.5 rounded text-xs font-semibold uppercase">{incident.severity}</span>
                    </div>
                    <p className="text-sm text-gray-400 mt-1">{new Date(incident.created_at).toLocaleString()} • App: {incident.application_id || 'System'}</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-[#1C2128] border border-[#2D333B] rounded-2xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-white mb-4">Payload Forensics</h2>
                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between items-center mb-2">
                                    <label className="text-xs text-gray-500 uppercase tracking-wide font-medium">Attempted Prompt ({incident.full_prompt.length} chars)</label>
                                    {incident.full_prompt.length > 50 && (
                                        <button onClick={() => setExpanded(!expanded)} className="text-xs text-blue-400 hover:text-blue-300">
                                            {expanded ? 'Collapse' : 'Expand Details'}
                                        </button>
                                    )}
                                </div>
                                <div className={`bg-[#0E1116] border border-[#2D333B] rounded-xl p-4 font-mono text-sm text-red-400 break-words whitespace-pre-wrap transition-all ${expanded ? '' : 'line-clamp-4'}`}>
                                    {incident.full_prompt}
                                </div>
                            </div>
                            <div className="pt-4 border-t border-[#2D333B]">
                                <label className="text-xs text-gray-500 uppercase tracking-wide font-medium">Scanner Breakdown</label>
                                <div className="mt-3 bg-[#0E1116] border border-[#2D333B] rounded-xl p-5 shadow-inner">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-sm text-gray-300 flex items-center gap-2"><Activity className="w-4 h-4 text-blue-400" /> Semantic Risk Confidence</span>
                                        <span className="text-sm font-bold text-red-500">{incident.risk_score}%</span>
                                    </div>
                                    <div className="w-full bg-gray-800 rounded-full h-2.5 mb-6">
                                        <div className="bg-gradient-to-r from-orange-500 to-red-600 h-2.5 rounded-full" style={{ width: `${incident.risk_score}%` }}></div>
                                    </div>

                                    {incident.scanner_breakdown?.isolated_injection_phrases && (
                                        <div>
                                            <span className="text-xs text-gray-400 font-medium">Isolated Vectors:</span>
                                            <div className="flex flex-wrap gap-2 mt-2">
                                                {incident.scanner_breakdown.isolated_injection_phrases.map((phrase: string) => (
                                                    <span key={phrase} className="bg-red-500/10 text-red-400 px-3 py-1.5 rounded-md text-xs border border-red-500/30">"{phrase}"</span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="space-y-6">
                    <div className="bg-[#1C2128] border border-[#2D333B] rounded-2xl p-6 shadow-sm">
                        <h2 className="text-lg font-semibold text-white mb-4">Resolution Tools</h2>

                        <div className="space-y-3">
                            <button onClick={() => handleUpdateStatus('resolved')} className="w-full flex items-center justify-center gap-2 bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-500 border border-emerald-500/20 px-4 py-2.5 rounded-lg font-medium transition-colors">
                                <CheckCircle className="w-4 h-4" /> Mark as Resolved
                            </button>
                            <button onClick={() => handleUpdateStatus('false_positive')} className="w-full flex items-center justify-center gap-2 bg-gray-700/20 hover:bg-gray-700/40 text-gray-300 border border-gray-600/30 px-4 py-2.5 rounded-lg font-medium transition-colors">
                                <XCircle className="w-4 h-4" /> False Positive
                            </button>
                        </div>

                        <div className="mt-6 pt-6 border-t border-[#2D333B]">
                            <h3 className="text-sm font-medium text-white mb-3">Metadata</h3>
                            <div className="space-y-3">
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-500">Current Status</span>
                                    <span className="text-emerald-400 capitalize bg-emerald-500/10 px-2 py-0.5 rounded">{incident.status}</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-500">Entity Type</span>
                                    <span className="text-gray-300 font-medium">{incident.type}</span>
                                </div>
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-500">Linked Policy</span>
                                    <span className="text-blue-400">{incident.policy_triggered || 'None'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
