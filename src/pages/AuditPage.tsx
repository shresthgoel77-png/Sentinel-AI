import { useState, useEffect } from 'react';
import { Download, Calendar, Filter, FileText } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

export default function AuditPage() {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    const handleExport = () => {
        let url = '/audit/export?format=csv';
        if (startDate) url += `&start=${startDate}`;
        if (endDate) url += `&end=${endDate}`;

        api.get(url, { responseType: 'blob' })
            .then(res => {
                const fileUrl = window.URL.createObjectURL(res.data);
                const a = document.createElement('a');
                a.href = fileUrl;
                a.download = `audit_export_${new Date().getTime()}.csv`;
                document.body.appendChild(a);
                a.click();
                a.remove();
            })
            .catch(console.error);
    };

    return (
        <div className="flex flex-col gap-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Audit & Reports</h1>
                    <p className="text-sm text-gray-400 mt-1">Review raw logs and generate compliance exports</p>
                </div>

                <button onClick={handleExport} className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors">
                    <Download className="w-4 h-4" /> Export CSV
                </button>
            </div>

            <div className="bg-[#1C2128] rounded-xl border border-[#2D333B] p-4 flex gap-4 items-end shadow-sm">
                <div className="flex-1">
                    <label className="block text-xs font-medium text-gray-400 uppercase tracking-wide mb-1 flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" /> Start Date</label>
                    <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} className="w-full bg-[#0E1116] border border-[#2D333B] text-gray-300 text-sm rounded-lg px-3 py-2 outline-none focus:border-blue-500 transition-colors" />
                </div>
                <div className="flex-1">
                    <label className="block text-xs font-medium text-gray-400 uppercase tracking-wide mb-1 flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" /> End Date</label>
                    <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} className="w-full bg-[#0E1116] border border-[#2D333B] text-gray-300 text-sm rounded-lg px-3 py-2 outline-none focus:border-blue-500 transition-colors" />
                </div>
                <div className="flex-none">
                    <button className="bg-[#2D333B] hover:bg-[#3D444D] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors h-[38px] flex items-center gap-2">
                        <Filter className="w-4 h-4" />
                        Apply Filters
                    </button>
                </div>
            </div>

            <div className="bg-[#1C2128] rounded-xl border border-[#2D333B] p-12 flex flex-col items-center justify-center shadow-sm">
                <FileText className="w-12 h-12 text-gray-600 mb-4" />
                <h3 className="text-lg font-medium text-white">Event Log Integration Active</h3>
                <p className="text-sm text-gray-400 max-w-md text-center mt-2">
                    The auditing pipeline is writing gateway payloads directly into your backend architecture. Configure filters and press Export to extract historical compliance reports natively.
                </p>
            </div>
        </div>
    )
}
