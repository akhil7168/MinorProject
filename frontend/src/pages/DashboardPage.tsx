import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { Activity, ShieldAlert, Cpu, Bell, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react'
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend,
} from 'recharts'
import { formatNumber, timeAgo } from '../lib/utils'
import { ATTACK_COLORS } from '../lib/constants'
import api from '../lib/api'

interface DashboardStats {
    total_flows_24h: number
    total_attacks_24h: number
    attack_rate_percent: number
    active_models: number
    open_alerts: number
    critical_alerts: number
    model_ensemble_accuracy: number
}

interface TimelinePoint {
    hour: string
    total_flows: number
    attack_flows: number
}

interface AttackDistItem {
    type: string
    count: number
    color: string
}

interface AlertItem {
    id: string
    severity: string
    attack_type: string
    source_ip: string
    confidence: number
    created_at: string
}




export default function DashboardPage() {
    const [stats, setStats] = useState<DashboardStats>({
        total_flows_24h: 0,
        total_attacks_24h: 0,
        attack_rate_percent: 0,
        active_models: 0,
        open_alerts: 0,
        critical_alerts: 0,
        model_ensemble_accuracy: 0,
    })
    const [timeline, setTimeline] = useState<TimelinePoint[]>([])
    const [attacks, setAttacks] = useState<AttackDistItem[]>([])
    const [alerts, setAlerts] = useState<AlertItem[]>([])
    const [loading, setLoading] = useState(true)

    const fetchAll = useCallback(async () => {
        setLoading(true)
        try {
            const [statsRes, timelineRes, attacksRes, alertsRes] = await Promise.allSettled([
                api.get('/dashboard/stats'),
                api.get('/dashboard/timeline'),
                api.get('/dashboard/attacks'),
                api.get('/alerts', { params: { limit: 10 } }),
            ])

            if (statsRes.status === 'fulfilled') {
                setStats(statsRes.value.data)
            }

            if (timelineRes.status === 'fulfilled') {
                const tl = timelineRes.value.data
                setTimeline(Array.isArray(tl) ? tl : [])
            }

            if (attacksRes.status === 'fulfilled') {
                const dist = attacksRes.value.data?.distribution || []
                setAttacks(dist.map((d: any) => ({
                    ...d,
                    name: d.type,
                    value: d.count,
                    color: ATTACK_COLORS[d.type] || ATTACK_COLORS.Unknown || '#6B7280',
                })))
            }

            if (alertsRes.status === 'fulfilled') {
                const alertList = alertsRes.value.data?.alerts || []
                setAlerts(alertList.slice(0, 5))
            }
        } catch (err) {
            console.error('Dashboard fetch error:', err)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchAll()
        // Refresh every 15 seconds for real-time feel
        const interval = setInterval(fetchAll, 15000)
        return () => clearInterval(interval)
    }, [fetchAll])

    const statCards = [
        {
            label: 'Total Flows (24h)',
            value: formatNumber(stats.total_flows_24h),
            icon: Activity,
            color: '#06B6D4',
            trend: stats.total_flows_24h > 0 ? `${stats.attack_rate_percent}% attack rate` : 'No data yet',
            trendUp: stats.total_flows_24h > 0,
        },
        {
            label: 'Attacks Detected',
            value: formatNumber(stats.total_attacks_24h),
            icon: ShieldAlert,
            color: '#EF4444',
            trend: stats.total_attacks_24h > 0 ? `${stats.attack_rate_percent}%` : 'No attacks',
            trendUp: false,
        },
        {
            label: 'Active Models',
            value: stats.active_models.toString(),
            icon: Cpu,
            color: '#8B5CF6',
            trend: stats.model_ensemble_accuracy > 0
                ? `${(stats.model_ensemble_accuracy * 100).toFixed(1)}% acc`
                : 'No models loaded',
            trendUp: stats.active_models > 0,
        },
        {
            label: 'Open Alerts',
            value: stats.open_alerts.toString(),
            icon: Bell,
            color: '#F97316',
            trend: stats.critical_alerts > 0 ? `${stats.critical_alerts} critical` : 'No critical alerts',
            trendUp: false,
        },
    ]

    const hasTimeline = timeline.length > 0 && timeline.some(t => t.total_flows > 0 || t.attack_flows > 0)
    const hasAttacks = attacks.length > 0
    const hasAlerts = alerts.length > 0

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Stats Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
                {statCards.map((card, i) => (
                    <motion.div
                        key={card.label}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="card"
                        style={{ padding: 20 }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div>
                                <div style={{ fontSize: 13, color: '#94A3B8', marginBottom: 8, fontWeight: 500 }}>
                                    {card.label}
                                </div>
                                <div style={{ fontSize: 28, fontWeight: 800, color: '#F1F5F9' }}>
                                    {card.value}
                                </div>
                                <div style={{
                                    display: 'flex', alignItems: 'center', gap: 4, marginTop: 8,
                                    fontSize: 12, color: card.trendUp ? '#22C55E' : '#94A3B8',
                                }}>
                                    {card.trendUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                                    {card.trend}
                                </div>
                            </div>
                            <div style={{
                                width: 44, height: 44, borderRadius: 10,
                                background: `${card.color}15`, display: 'flex',
                                alignItems: 'center', justifyContent: 'center',
                            }}>
                                <card.icon size={22} color={card.color} />
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Charts Row */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
                {/* Traffic Timeline */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                    className="card"
                    style={{ padding: 20 }}
                >
                    <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#F1F5F9' }}>
                        Traffic Timeline (24h)
                    </h3>
                    {hasTimeline ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <AreaChart data={timeline}>
                                <defs>
                                    <linearGradient id="totalGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#06B6D4" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="attackGrad" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                                <XAxis dataKey="hour" stroke="#64748B" fontSize={11} />
                                <YAxis stroke="#64748B" fontSize={11} />
                                <Tooltip
                                    contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: 8, color: '#F1F5F9' }}
                                />
                                <Area type="monotone" dataKey="total_flows" stroke="#06B6D4" fill="url(#totalGrad)" strokeWidth={2} name="Total Flows" />
                                <Area type="monotone" dataKey="attack_flows" stroke="#EF4444" fill="url(#attackGrad)" strokeWidth={2} name="Attack Flows" />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            height: 280, color: '#64748B', fontSize: 14, flexDirection: 'column', gap: 8,
                        }}>
                            <Activity size={32} color="#334155" />
                            <span>No traffic data yet. Live capture will populate this chart.</span>
                        </div>
                    )}
                </motion.div>

                {/* Attack Distribution */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    className="card"
                    style={{ padding: 20 }}
                >
                    <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#F1F5F9' }}>
                        Attack Distribution
                    </h3>
                    {hasAttacks ? (
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie
                                    data={attacks}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={60}
                                    outerRadius={90}
                                    paddingAngle={3}
                                    dataKey="value"
                                    nameKey="name"
                                >
                                    {attacks.map((entry, idx) => (
                                        <Cell key={idx} fill={entry.color} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: 8, color: '#F1F5F9' }} />
                                <Legend wrapperStyle={{ fontSize: 12, color: '#94A3B8' }} />
                            </PieChart>
                        </ResponsiveContainer>
                    ) : (
                        <div style={{
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            height: 280, color: '#64748B', fontSize: 14, flexDirection: 'column', gap: 8,
                        }}>
                            <ShieldAlert size={32} color="#334155" />
                            <span>No attacks detected yet.</span>
                        </div>
                    )}
                </motion.div>
            </div>

            {/* Recent Alerts */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                className="card"
                style={{ padding: 20 }}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <h3 style={{ fontSize: 16, fontWeight: 600, color: '#F1F5F9' }}>
                        Recent Alerts
                    </h3>
                    <button
                        onClick={fetchAll}
                        disabled={loading}
                        style={{
                            background: 'transparent', border: '1px solid #334155', borderRadius: 6,
                            padding: '4px 10px', color: '#94A3B8', cursor: 'pointer',
                            display: 'flex', alignItems: 'center', gap: 4, fontSize: 12,
                        }}
                    >
                        <RefreshCw size={12} className={loading ? 'spin' : ''} />
                        Refresh
                    </button>
                </div>
                {hasAlerts ? (
                    <table>
                        <thead>
                            <tr>
                                <th>Severity</th>
                                <th>Attack Type</th>
                                <th>Source IP</th>
                                <th>Confidence</th>
                                <th>Time</th>
                            </tr>
                        </thead>
                        <tbody>
                            {alerts.map((alert) => (
                                <tr key={alert.id}>
                                    <td>
                                        <span className={`badge badge-${alert.severity}`}>
                                            {alert.severity}
                                        </span>
                                    </td>
                                    <td style={{ fontWeight: 500 }}>{alert.attack_type || '—'}</td>
                                    <td className="mono" style={{ color: '#94A3B8', fontSize: 13 }}>{alert.source_ip || '—'}</td>
                                    <td>
                                        <div style={{
                                            display: 'flex', alignItems: 'center', gap: 8,
                                        }}>
                                            <div style={{
                                                width: 60, height: 6, borderRadius: 3,
                                                background: '#1F2937',
                                            }}>
                                                <div style={{
                                                    width: `${(alert.confidence || 0) * 100}%`,
                                                    height: '100%',
                                                    borderRadius: 3,
                                                    background: (alert.confidence || 0) > 0.95 ? '#EF4444' : (alert.confidence || 0) > 0.9 ? '#F97316' : '#06B6D4',
                                                }} />
                                            </div>
                                            <span style={{ fontSize: 13, color: '#94A3B8' }}>
                                                {((alert.confidence || 0) * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    </td>
                                    <td style={{ fontSize: 13, color: '#64748B' }}>{timeAgo(alert.created_at)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <div style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        padding: 40, color: '#64748B', fontSize: 14, flexDirection: 'column', gap: 8,
                    }}>
                        <Bell size={32} color="#334155" />
                        <span>No alerts yet. Alerts will appear here when attacks are detected from live traffic.</span>
                    </div>
                )}
            </motion.div>
        </div>
    )
}
