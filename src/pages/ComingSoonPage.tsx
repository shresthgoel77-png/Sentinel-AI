import { ShieldAlert, Info } from 'lucide-react';

export default function ComingSoonPage({ title }: { title: string }) {
    return (
        <div className="flex flex-col items-center justify-center h-[calc(100vh-8rem)] text-center">
            <div className="bg-[#1C2128] p-6 rounded-2xl border border-[#2D333B] shadow-lg max-w-md w-full">
                <div className="flex justify-center mb-4">
                    <div className="bg-emerald-500/10 p-4 rounded-full">
                        <Info className="w-8 h-8 text-emerald-500" />
                    </div>
                </div>
                <h2 className="text-2xl font-semibold text-white mb-2">{title}</h2>
                <p className="text-gray-400">
                    This module is currently under construction. Check back later for updates as we finalize the Security Command Center.
                </p>
            </div>
        </div>
    );
}
