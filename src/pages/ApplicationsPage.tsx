import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, AppWindow, MoreVertical, Key } from 'lucide-react';
import api from '../api';
import Skeleton from '../components/ui/Skeleton';

export default function ApplicationsPage() {
    const [apps, setApps] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const navigate = useNavigate();

    const fetchApps = async () => {
        setIsLoading(true);
        try {
            const { data } = await api.get('/applications');
            setApps(data);
        } catch (e) {
            console.error("Failed to fetch applications:", e);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchApps();
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsCreating(true);
        try {
            await api.post('/applications', {
                name,
                description,
                status: 'active'
            });
            await fetchApps();
            setIsModalOpen(false);
            setName('');
            setDescription('');
        } catch (e) {
            console.error("Failed to create app:", e);
        } finally {
            setIsCreating(false);
        }
    };

    return (
        <div className="flex flex-col gap-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold text-white tracking-tight">Applications</h1>
                <button onClick={() => setIsModalOpen(true)} className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-colors">
                    <Plus className="w-4 h-4" /> Create App
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
                {isLoading ? (
                    <>
                        <div className="bg-[#1C2128] p-6 rounded-2xl border border-[#2D333B] h-48"><Skeleton className="h-full w-full" /></div>
                        <div className="bg-[#1C2128] p-6 rounded-2xl border border-[#2D333B] h-48"><Skeleton className="h-full w-full" /></div>
                        <div className="bg-[#1C2128] p-6 rounded-2xl border border-[#2D333B] h-48"><Skeleton className="h-full w-full" /></div>
                    </>
                ) : apps.length === 0 ? (
                    <div className="col-span-1 md:col-span-3 p-12 text-center text-gray-400 bg-[#1C2128] border border-[#2D333B] rounded-2xl">
                        No applications found. Create one to generate API keys.
                    </div>
                ) : (
                    apps.map(app => (
                        <div key={app.id} onClick={() => navigate(`/dashboard/applications/${app.id}`)} className="bg-[#1C2128] p-6 rounded-2xl border border-[#2D333B] hover:border-[#3D444D] cursor-pointer transition-all group shadow-sm hover:shadow-md flex flex-col">
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-3 bg-blue-500/10 rounded-xl group-hover:bg-blue-500/20 transition-colors">
                                    <AppWindow className="w-6 h-6 text-blue-500" />
                                </div>
                                <button className="text-gray-500 hover:text-gray-300" onClick={(e) => e.stopPropagation()}><MoreVertical className="w-5 h-5" /></button>
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-1">{app.name}</h3>
                            <p className="text-sm text-gray-400 mb-4 h-10 line-clamp-2">{app.description}</p>
                            <div className="flex items-center justify-between pt-4 border-t border-[#2D333B] mt-auto">
                                <div className="flex items-center gap-1.5 text-sm text-gray-400">
                                    <Key className="w-4 h-4" />
                                    <span>{app.api_keys?.length || 0} Keys</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className={`w-2 h-2 rounded-full ${app.status === 'active' ? 'bg-emerald-500' : 'bg-gray-500'}`}></span>
                                    <span className="text-xs font-medium text-gray-300 capitalize">{app.status}</span>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {isModalOpen && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center">
                    <div className="bg-[#1C2128] border border-[#2D333B] w-full max-w-md rounded-2xl p-6 shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-4">Create Application</h2>
                        <form onSubmit={handleCreate} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Name</label>
                                <input autoFocus required value={name} onChange={e => setName(e.target.value)} className="w-full bg-[#0E1116] border border-[#2D333B] rounded-lg px-4 py-2 text-white outline-none focus:border-blue-500 transition-colors" placeholder="e.g. Sales Copilot" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Description</label>
                                <textarea value={description} onChange={e => setDescription(e.target.value)} className="w-full bg-[#0E1116] border border-[#2D333B] rounded-lg px-4 py-2 text-white outline-none focus:border-blue-500 transition-colors resize-none h-24" placeholder="App description..."></textarea>
                            </div>
                            <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-[#2D333B]">
                                <button type="button" onClick={() => setIsModalOpen(false)} disabled={isCreating} className="px-4 py-2 rounded-lg font-medium text-gray-400 hover:text-white transition-colors disabled:opacity-50">Cancel</button>
                                <button type="submit" disabled={isCreating} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50">
                                    {isCreating ? "Creating..." : "Create"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    )
}
