import { useState, useEffect } from 'react';
import { Users, UserPlus, Mail, ShieldAlert, CheckCircle } from 'lucide-react';
import api from '../api';
import Skeleton from '../components/ui/Skeleton';

export default function TeamPage() {
    const [team, setTeam] = useState<any[]>([]);
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState("viewer");
    const [status, setStatus] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [isInviting, setIsInviting] = useState(false);

    useEffect(() => {
        fetchTeam();
    }, []);

    const fetchTeam = async () => {
        setIsLoading(true);
        try {
            const { data } = await api.get('/team');
            setTeam(data);
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    }

    const handleInvite = async (e: any) => {
        e.preventDefault();
        setIsInviting(true);
        setStatus("");
        try {
            await api.post('/team/invite', { email: inviteEmail, name: inviteEmail.split('@')[0], role: inviteRole }, { headers: { 'X-Mock-Role': 'admin' } });
            setInviteEmail("");
            setStatus("Invitation sent successfully!");
            await fetchTeam();
        } catch (e: any) {
            setStatus(e.response?.data?.detail || "Invite Failed");
        } finally {
            setIsInviting(false);
            setTimeout(() => setStatus(""), 3000);
        }
    }

    const handleDelete = async (id: number) => {
        try {
            await api.delete(`/team/${id}`, { headers: { 'X-Mock-Role': 'admin' } });
            await fetchTeam();
        } catch (e) {
            console.error(e);
        }
    }

    return (
        <div className="max-w-5xl">
            <div className="mb-8 flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
                        <Users className="w-8 h-8 text-gray-500" /> Team Management
                    </h1>
                    <p className="text-sm text-gray-400 mt-2">Manage organizational access and assign RBAC constraints.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-[#1C2128] border border-[#2D333B] rounded-2xl overflow-hidden shadow-sm">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-[#22272E] border-b border-[#2D333B]">
                                <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase">Team Member</th>
                                <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase">Role</th>
                                <th className="p-4 text-xs font-semibold tracking-wide text-gray-400 uppercase text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#2D333B]">
                            {isLoading ? (
                                <tr><td colSpan={3} className="p-4"><Skeleton className="h-10 w-full" /></td></tr>
                            ) : team.map(member => (
                                <tr key={member.id} className="hover:bg-[#2D333B]/30">
                                    <td className="p-4">
                                        <p className="text-sm font-medium text-white">{member.name}</p>
                                        <p className="text-xs text-gray-500 mt-0.5">{member.email}</p>
                                    </td>
                                    <td className="p-4">
                                        <span className={`inline-flex px-2 py-0.5 text-xs rounded border font-medium capitalize ${member.role === 'admin' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' : member.role === 'security_engineer' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : 'bg-gray-500/10 text-gray-400 border-gray-500/40'}`}>
                                            {member.role?.replace('_', ' ')}
                                        </span>
                                    </td>
                                    <td className="p-4 text-right">
                                        <button onClick={() => handleDelete(member.id)} className="text-xs text-gray-500 hover:text-red-400 font-medium transition-colors">Revoke Access</button>
                                    </td>
                                </tr>
                            ))}
                            {!isLoading && team.length === 0 && (
                                <tr><td colSpan={3} className="p-6 text-center text-gray-500 text-sm">No team members invited yet.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>

                <div className="bg-[#1C2128] border border-[#2D333B] rounded-2xl shadow-sm p-6">
                    <h3 className="text-white font-semibold flex items-center gap-2 mb-6"><UserPlus className="w-5 h-5 text-gray-400" /> Invite Member</h3>
                    <form onSubmit={handleInvite} className="flex flex-col gap-4">
                        <div>
                            <label className="text-xs font-medium text-gray-400 mb-1.5 block">Email Address</label>
                            <input required type="email" value={inviteEmail} onChange={e => setInviteEmail(e.target.value)} placeholder="colleague@company.com" className="w-full bg-[#0E1116] border border-[#2D333B] text-gray-200 px-3 py-2.5 rounded-lg text-sm outline-none focus:border-blue-500" />
                        </div>
                        <div>
                            <label className="text-xs font-medium text-gray-400 mb-1.5 block">RBAC Role</label>
                            <select value={inviteRole} onChange={e => setInviteRole(e.target.value)} className="w-full bg-[#0E1116] border border-[#2D333B] text-gray-200 px-3 py-2.5 rounded-lg text-sm outline-none focus:border-blue-500">
                                <option value="admin">Administrator</option>
                                <option value="security_engineer">Security Engineer</option>
                                <option value="viewer">Viewer (Read-Only)</option>
                            </select>
                        </div>
                        <button type="submit" disabled={isInviting} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition-colors mt-2 text-sm shadow-[0_0_10px_rgba(37,99,235,0.2)]">
                            {isInviting ? "Sending..." : "Send Invitation"}
                        </button>
                    </form>
                    {status && <div className="mt-4 text-xs font-medium text-emerald-400 text-center">{status}</div>}
                </div>
            </div>
        </div>
    )
}
