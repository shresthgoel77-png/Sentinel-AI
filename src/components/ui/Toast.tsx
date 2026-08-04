import React, { createContext, useContext, useState, ReactNode } from 'react';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

type ToastType = 'success' | 'error' | 'info';

interface ToastMessage {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = (message: string, type: ToastType = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            style={{ animation: 'slideIn 0.3s ease-out forwards' }}
            className={`flex items-center gap-3 px-5 py-4 rounded-xl shadow-2xl text-white max-w-sm pointer-events-auto border ${
              toast.type === 'success' ? 'bg-[#1C2128] border-emerald-500/30' : toast.type === 'error' ? 'bg-[#1C2128] border-red-500/30' : 'bg-[#1C2128] border-blue-500/30'
            }`}
          >
            {toast.type === 'success' ? <CheckCircle className="w-5 h-5 text-emerald-500" /> : toast.type === 'error' ? <AlertCircle className="w-5 h-5 text-red-500" /> : <Info className="w-5 h-5 text-blue-500" />}
            <span className="text-sm font-medium">{toast.message}</span>
            <button onClick={() => setToasts(t => t.filter(x => x.id !== toast.id))} className="ml-auto text-gray-400 hover:text-white transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
      <style>{`
        @keyframes slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to { transform: translateX(0); opacity: 1; }
        }
      `}</style>
    </ToastContext.Provider>
  );
}

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
};
