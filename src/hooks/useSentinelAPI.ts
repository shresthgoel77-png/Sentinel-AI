import { useState, useRef, useCallback } from 'react';
import type { Verdict } from '../lib/types';

// ==========================================
// TYPE DEFINITIONS
// ==========================================
export interface AnalysisResult {
    risk_score: number;
    threat_level: string;
    verdict: Verdict;
    details: string;
}

export interface ScanStatus {
    status: string;
    stage: string | null;
    message: string | null;
    isolated_injection_phrases: string[];
    risk_score: number | null;
}

// ==========================================
// UNIFIED SENTINEL API HOOK
// ==========================================
export function useSentinelAPI() {
    // Shared State
    const [logs, setLogs] = useState<string[]>([]);
    const [error, setError] = useState<string | null>(null);
    const pollingIntervalRef = useRef<number | null>(null);

    // Phase 1-3 State (Text Prompt Analysis)
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [finalResult, setFinalResult] = useState<AnalysisResult | null>(null);

    // Phase 4 State (File Scanning Terminal)
    const [isScanning, setIsScanning] = useState(false);
    const [finalVerdict, setFinalVerdict] = useState<ScanStatus | null>(null);

    // ==========================================
    // UTILITIES
    // ==========================================
    const clearPolling = useCallback(() => {
        if (pollingIntervalRef.current !== null) {
            window.clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
        }
    }, []);

    // ==========================================
    // ROUTE 1: TEXT PROMPT INGESTION
    // ==========================================
    const analyzePrompt = async (prompt: string) => {
        if (!prompt.trim()) return;

        setIsAnalyzing(true);
        setLogs(["[SYSTEM] Initializing Sentinel engine connection..."]);
        setFinalResult(null);
        setError(null);
        clearPolling();

        try {
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

                    const currentLogMessage = statusData.message || statusData.step;

                    if (currentLogMessage) {
                        setLogs((prev) => {
                            if (prev[prev.length - 1] !== currentLogMessage) {
                                return [...prev, currentLogMessage];
                            }
                            return prev;
                        });
                    }

                    if (statusData.is_complete === true || statusData.is_complete === "true") {
                        clearPolling();
                        setIsAnalyzing(false);
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
            }, 500);

        } catch (err: any) {
            setError(err.message || "Failed to establish cross-origin connection to Python backend.");
            setLogs((prev) => [...prev, "[ERROR] Pipeline connection failed. Ensure Uvicorn and Redis are active."]);
            setIsAnalyzing(false);
            clearPolling();
        }
    };

    // ==========================================
    // ROUTE 2: FILE SCANNING TERMINAL
    // ==========================================
    const startScan = async (file: File) => {
        setIsScanning(true);
        setLogs([]); 
        setFinalVerdict(null);
        setError(null);
        clearPolling();

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("http://127.0.0.1:8000/api/scan", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) throw new Error("Backend ingestion failed.");

            const data = await response.json();
            const taskId = data.task_id;

            pollingIntervalRef.current = window.setInterval(async () => {
                try {
                    const res = await fetch(`http://127.0.0.1:8000/api/status/${taskId}`);
                    if (!res.ok) return;

                    const statusData: ScanStatus = await res.json();

                    if (statusData.message) {
                        setLogs(prevLogs => {
                            if (prevLogs[prevLogs.length - 1] !== statusData.message) {
                                return [...prevLogs, statusData.message!];
                            }
                            return prevLogs;
                        });
                    }

                    if (statusData.status === "safe" || statusData.status === "malicious") {
                        clearPolling();
                        setFinalVerdict(statusData);
                        setIsScanning(false);
                    }

                } catch (error) {
                    console.error("Polling error:", error);
                }
            }, 400); 

        } catch (err: any) {
            setLogs(prev => [...prev, `[ERROR] Connection refused: ${err.message}`]);
            setError(err.message);
            setIsScanning(false);
            clearPolling();
        }
    };

    
    // ==========================================
    // EXPORT ALL CAPABILITIES
    // ==========================================
    return {
        // Shared
        logs,
        error,
        clearPolling,
        
        // Phase 1-3 (Text)
        isAnalyzing,
        analyzePrompt,
        finalResult,
        
        // Phase 4 (Files)
        isScanning,
        startScan,
        finalVerdict
    };
}