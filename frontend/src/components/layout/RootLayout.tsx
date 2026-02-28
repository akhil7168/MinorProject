import { useState, type ReactNode } from 'react'
import Sidebar from './Sidebar'
import TopBar from './TopBar'

interface Props {
    children: ReactNode
}

export default function RootLayout({ children }: Props) {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

    return (
        <div style={{ display: 'flex', minHeight: '100vh', width: '100%' }}>
            <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
            <div style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                marginLeft: sidebarCollapsed ? 72 : 260,
                transition: 'margin-left 0.3s ease',
            }}>
                <TopBar />
                <main style={{ flex: 1, padding: 24, overflowY: 'auto' }}>
                    {children}
                </main>
            </div>
        </div>
    )
}
