import { useState, useRef, useCallback } from 'react';
import type { Verdict } from '../lib/types';

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

  const pollingIntervalRef = useRef<number | null>(null);

  const clearPolling = useCallback(() => {
    if (pollingIntervalRef.current !== null) {
      window.clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  const analyzePrompt = async (prompt: string) => {
    if (!prompt.trim()) return;

    setIsAnalyzing(true);
    setLogs(["[SYSTEM] Initializing Sentinel engine connection..."]);
    setFinalResult(null);
    setError(null);
    clearPolling();

    try {
      // FIX 1: We change the endpoint to 127.0.0.1 to prevent Windows localhost resolution bugs
      // FIX 2: We change the payload key from 'prompt' to 'text' to match your Pydantic model
      const response = await fetch('http://127.0.0.1:8000/api/analyze-prompt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: prompt }),
      });

      if (!response.ok) {
        throw new Error(`Backend returned status code ${response.status}`);
      }
      
      const data = await response.json();
      const taskId = data.task_id;

      // Start polling the status endpoint
      pollingIntervalRef.current = window.setInterval(async () => {
        try {
          const statusRes = await fetch(`http://127.0.0.1:8000/api/status/${taskId}`);
          const statusData = await statusRes.json();

          if (statusData.error) {
            clearPolling();
            setError(statusData.error);
            setIsAnalyzing(false);
            return;
          }

          // FIX 3: Read 'message' or 'step' from your LangGraph response instead of 'status'
          const currentLogMessage = statusData.message || statusData.step;
          
          if (currentLogMessage) {
            setLogs((prev) => {
              if (prev[prev.length - 1] !== currentLogMessage) {
                return [...prev, currentLogMessage];
              }
              return prev;
            });
          }

          // Check if the LangGraph agent chain has finished
          if (statusData.is_complete === true || statusData.is_complete === "true") {
            clearPolling();
            setIsAnalyzing(false);
            
            // Map your final Graph states directly into the UI dashboard elements
            setFinalResult({
              risk_score: statusData.confidence || 0,
              threat_level: statusData.threat_level || 'low',
              verdict: statusData.final_action === 'block' ? 'threat' : 'safe',
              details: statusData.findings || 'Analysis complete. No severe issues flagged.'
            });
          }
        } catch (pollErr) {
          console.error("Polling heartbeat error:", pollErr);
        }
      }, 500); // 500ms heartbeat
      
    } catch (err: any) {
      setError(err.message || "Failed to establish cross-origin connection to Python backend.");
      setLogs((prev) => [...prev, "[ERROR] Pipeline connection failed. Ensure Uvicorn and Redis are active."]);
      setIsAnalyzing(false);
      clearPolling();
    }
  };

  return { analyzePrompt, isAnalyzing, logs, finalResult, error, clearPolling };
}