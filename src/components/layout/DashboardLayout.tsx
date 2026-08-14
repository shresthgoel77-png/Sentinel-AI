import { Outlet, useLocation } from 'react-router-dom';
import { useState } from 'react';
import { Search } from 'lucide-react';
import Sidebar from './Sidebar';
import OnboardingModal from '../OnboardingModal';
import DarkVeil from '../DarkVeil';

export default function DashboardLayout() {
    const location = useLocation();
    const [searchQuery, setSearchQuery] = useState('');
    const titleMap: any = {
        '/overview': 'Global Analytics Engine',
        '/policies': 'Policy Studio Management',
        '/applications': 'Registered Tenants',
        '/incidents': 'Forensic Security Logs',
        '/audit': 'Compliance Auditing',
        '/team': 'Role-Based Access Control',
        '/traffic': 'Live Telemetry Stream',
        '/settings': 'Configuration Parameters'
    };

    return (
        <div className="flex h-screen bg-[#0D1117] overflow-hidden selection:bg-blue-500/30">
            <Sidebar />
            <div className="flex-1 flex flex-col h-screen overflow-hidden relative">
                {/* Global Search Header */}
                <header className="h-16 flex-shrink-0 border-b border-[#2D333B] bg-[#161B22]/80 backdrop-blur-md flex justify-between items-center px-8 z-20 relative">
                    <div className="text-gray-400 font-medium">
                        Sentinel Platform / <span className="text-white">{titleMap[location.pathname] || 'Dashboard'}</span>
                    </div>
                    <form 
                        className="relative"
                        onSubmit={(e) => e.preventDefault()}
                    >
                        <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
                        <input 
                            type="text" 
                            placeholder="Search incidents, apps, policies (CMD+K)" 
                            className="bg-[#0E1116] border border-[#2D333B] text-sm text-gray-300 rounded-full pl-10 pr-4 py-1.5 w-[300px] outline-none focus:border-blue-500 transition-colors shadow-inner" 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </form>
                </header>

                {/* Main Content Area */}
                <main className="flex-1 overflow-y-auto p-8 relative z-10 custom-scrollbar pb-24">
                    <Outlet context={{ searchQuery }} />
                </main>

                {/* Ambient Glows */}
                <div className="absolute top-0 right-0 -mr-[500px] -mt-[300px] w-[1000px] h-[1000px] bg-blue-500/5 rounded-full blur-3xl pointer-events-none z-0"></div>
                <div className="absolute bottom-0 left-[20%] -mb-[500px] w-[800px] h-[800px] bg-emerald-500/5 rounded-full blur-3xl pointer-events-none z-0"></div>
            </div>

            <OnboardingModal />
        </div>
    )
}
