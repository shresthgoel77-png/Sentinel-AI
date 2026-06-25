import { useState, useCallback } from 'react'
import StatusBar from './components/StatusBar'
import Hero from './components/Hero'
import CoreAnalyzer from './components/CoreAnalyzer' // The new God Component
import CombinedDashboard from './components/CombinedDashboard'
import Architecture from './components/Architecture'
import JudgesSection from './components/JudgesSection'
import Footer from './components/Footer'
import type { ShieldStats, Verdict } from './lib/types'

const INITIAL_STATS: ShieldStats = {
  threatsBlocked: 0,
  safeRequests: 0,
  totalScans: 0
}

export default function App() {
  const [stats, setStats] = useState<ShieldStats>(INITIAL_STATS)

  // Single handler for all prompt scans coming from the real Python backend
  const handleScanResult = useCallback((verdict: Verdict) => {
    setStats((prev) => ({
      ...prev,
      threatsBlocked: prev.threatsBlocked + (verdict === 'threat' ? 1 : 0),
      safeRequests: prev.safeRequests + (verdict === 'safe' ? 1 : 0),
      totalScans: prev.totalScans + 1
    }))
  }, [])

  return (
    <div className="min-h-screen flex flex-col">
      <StatusBar stats={stats} />
      <main className="flex-grow">
        <Hero />
        
        {/* The single point of entry for analyzing prompts */}
        <CoreAnalyzer onResult={handleScanResult} />
        
        <CombinedDashboard stats={stats} />
        <Architecture />
        <JudgesSection />
      </main>
      <Footer />
    </div>
  )
}