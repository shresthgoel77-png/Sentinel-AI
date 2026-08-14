import { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Filter, AlertTriangle, ShieldAlert, AlertCircle, Info, X, Check } from 'lucide-react';
import api from '../api';
import Skeleton from '../components/ui/Skeleton';

interface Incident {
    id: number | string;
    application_id?: number | string | null;
    type: string;
    severity: string;
    status: string;
    created_at: string;
    [key: string]: unknown;
}

const SEVERITY_OPTIONS = ['critical', 'high', 'medium', 'low'] as const;
type SeverityFilter = (typeof SEVERITY_OPTIONS)[number];

export default function IncidentsPage() {
    const [isLoading, setIsLoading] = useState(true);
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const navigate = useNavigate();

    // --- Search bar state ---
    const [searchQuery, setSearchQuery] = useState('');

    // --- Filter dropdown state ---
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [activeSeverities, setActiveSeverities] = useState<Set<SeverityFilter>>(new Set());
    const filterRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        setIsLoading(true);
        api.get('/incidents')
            .then(res => {
                if (Array.isArray(res.data)) setIncidents(res.data);
            })
            .catch(err => console.error("Incident API Error:", err))
            .finally(() => setIsLoading(false));
    }, []);

    // Close the filter dropdown when clicking outside of it or pressing Escape.
    useEffect(() => {
        if (!isFilterOpen) return;

        const handleClickOutside = (event: MouseEvent) => {
            if (filterRef.current && !filterRef.current.contains(event.target as Node)) {
                setIsFilterOpen(false);
            }
        };
        const handleEscape = (event: KeyboardEvent) => {
            if (event.key === 'Escape') setIsFilterOpen(false);
        };

        document.addEventListener('mousedown', handleClickOutside);
        document.addEventListener('keydown', handleEscape);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            document.removeEventListener('keydown', handleEscape);
        };
    }, [isFilterOpen]);

    const toggleSeverity = (severity: SeverityFilter) => {
        setActiveSeverities(prev => {
            const next = new Set(prev);
            if (next.has(severity)) {
                next.delete(severity);
            } else {
                next.add(severity);
            }
            return next;
        });
    };

    const clearFilters = () => setActiveSeverities(new Set());

    /**
     * Synthetic client-side filtering over the locally held incident list.
     * Matches the search query against the ID, application, type, severity,
     * and status fields, then narrows further by any active severity filters.
     * This runs entirely on data already in local state (no network calls),
     * and logs the resulting match count for visibility during development.
     */
    const filteredIncidents = useMemo(() => {
        const query = searchQuery.trim().toLowerCase();

        const result = incidents.filter(inc => {
            const matchesSeverity =
                activeSeverities.size === 0 || activeSeverities.has(inc.severity.toLowerCase() as SeverityFilter);

            if (!matchesSeverity) return false;
            if (!query) return true;

            const haystack = [
                `INC-${inc.id.toString().padStart(4, '0')}`,
                inc.application_id != null ? `App ID: ${inc.application_id}` : 'System',
                inc.type,
                inc.severity,
                inc.status,
            ]
                .join(' ')
                .toLowerCase();

            return haystack.includes(query);
        });

        console.log(
            `[IncidentsPage] filtered ${result.length}/${incidents.length} incidents ` +
            `(query="${query}", severities=${activeSeverities.size ? [...activeSeverities].join(',') : 'all'})`
        );

        return result;
    }, [incidents, searchQuery, activeSeverities]);

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
                        <input
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search incidents..."
                            aria-label="Search incidents"
                            className="bg-[#1C2128] border border-[#2D333B] rounded-lg pl-9 pr-8 py-2 text-sm text-white focus:outline-none focus:border-blue-500 w-64 transition-colors"
                        />
                        {searchQuery && (
                            <button
                                type="button"
                                onClick={() => setSearchQuery('')}
                                aria-label="Clear search"
                                className="absolute right-2.5 top-2.5 text-gray-500 hover:text-white transition-colors"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        )}
                    </div>

                    <div className="relative" ref={filterRef}>
                        <button
                            type="button"
                            onClick={() => setIsFilterOpen(prev => !prev)}
                            aria-haspopup="true"
                            aria-expanded={isFilterOpen}
                            className={`relative p-2 bg-[#1C2128] border rounded-lg text-gray-400 hover:text-white transition-colors ${isFilterOpen ? 'border-blue-500 text-white' : 'border-[#2D333B]'
                                }`}
                        >
                            <Filter className="w-4 h-4" />
                            {activeSeverities.size > 0 && (
                                <span className="absolute -top-1.5 -right-1.5 flex items-center justify-center w-4 h-4 rounded-full bg-blue-500 text-white text-[10px] font-semibold">
                                    {activeSeverities.size}
                                </span>
                            )}
                        </button>

                        {isFilterOpen && (
                            <div className="absolute right-0 mt-2 w-56 bg-[#1C2128] border border-[#2D333B] rounded-lg shadow-lg z-10 overflow-hidden">
                                <div className="flex items-center justify-between px-3 py-2 border-b border-[#2D333B]">
                                    <span className="text-xs font-semibold tracking-wide text-gray-400 uppercase">Severity</span>
                                    {activeSeverities.size > 0 && (
                                        <button
                                            type="button"
                                            onClick={clearFilters}
                                            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                                        >
                                            Clear
                                        </button>
                                    )}
                                </div>
                                <ul className="py-1">
                                    {SEVERITY_OPTIONS.map(sev => {
                                        const isActive = activeSeverities.has(sev);
                                        return (
                                            <li key={sev}>
                                                <button
                                                    type="button"
                                                    onClick={() => toggleSeverity(sev)}
                                                    className="w-full flex items-center justify-between gap-2 px-3 py-2 text-sm text-gray-200 hover:bg-[#22272E] transition-colors capitalize"
                                                >
                                                    <span className="flex items-center gap-2">
                                                        {getSeverityIcon(sev)}
                                                        {sev}
                                                    </span>
                                                    {isActive && <Check className="w-4 h-4 text-blue-400" />}
                                                </button>
                                            </li>
                                        );
                                    })}
                                </ul>
                            </div>
                        )}
                    </div>
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
                        ) : filteredIncidents.length > 0 ? (
                            filteredIncidents.map(inc => (
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
                                <td colSpan={5} className="p-8 text-center text-gray-500">
                                    {incidents.length === 0
                                        ? 'No active incidents found.'
                                        : 'No incidents match your search or filters.'}
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}