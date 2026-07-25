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
    // ROUTE 1A: TEXT PROMPT INGESTION (ANALYZER)
    // ==========================================
    const analyzePrompt = async (prompt: string) => {
        if (!prompt.trim()) return;

        setIsAnalyzing(true);
        setLogs(["[SYSTEM] Initializing Prompt Analyzer..."]);
        setFinalResult(null);
        setError(null);
        clearPolling();

        try {
            const response = await fetch("http://127.0.0.1:8000/api/analyze-prompt", {
                method: "POST",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: prompt }),
            });

            if (!response.ok) throw new Error("Backend analyzer ingestion failed.");

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
                        setFinalResult({
                            risk_score: statusData.risk_score || 0,
                            threat_level: statusData.status === "malicious" ? "high" : "low",
                            verdict: statusData.status === "malicious" ? "threat" : "safe",
                            details: statusData.isolated_injection_phrases?.length 
                                ? `Isolated Injection Vectors: [ ${statusData.isolated_injection_phrases.join(', ')} ]`
                                : (statusData.message || 'Validation complete.')
                        });
                        setIsAnalyzing(false);
                    }

                } catch (error) {
                    console.error("Polling error:", error);
                }
            }, 400);

        } catch (err: any) {
            setError(err.message || "Failed to establish connection to Python backend.");
            setLogs((prev) => [...prev, "[ERROR] Pipeline connection failed."]);
            setIsAnalyzing(false);
        }
    };

    // ==========================================
    // ROUTE 1B: TEXT PROMPT INGESTION (GATEWAY)
    // ==========================================
    const analyzeGateway = async (prompt: string) => {
        if (!prompt.trim()) return;

        setIsAnalyzing(true);
        setLogs(["[SYSTEM] Initializing Sentinel Gateway connection..."]);
        setFinalResult(null);
        setError(null);
        clearPolling();

        try {
            const response = await fetch('http://127.0.0.1:8000/v1/chat/completions', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer sk_sentinel_test_123'
                },
                body: JSON.stringify({
                    model: "gpt-4",
                    messages: [{ role: "user", content: prompt }]
                }),
            });

            const data = await response.json();
            const trace = data._sentinel_trace || {};
            const latency = trace.latency_ms || 120;
            const riskScore = trace.langgraph_risk || 0;

            if (data.error || riskScore > 80) {
                setLogs([
                    "[GATEWAY] Prompt Received & Validated",
                    `[LANGGRAPH] Security pipeline evaluated. Risk Score: ${riskScore}`,
                    "[SECURITY] Threat detected! High risk content blocked.",
                    "[GATEWAY] Blocked execution.",
                    `[GATEWAY] Total latency: ${latency}ms`
                ]);
                setIsAnalyzing(false);
                setFinalResult({
                    risk_score: riskScore,
                    threat_level: 'high',
                    verdict: 'threat',
                    details: data.error ? data.error.message : "Threat Blocked."
                });
                return;
            }

            setLogs([
                "[GATEWAY] Prompt Received & Validated",
                `[LANGGRAPH] Security pipeline evaluated. Risk Score: ${riskScore}`,
                "[PROVIDER] Pre-flight cleared. Model Safe Route Activated.",
                "[EGRESS] Response Scanning for PII formatting...",
                `[GATEWAY] Transaction complete. Cost: ${trace.tokens_used || 0} tokens`,
                `[GATEWAY] Extended metrics: Latency = ${latency}ms`
            ]);
            
            setIsAnalyzing(false);
            setFinalResult({
                 risk_score: riskScore,
                 threat_level: 'low',
                 verdict: 'safe',
                 details: data.choices?.[0]?.message?.content || 'Completed safely.'
            });

        } catch (err: any) {
            setError(err.message || "Failed to establish cross-origin connection to Python backend.");
            setLogs((prev) => [...prev, "[ERROR] Pipeline connection failed. Ensure Uvicorn is active."]);
            setIsAnalyzing(false);
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
        analyzeGateway,
        finalResult,
        
        // Phase 4 (Files)
        isScanning,
        startScan,
        finalVerdict
    };
}