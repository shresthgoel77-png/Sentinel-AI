import { useState, useCallback } from 'react'
import StatusBar from './components/StatusBar'
import Hero from './components/Hero'
import DataLeakDemo from './components/DataLeakDemo'
import JailbreakDemo from './components/JailbreakDemo'
import CombinedDashboard from './components/CombinedDashboard'
import AttackSimulation from './components/AttackSimulation'
import Architecture from './components/Architecture'
import JudgesSection from './components/JudgesSection'
import Footer from './components/Footer'
import type { ShieldStats, Verdict } from './lib/types'

const INITIAL_STATS: ShieldStats = {
  dataLeaksBlocked: 0,
  jailbreaksDetected: 0,
  safeRequests: 0,
}

export default function App() {
  const [stats, setStats] = useState<ShieldStats>(INITIAL_STATS)

  const handleDataLeakResult = useCallback((verdict: Verdict) => {
    setStats((prev) => ({
      ...prev,
      dataLeaksBlocked: prev.dataLeaksBlocked + (verdict === 'threat' ? 1 : 0),
      safeRequests: prev.safeRequests + (verdict === 'safe' ? 1 : 0),
    }))
  }, [])

  const handleJailbreakResult = useCallback((verdict: Verdict) => {
    setStats((prev) => ({
      ...prev,
      jailbreaksDetected: prev.jailbreaksDetected + (verdict === 'threat' ? 1 : 0),
      safeRequests: prev.safeRequests + (verdict === 'safe' ? 1 : 0),
    }))
  }, [])

  return (
    <div className="min-h-screen">
      <StatusBar stats={stats} />
      <main>
        <Hero />
        <DataLeakDemo onResult={handleDataLeakResult} />
        <JailbreakDemo onResult={handleJailbreakResult} />
        <CombinedDashboard stats={stats} />
        <AttackSimulation />
        <Architecture />
        <JudgesSection />
      </main>
      <Footer />
    </div>
  )
}
