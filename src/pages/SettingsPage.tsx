import { useState } from 'react';
import { Settings2, Bell, Hash } from 'lucide-react';
import toast from 'react-hot-toast';

export default function SettingsPage() {
    const [webhook, setWebhook] = useState("");
    const [isActive, setIsActive] = useState(true);
    const [saving, setSaving] = useState(false);

    const handleSave = () => {
        setSaving(true);
        const toastId = toast.loading("Saving configuration...");
        fetch('http://localhost:8000/api/alerts/configure', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer sk_sentinel_demo_key', 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: "slack", webhook_url: webhook, is_active: isActive, events: ["incident.critical", "incident.high"] })
        }).then((res) => {
            if (res.ok) {
                toast.success("Webhook configuration saved successfully.", { id: toastId });
            } else {
                toast.error("Failed to save configuration.", { id: toastId });
            }
        }).catch(() => {
            toast.error("Failed to save configuration.", { id: toastId });
        }).finally(() => setSaving(false));
    }

    return (
        <div className="max-w-4xl">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
                    <Settings2 className="w-8 h-8 text-gray-500" /> Platform Settings
                </h1>
                <p className="text-sm text-gray-400 mt-2">Configure enterprise integrations and global gateway controls.</p>
            </div>

            <div className="bg-[#1C2128] border border-[#2D333B] rounded-2xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-[#2D333B] bg-[#22272E] flex items-center gap-2 text-white font-medium">
                    <Bell className="w-5 h-5 text-emerald-500" /> Real-time Alerting (Webhooks)
                </div>
                <div className="p-6 flex flex-col gap-6">
                    <div>
                        <label className="text-sm font-medium text-gray-300 flex items-center gap-2 mb-2"><Hash className="w-4 h-4 text-gray-400" /> Slack Webhook URL</label>
                        <input type="text" value={webhook} onChange={e => setWebhook(e.target.value)} placeholder="https://hooks.slack.com/services/YOUR_TEAM/YOUR_CHANNEL/YOUR_TOKEN" className="w-full bg-[#0E1116] border border-[#2D333B] text-gray-300 text-sm rounded-lg px-4 py-3 outline-none focus:border-blue-500 transition-colors shadow-inner" />
                    </div>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-white font-medium">Enable Alert Engine</p>
                            <p className="text-xs text-gray-500 mt-1">Dispatches alerts instantly on Critical or High-severity security events.</p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked={isActive} onChange={() => setIsActive(!isActive)} className="sr-only peer" />
                            <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-500"></div>
                        </label>
                    </div>
                </div>
                <div className="px-6 py-4 border-t border-[#2D333B] bg-[#22272E] flex justify-between items-center">
                    <div></div>
                    <button onClick={handleSave} disabled={saving} className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50">
                        {saving ? "Saving..." : "Save Configuration"}
                    </button>
                </div>
            </div>
        </div>
    )
}
