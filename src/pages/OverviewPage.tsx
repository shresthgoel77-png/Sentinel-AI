import { ShieldAlert, ShieldCheck, Activity, AppWindow, ArrowRight } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import Skeleton from '../components/ui/Skeleton';

export default function OverviewPage() {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(true);
    const [liveTraffic, setLiveTraffic] = useState<any[]>([]);
    const [analytics, setAnalytics] = useState<any>({
        threats_blocked_today: 0,
        open_incidents: 0,
        policy_health_score: 100,
        applications_protected: 0,
        trend_data: [],
        top_threats: []
    });

    useEffect(() => {
        setIsLoading(true);
        Promise.all([
            api.get('/overview'),
            api.get('/traffic?limit=5')
        ]).then(([ovwRes, trafRes]) => {
            if (ovwRes.data.trend_data) setAnalytics(ovwRes.data);
            if (Array.isArray(trafRes.data)) setLiveTraffic(trafRes.data);
        }).catch(err => {
            console.error("Dashboard API Error:", err);
        }).finally(() => {
            setIsLoading(false);
        });
    }, []);

    return (
        <div className="flex flex-col gap-6">
            {/* Header */}
            <div className="flex justify-between items-center mb-2">
                <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
                    Security Overview
                    <span className="flex h-3 w-3 relative ml-1">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                    </span>
                </h1>
                <div className={`text-sm font-medium px-4 py-1.5 rounded-lg border flex items-center gap-2 bg-emerald-500/10 text-emerald-400 border-emerald-500/20`}>
                    <Activity className="w-4 h-4" /> LIVE
                </div>
            </div>

            {/* Hero Stats */}
            {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Skeleton className="h-[96px]" />
                    <Skeleton className="h-[96px]" />
                    <Skeleton className="h-[96px]" />
                    <Skeleton className="h-[96px]" />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-[#1C2128] p-6 rounded-2xl border border-[#2D333B] flex items-center gap-4 shadow-sm">
                        <div className="p-3 bg-red-500/10 rounded-xl">
                            <ShieldAlert className="w-8 h-8 text-red-500" />
                        </div>
                        <div>
                            <p className="text-gray-400 text-sm font-medium">Threats Blocked Today</p>
                            <p className="text-2xl font-bold text-white mt-1">{analytics.threats_blocked_today.toLocaleString()}</p>
                        </div>
                    </div>

                    <div className="bg-[#1C2128] p-6 rounded-2xl border border-[#2D333B] flex items-center gap-4 shadow-sm">
                        <div className="p-3 bg-amber-500/10 rounded-xl">
                            <Activity className="w-8 h-8 text-amber-500" />
                        </div>
                        <div>
                            <p className="text-gray-400 text-sm font-medium">Open Incidents</p>
                            <p className="text-2xl font-bold text-white mt-1">{analytics.open_incidents}</p>
                        </div>
                    </div>

                    <div className="bg-[#1C2128] p-6 rounded-2xl border border-[#2D333B] flex items-center gap-4 shadow-sm">
                        <div className="p-3 bg-emerald-500/10 rounded-xl">
                            <ShieldCheck className="w-8 h-8 text-emerald-500" />
                        </div>
                        <div>
                            <p className="text-gray-400 text-sm font-medium">Policy Health Score</p>
                            <p className="text-2xl font-bold text-white mt-1">{analytics.policy_health_score}%</p>
                        </div>
                    </div>

                    <div className="bg-[#1C2128] p-6 rounded-2xl border border-[#2D333B] flex items-center gap-4 shadow-sm">
                        <div className="p-3 bg-blue-500/10 rounded-xl">
                            <AppWindow className="w-8 h-8 text-blue-500" />
                        </div>
                        <div>
                            <p className="text-gray-400 text-sm font-medium">Apps Protected</p>
                            <p className="text-2xl font-bold text-white mt-1">{analytics.applications_protected}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Main Chart Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-[#1C2128] p-6 rounded-2xl border border-[#2D333B] shadow-sm">
                    <h2 className="text-lg font-semibold text-white mb-6">Traffic & Anomalies (7 Days)</h2>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={analytics.trend_data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="colorBlocked" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="date" stroke="#6b7280" style={{ fontSize: '12px' }} tickMargin={10} axisLine={false} tickLine={false} />
                                <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} axisLine={false} tickLine={false} />
                                <CartesianGrid strokeDasharray="3 3" stroke="#2D333B" vertical={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0E1116', borderColor: '#2D333B', color: '#fff', borderRadius: '8px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Area type="monotone" dataKey="allowed" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorRequests)" name="Allowed" />
                                <Area type="monotone" dataKey="blocked" stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorBlocked)" name="Blocked" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-[#1C2128] p-6 rounded-2xl border border-[#2D333B] shadow-sm">
                    <h2 className="text-lg font-semibold text-white mb-6">Top Threats Vectors</h2>
                    <div className="h-[300px] w-full">
                        {analytics.top_threats.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart layout="vertical" data={analytics.top_threats} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
                                    <XAxis type="number" hide />
                                    <YAxis type="category" dataKey="type" stroke="#6b7280" width={120} tick={{ fontSize: 11, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
                                    <Tooltip
                                        cursor={{ fill: 'transparent' }}
                                        contentStyle={{ backgroundColor: '#0E1116', borderColor: '#2D333B', color: '#fff', borderRadius: '8px' }}
                                    />
                                    <Bar dataKey="count" fill="#ef4444" radius={[0, 4, 4, 0]} barSize={24} name="Occurrences" />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full text-sm text-gray-500">No active threats detected.</div>
                        )}
                    </div>
                </div>
            </div>

            {/* Mini Traffic Feed */}
            <div className="bg-[#1C2128] rounded-2xl border border-[#2D333B] overflow-hidden shadow-sm">
                <div className="flex justify-between items-center bg-[#22272E] px-6 py-4 border-b border-[#2D333B]">
                    <h3 className="font-semibold text-white">Live Traffic Stream</h3>
                    <button onClick={() => navigate('/dashboard/traffic')} className="text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">
                        View Complete Feed <ArrowRight className="w-4 h-4" />
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-[#1C2128] border-b border-[#2D333B]">
                                <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase">Gateway Time</th>
                                <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase">Provider / Model</th>
                                <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase text-center">Threat Score</th>
                                <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase text-right">Interceptor Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#2D333B]">
                            {isLoading ? (
                                <tr>
                                    <td colSpan={4} className="p-4"><Skeleton className="h-[40px] w-full" /></td>
                                </tr>
                            ) : liveTraffic.map((log) => (
                                <tr key={log.id} onClick={() => log.action_taken === 'BLOCKED' && navigate('/dashboard/incidents')} className="hover:bg-[#2D333B]/40 transition-colors cursor-pointer group">
                                    <td className="p-4 text-sm font-mono text-gray-400 group-hover:text-blue-400 transition-colors">{new Date(log.time_stamp).toLocaleTimeString([], { hour12: false })}</td>
                                    <td className="p-4 text-sm font-mono text-gray-300">{log.provider_used} // {log.model_name}</td>
                                    <td className="p-4 text-center">
                                        {log.risk_score > 0 ? (
                                            <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium font-mono ${log.risk_score > 70 ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                                                {log.risk_score}
                                            </span>
                                        ) : <span className="text-gray-600 text-xs">—</span>}
                                    </td>
                                    <td className="p-4 text-right font-medium text-sm">
                                        <span className={log.action_taken === 'ALLOWED' ? 'text-emerald-500' : 'text-red-500'}>
                                            {log.action_taken}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
