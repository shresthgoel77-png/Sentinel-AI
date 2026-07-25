import { useState } from 'react';

export interface GatewayResponse {
    allowed: boolean;
    content?: string;
    risk_score?: number;
    classification?: string;
    justification?: string;
    latency_ms: number;
}

export function useGateway() {
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<GatewayResponse | null>(null);

    const sendPrompt = async (prompt: string, model: string = 'gemini-2.0-flash') => {
        setIsLoading(true);
        setResult(null);
        const start = performance.now();

        try {
            const response = await fetch('http://localhost:8000/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer sk_sentinel_demo_production_secret' // Hardcoded demo tenant
                },
                body: JSON.stringify({
                    model,
                    messages: [{ role: 'user', content: prompt }]
                })
            });

            const latency_ms = Math.round(performance.now() - start);
            const data = await response.json();

            // Gracefully parse HTTP 403 blocks from the unified error schema
            if (response.status === 403 || data.error) {
                setResult({
                    allowed: false,
                    risk_score: data.error?.risk_score,
                    classification: data.error?.code,
                    justification: data.error?.message,
                    latency_ms
                });
            } else {
                setResult({
                    allowed: true,
                    content: data.choices?.[0]?.message?.content,
                    latency_ms
                });
            }
        } catch (error) {
            console.error("Gateway transmission failed: ", error);
        } finally {
            setIsLoading(false);
        }
    };

    return { isLoading, result, sendPrompt };
}
