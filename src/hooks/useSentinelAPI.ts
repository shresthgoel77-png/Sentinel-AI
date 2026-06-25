import { useState, useRef, useCallback } from 'react';
import type { Verdict } from '../lib/types'; // Adjust path if needed

export interface AnalysisResult {
  risk_score: number;
  threat_level: string;
  verdict: Verdict;
  details: string;
}

export function useSentinelAPI() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [finalResult, setFinalResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // FIX: Use 'number' instead of 'NodeJS.Timeout' for browser environments
  const pollingIntervalRef = useRef<number | null>(null);

  const clearPolling = useCallback(() => {
    if (pollingIntervalRef.current !== null) {
      window.clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  const analyzePrompt = async (prompt: string) => {
    if (!prompt.trim()) return;

    // 1. Reset state for a fresh run
    setIsAnalyzing(true);
    setLogs(["[SYSTEM] Initializing Sentinel connection..."]);
    setFinalResult(null);
    setError(null);
    clearPolling();

    try {
      // 2. Send prompt to the Python backend
      const response = await fetch('http://localhost:8000/api/analyze-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) throw new Error('Backend connection failed');
      
      const data = await response.json();
      const taskId = data.task_id;

      // 3. Start the half-second polling loop to read Redis status
      // FIX: Use window.setInterval to strictly enforce the browser API
      pollingIntervalRef.current = window.setInterval(async () => {
        try {
          const statusRes = await fetch(`http://localhost:8000/api/status/${taskId}`);
          const statusData = await statusRes.json();

          if (statusData.error) {
            clearPolling();
            setError(statusData.error);
            setIsAnalyzing(false);
            return;
          }

          // Append log only if it's new
          setLogs((prev) => {
            if (prev[prev.length - 1] !== statusData.status) {
              return [...prev, statusData.status];
            }
            return prev;
          });

          // 4. Halt polling when Redis signals the task is complete
          if (statusData.is_complete === "true" || statusData.is_complete === true) {
            clearPolling();
            setIsAnalyzing(false);
            
            if (statusData.result) {
              const parsedResult = typeof statusData.result === 'string' 
                ? JSON.parse(statusData.result) 
                : statusData.result;
              setFinalResult(parsedResult);
            }
          }
        } catch (pollErr) {
          console.error("Polling error:", pollErr);
        }
      }, 500); // 500ms heartbeat
      
    } catch (err: any) {
      setError(err.message || "Failed to reach backend");
      setLogs((prev) => [...prev, "[ERROR] Backend unreachable. Check if Python/Redis are running."]);
      setIsAnalyzing(false);
      clearPolling();
    }
  };

  return { analyzePrompt, isAnalyzing, logs, finalResult, error, clearPolling };
}