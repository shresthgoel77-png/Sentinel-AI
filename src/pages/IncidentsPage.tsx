import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, AlertTriangle, ShieldAlert, AlertCircle, Info } from 'lucide-react';
import api from '../api';
import Skeleton from '../components/ui/Skeleton';

export default function IncidentsPage() {
    const [isLoading, setIsLoading] = useState(true);
    const [incidents, setIncidents] = useState<any[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        setIsLoading(true);
        api.get('/incidents')
            .then(res => {
                if (Array.isArray(res.data)) setIncidents(res.data);
            })
            .catch(err => console.error("Incident API Error:", err))
            .finally(() => setIsLoading(false));
    }, []);

    const getSeverityColor = (sev: string) => {
        switch (sev.toLowerCase()) {
            case 'critical': return 'text-red-500 bg-red-500/10 border-red-500/20';
            case 'high': return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
            case 'medium': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
            default: return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
        }
    };

    const getSeverityIcon = (sev: string) => {
        switch (sev.toLowerCase()) {
            case 'critical': return <ShieldAlert className="w-4 h-4 text-red-500" />;
            case 'high': return <AlertTriangle className="w-4 h-4 text-orange-500" />;
            case 'medium': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
            default: return <Info className="w-4 h-4 text-blue-500" />;
        }
    }

    return (
        <div className="flex flex-col gap-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-white tracking-tight">Incident Queue</h1>
                <div className="flex gap-3">
                    <div className="relative">
                        <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-500" />
                        <input placeholder="Search incidents..." className="bg-[#1C2128] border border-[#2D333B] rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 w-64 transition-colors" />
                    </div>
                    <button className="p-2 bg-[#1C2128] border border-[#2D333B] rounded-lg text-gray-400 hover:text-white transition-colors">
                        <Filter className="w-4 h-4" />
                    </button>
                </div>
            </div>

            <div className="bg-[#1C2128] rounded-xl border border-[#2D333B] overflow-hidden shadow-sm">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-[#22272E] border-b border-[#2D333B]">
                            <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase">ID / Time</th>
                            <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase">Application</th>
                            <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase">Type</th>
                            <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase">Severity</th>
                            <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase">Status</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#2D333B]">
                        {isLoading ? (
                            <tr>
                                <td colSpan={5} className="p-4"><Skeleton className="h-[48px] w-full" /></td>
                            </tr>
                        ) : incidents.length > 0 ? (
                            incidents.map(inc => (
                                <tr key={inc.id} onClick={() => navigate(`/dashboard/incidents/${inc.id}`)} className="hover:bg-[#22272E] cursor-pointer transition-colors group">
                                    <td className="p-4">
                                        <p className="text-sm font-medium text-white group-hover:text-blue-400 transition-colors">INC-{inc.id.toString().padStart(4, '0')}</p>
                                        <p className="text-xs text-gray-500 mt-0.5">{new Date(inc.created_at).toLocaleString()}</p>
                                    </td>
                                    <td className="p-4"><span className="text-sm text-gray-300 flex items-center gap-2">App ID: {inc.application_id || 'System'}</span></td>
                                    <td className="p-4 text-sm text-gray-200 font-medium">{inc.type}</td>
                                    <td className="p-4">
                                        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-medium ${getSeverityColor(inc.severity)}`}>
                                            {getSeverityIcon(inc.severity)}
                                            {inc.severity}
                                        </div>
                                    </td>
                                    <td className="p-4" onClick={(e) => e.stopPropagation()}>
                                        <select value={inc.status} disabled className="bg-[#0E1116] border border-[#2D333B] text-gray-300 text-xs rounded px-2 py-1 outline-none focus:border-blue-500 capitalize cursor-pointer">
                                            <option value="open">Open</option>
                                            <option value="investigating">Investigating</option>
                                            <option value="resolved">Resolved</option>
                                            <option value="false_positive">False Positive</option>
                                        </select>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={5} className="p-8 text-center text-gray-500">No active incidents found.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div >
    )
}
