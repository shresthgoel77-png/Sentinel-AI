import { useState, useEffect, useRef } from 'react';

export interface ScanVerdict {
  status: 'processing' | 'safe' | 'malicious';
  stage?: 'PARSER' | 'HEURISTICS' | 'SEMANTIC_AGENT';
  message?: string;
  isolated_injection_phrases?: string[];
  risk_score?: number;
}

export const useFileScanner = () => {
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [verdict, setVerdict] = useState<ScanVerdict | null>(null);
  const pollingRef = useRef<number | null>(null);

  const stopPolling = () => {
    if (pollingRef.current !== null) {
      window.clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const processAndUploadFile = async (file: File) => {
    setIsScanning(true);
    setVerdict(null);
    setLogs([
      `[SYSTEM] Ingesting: ${file.name} (${file.size} bytes)`,
      `[SYSTEM] Initializing stream mapping to raw byte payload...`
    ]);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Replace with your actual backend endpoint if different
      const response = await fetch('/api/scan', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error(`HTTP Error ${response.status}`);
      const data = await response.json();

      if (data.task_id) {
        setLogs(prev => [...prev, `[SYSTEM] Async task allocated: ID ${data.task_id}`, `[SYSTEM] Launching 400ms polling cycle...`]);
        startPolling(data.task_id);
      } else {
        throw new Error('Malformed backend response: Missing task_id');
      }
    } catch (err: any) {
      setLogs(prev => [...prev, `[CRITICAL ERROR] Pipeline execution stalled: ${err.message}`]);
      setIsScanning(false);
    }
  };

  const startPolling = (taskId: string) => {
    stopPolling();

    pollingRef.current = window.setInterval(async () => {
      try {
        const res = await fetch(`/api/status/${taskId}`);
        if (!res.ok) return;

        const data: ScanVerdict = await res.json();

        if (data.message) {
          const currentMessage = data.message; // Capture to ensure type narrowing
          setLogs((prev: string[]): string[] => {
            const lastLog = prev.length > 0 ? prev[prev.length - 1] : undefined;
            if (lastLog === currentMessage) return prev;
            return [...prev, currentMessage];
          });
        }

        if (data.status === 'safe' || data.status === 'malicious') {
          stopPolling();
          setVerdict(data);
          setIsScanning(false);

          if (data.status === 'safe') {
            setLogs(prev => [...prev, `[SUCCESS] Ingestion authorization signature generated.`]);
          } else {
            setLogs(prev => [
              ...prev, 
              `[SECURITY ALERT] Isolated injection strings mapped. Core bypassed neutralized.`,
              `[SYSTEM] State changed: QUARANTINED.`
            ]);
          }
        }
      } catch (error) {
        setLogs(prev => [...prev, `[CONNECTIVITY WARNING] Lost sync with polling layer...`]);
      }
    }, 400);
  };

  useEffect(() => {
    return () => stopPolling();
  }, []);

  return { processAndUploadFile, isScanning, logs, verdict, setLogs };
};