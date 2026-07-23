import { useState, useCallback, useEffect } from 'react'
import StatusBar from './components/StatusBar'
import Hero from './components/Hero'
import LiveBackendDemo from './components/LiveBackendDemo'
import GatewayDemo from './components/GatewayDemo'
import CoreAnalyzer from './components/CoreAnalyzer'
import CombinedDashboard from './components/CombinedDashboard'
import Architecture from './components/Architecture'
import JudgesSection from './components/JudgesSection'
import Footer from './components/Footer'
import DarkVeil from './components/DarkVeil'

export default function App() {
  const [stats, setStats] = useState<any>({
    threatsBlocked: 0,
    safeRequests: 0,
    totalScans: 0,
    averageRiskScore: 0,
    averageLatencyMs: 0,
    providerSplit: { openai: 0, anthropic: 0 },
    totalTokens: 0
  });

  // Pull global persistence logs
  const fetchAnalytics = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/v1/analytics/dashboard');
      if (res.ok) {
        const data = await res.json();
        if (data.stats) setStats(data.stats);
      }
    } catch (e) {
      console.error("Analytics fetch failed", e);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 3000);
    return () => clearInterval(interval);
  }, []);

  // Update immediately after a local scan
  const handleScanResult = useCallback(() => {
    setTimeout(fetchAnalytics, 1500);
  }, [])

  return (
    <div style={{ position: 'relative', width: '100%', minHeight: '100vh', overflow: 'hidden' }}>

      {/* Background layer */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: -1,
          pointerEvents: 'none'
        }}
      >
        <DarkVeil />
      </div>

      {/* Existing application content */}
      <main className="flex flex-col flex-grow" style={{ position: 'relative', zIndex: 1 }}>
        <StatusBar stats={stats as any} />
        <Hero />
        <GatewayDemo />
        <LiveBackendDemo onResult={handleScanResult} />
        {/* The single point of entry for analyzing prompts */}
        <CoreAnalyzer onResult={handleScanResult} />
        <CombinedDashboard stats={stats} />
        <Architecture />
        <JudgesSection />
        <div className="bg-background/80 backdrop-blur-sm">
          <Footer />
        </div>
      </main>
    </div>
  )
}