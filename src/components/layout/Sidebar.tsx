import { NavLink } from 'react-router-dom';
import { LayoutDashboard, AlertCircle, Shield, AppWindow, Activity, Users, Settings, FileText } from 'lucide-react';

const navItems = [
    { path: '/dashboard/overview', label: 'Overview', icon: LayoutDashboard },
    { path: '/dashboard/incidents', label: 'Incidents', icon: AlertCircle },
    { path: '/dashboard/policies', label: 'Policies', icon: Shield },
    { path: '/dashboard/applications', label: 'Applications', icon: AppWindow },
    { path: '/dashboard/traffic', label: 'Live Traffic', icon: Activity },
    { path: '/dashboard/audit', label: 'Audit & Reports', icon: FileText },
    { path: '/dashboard/team', label: 'Team', icon: Users },
    { path: '/dashboard/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
    return (
        <div className="w-64 h-screen bg-[#0E1116] border-r border-[#1C2128] flex flex-col shrink-0 text-gray-400 relative z-30">
            <div className="p-6 flex items-center gap-3">
                <Shield className="text-emerald-500 w-6 h-6" />
                <span className="text-white font-semibold text-lg tracking-wide">Sentinel AI</span>
            </div>
            <nav className="flex-grow pt-4">
                <ul className="flex flex-col gap-1 px-3">
                    {navItems.map((item) => (
                        <li key={item.path}>
                            <NavLink
                                to={item.path}
                                className={({ isActive }) =>
                                    `flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors ${isActive
                                        ? 'bg-[#1C2128] text-white'
                                        : 'hover:bg-[#1C2128]/50 hover:text-white'
                                    }`
                                }
                            >
                                <item.icon className="w-5 h-5 opacity-70" />
                                <span className="text-sm font-medium">{item.label}</span>
                            </NavLink>
                        </li>
                    ))}
                </ul>
            </nav>
            <div className="p-4 border-t border-[#1C2128]">
                <div className="text-xs text-center opacity-50">
                    v1.0.0 (Gateway Proxy)
                </div>
            </div>
        </div>
    );
}
