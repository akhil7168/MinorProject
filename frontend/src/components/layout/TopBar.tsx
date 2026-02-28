import { useLocation } from 'react-router-dom'
import { Wifi, WifiOff } from 'lucide-react'
import { useState, useEffect } from 'react'

const PAGE_TITLES: Record<string, string> = {
    '/': 'Dashboard',
    '/training': 'Model Training',
    '/analysis': 'Traffic Analysis',
    '/alerts': 'Alert Management',
    '/models': 'Model Registry',
    '/settings': 'Settings',
}

export default function TopBar() {
    const location = useLocation()
    const [connected, setConnected] = useState(true)
    const title = PAGE_TITLES[location.pathname] || 'DeepShield'

    useEffect(() => {
        // Check backend health periodically
        const check = async () => {
            try {
                const res = await fetch('/health')
                setConnected(res.ok)
            } catch { setConnected(false) }
        }
        check()
        const interval = setInterval(check, 30000)
        return () => clearInterval(interval)
    }, [])

    return (
        <header style={{
            height: 64,
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(31, 41, 55, 0.6)',
            background: 'rgba(10, 15, 28, 0.8)',
            backdropFilter: 'blur(10px)',
            position: 'sticky',
            top: 0,
            zIndex: 40,
        }}>
            <div>
                <h1 style={{ fontSize: 20, fontWeight: 700, color: '#F1F5F9' }}>
                    {title}
                </h1>
                <div style={{ fontSize: 12, color: '#64748B', marginTop: 2 }}>
                    AI-Powered Network Intrusion Detection
                </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                {/* Connection status */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '6px 12px',
                    borderRadius: 8,
                    background: connected ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    border: `1px solid ${connected ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`,
                }}>
                    {connected ? <Wifi size={14} color="#22C55E" /> : <WifiOff size={14} color="#EF4444" />}
                    <span style={{
                        fontSize: 12,
                        fontWeight: 500,
                        color: connected ? '#22C55E' : '#EF4444',
                    }}>
                        {connected ? 'Connected' : 'Offline'}
                    </span>
                </div>
            </div>
        </header>
    )
}
