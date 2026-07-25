import { useState, useEffect } from 'react';
import { Activity, CheckCircle, ShieldAlert } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import Skeleton from '../components/ui/Skeleton';

export default function TrafficPage() {
    const [isLoading, setIsLoading] = useState(true);
    const [traffic, setTraffic] = useState<any[]>([]);
    const [liveIndicator, setLiveIndicator] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchTraffic = () => {
            api.get('/traffic?limit=50')
                .then(res => {
                    if (Array.isArray(res.data)) {
                        setTraffic(res.data);
                        setLiveIndicator(true);
                        setTimeout(() => setLiveIndicator(false), 800);
                    }
                })
                .catch(err => console.error("Traffic API Error:", err))
                .finally(() => setIsLoading(false));
        };
        fetchTraffic();
        const intv = setInterval(fetchTraffic, 3000);
        return () => clearInterval(intv);
    }, []);

    return (
        <div className="flex flex-col h-[calc(100vh-100px)]">
            <div className="flex justify-between items-end mb-6 shrink-0">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
                        <Activity className="w-8 h-8 text-blue-500" /> Live Feed
                        {liveIndicator && <span className="flex h-3 w-3 relative ml-2"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span><span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span></span>}
                    </h1>
                    <p className="text-sm text-gray-400 mt-2">Streaming real-time proxy engagements mapping native inference traffic.</p>
                </div>
            </div>

            <div className="flex-1 bg-[#1C2128] border border-[#2D333B] rounded-2xl overflow-hidden flex flex-col shadow-sm">
                <div className="overflow-y-auto flex-1">
                    <table className="w-full text-left border-collapse text-sm">
                        <thead className="bg-[#22272E] sticky top-0 z-10 shadow-sm border-b border-[#2D333B]">
                            <tr>
                                <th className="p-4 font-semibold text-gray-400 uppercase tracking-widest text-[10px]">Timestamp</th>
                                <th className="p-4 font-semibold text-gray-400 uppercase tracking-widest text-[10px]">Provider / Model</th>
                                <th className="p-4 font-semibold text-gray-400 uppercase tracking-widest text-[10px]">Threat Trace Overview</th>
                                <th className="p-4 font-semibold text-gray-400 uppercase tracking-widest text-[10px]">Risk Confidence</th>
                                <th className="p-4 font-semibold text-gray-400 uppercase tracking-widest text-[10px] text-right">Interceptor Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#2D333B]">
                            {isLoading ? (
                                <tr>
                                    <td colSpan={5} className="p-4"><Skeleton className="h-[48px] w-full" /></td>
                                </tr>
                            ) : traffic.length > 0 ? (
                                traffic.map((log) => (
                                    <tr key={log.id} className="hover:bg-[#2D333B]/50 transition-colors group cursor-pointer" onClick={() => log.action_taken === 'BLOCKED' && navigate('/dashboard/incidents')}>
                                        <td className="p-4 text-gray-400 whitespace-nowrap">{new Date(log.time_stamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}.{new Date(log.time_stamp).getMilliseconds().toString().padStart(3, '0')} <span className="text-[10px] text-gray-600 ml-2">{log.latency_ms}ms roundtrip</span></td>
                                        <td className="p-4 text-gray-300">
                                            <span className="bg-[#0E1116] border border-[#2D333B] px-2 py-0.5 rounded text-xs font-mono">{log.provider_used} // {log.model_name}</span>
                                        </td>
                                        <td className="p-4 text-gray-400 w-[30%]">
                                            <div className="truncate max-w-[250px] font-mono text-[11px]">{log.threat_classification ? <span className="text-red-400">{log.threat_classification.replace(/_/g, ' ')}</span> : <span className="text-gray-500">Standard Execution</span>}</div>
                                        </td>
                                        <td className="p-4">
                                            {log.risk_score > 0 ? (
                                                <div className="flex items-center gap-2">
                                                    <span className={`w-2 h-2 rounded-full shadow-[0_0_8px_rgba(0,0,0,0.5)] ${log.risk_score > 70 ? 'bg-red-500 shadow-red-500/50' : 'bg-yellow-500 shadow-yellow-500/50'}`}></span>
                                                    <span className={`font-mono text-xs font-medium ${log.risk_score > 70 ? 'text-red-400' : 'text-yellow-400'}`}>Score: {log.risk_score}</span>
                                                </div>
                                            ) : <span className="text-gray-600 text-xs">Clean Pipeline</span>}
                                        </td>
                                        <td className="p-4 text-right">
                                            {log.action_taken === 'ALLOWED' ? (
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                                    <CheckCircle className="w-3 h-3" /> ALLOWED
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-red-500/10 text-red-500 border border-red-500/20 shadow-[0_0_10px_rgba(239,68,68,0.1)]">
                                                    <ShieldAlert className="w-3 h-3" /> BLOCKED
                                                </span>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={5} className="p-12 text-center text-gray-500">
                                        <Activity className="w-8 h-8 mx-auto mb-3 opacity-20" />
                                        Waiting for Real-Time Gateway Traffic...
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
