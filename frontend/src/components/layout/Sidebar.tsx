import { NavLink, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
    LayoutDashboard, Brain, Search, Bell, Boxes, Settings,
    ChevronLeft, ChevronRight, Shield
} from 'lucide-react'

interface Props {
    collapsed: boolean
    onToggle: () => void
}

const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/training', icon: Brain, label: 'Training' },
    { path: '/analysis', icon: Search, label: 'Analysis' },
    { path: '/alerts', icon: Bell, label: 'Alerts' },
    { path: '/models', icon: Boxes, label: 'Models' },
    { path: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar({ collapsed, onToggle }: Props) {
    const location = useLocation()

    return (
        <motion.aside
            animate={{ width: collapsed ? 72 : 260 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            style={{
                position: 'fixed',
                left: 0,
                top: 0,
                height: '100vh',
                background: 'linear-gradient(180deg, #0F172A 0%, #0A0F1C 100%)',
                borderRight: '1px solid rgba(6, 182, 212, 0.1)',
                display: 'flex',
                flexDirection: 'column',
                zIndex: 50,
                overflow: 'hidden',
            }}
        >
            {/* Logo */}
            <div style={{
                padding: '20px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                borderBottom: '1px solid rgba(6, 182, 212, 0.1)',
            }}>
                <div style={{
                    width: 40,
                    height: 40,
                    borderRadius: 10,
                    background: 'linear-gradient(135deg, #06B6D4, #0891B2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                }}>
                    <Shield size={22} color="white" />
                </div>
                {!collapsed && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.1 }}
                    >
                        <div style={{ fontWeight: 800, fontSize: 18 }} className="gradient-text">
                            DeepShield
                        </div>
                        <div style={{ fontSize: 11, color: '#64748B', fontWeight: 500 }}>
                            AI-Powered IDS
                        </div>
                    </motion.div>
                )}
            </div>

            {/* Navigation */}
            <nav style={{ flex: 1, padding: '16px 8px', display: 'flex', flexDirection: 'column', gap: 4 }}>
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path
                    const Icon = item.icon

                    return (
                        <NavLink
                            key={item.path}
                            to={item.path}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 12,
                                padding: collapsed ? '12px 0' : '10px 14px',
                                justifyContent: collapsed ? 'center' : 'flex-start',
                                borderRadius: 8,
                                textDecoration: 'none',
                                color: isActive ? '#06B6D4' : '#94A3B8',
                                background: isActive ? 'rgba(6, 182, 212, 0.1)' : 'transparent',
                                transition: 'all 0.2s ease',
                                fontWeight: isActive ? 600 : 400,
                                fontSize: 14,
                                position: 'relative',
                            }}
                        >
                            {isActive && (
                                <motion.div
                                    layoutId="nav-indicator"
                                    style={{
                                        position: 'absolute',
                                        left: 0,
                                        top: '50%',
                                        transform: 'translateY(-50%)',
                                        width: 3,
                                        height: 24,
                                        borderRadius: 4,
                                        background: '#06B6D4',
                                    }}
                                />
                            )}
                            <Icon size={20} />
                            {!collapsed && <span>{item.label}</span>}
                        </NavLink>
                    )
                })}
            </nav>

            {/* Collapse toggle */}
            <button
                onClick={onToggle}
                style={{
                    padding: 12,
                    borderTop: '1px solid rgba(6, 182, 212, 0.1)',
                    background: 'none',
                    border: 'none',
                    color: '#64748B',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'center',
                }}
            >
                {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
            </button>
        </motion.aside>
    )
}
