import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, ShieldAlert, Cpu, Bell, TrendingUp, TrendingDown } from 'lucide-react'
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend,
} from 'recharts'
import { formatNumber } from '../lib/utils'
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

// Demo data for timeline chart
const DEMO_TIMELINE = Array.from({ length: 24 }, (_, i) => ({
    hour: `${String(i).padStart(2, '0')}:00`,
    total: Math.floor(Math.random() * 5000 + 2000),
    attacks: Math.floor(Math.random() * 200 + 20),
}))

const DEMO_ATTACKS = [
    { name: 'DoS', value: 423, color: ATTACK_COLORS.DoS },
    { name: 'Probe', value: 287, color: ATTACK_COLORS.Probe },
    { name: 'R2L', value: 156, color: ATTACK_COLORS.R2L },
    { name: 'Botnet', value: 89, color: ATTACK_COLORS.Botnet },
    { name: 'WebAttack', value: 45, color: ATTACK_COLORS.WebAttack },
]

const DEMO_ALERTS = [
    { id: '1', severity: 'critical', type: 'DDoS Flood', src: '192.168.1.105', confidence: 0.97, time: '2m ago' },
    { id: '2', severity: 'high', type: 'Port Scan', src: '10.0.0.42', confidence: 0.91, time: '5m ago' },
    { id: '3', severity: 'medium', type: 'Brute Force', src: '172.16.0.88', confidence: 0.87, time: '12m ago' },
    { id: '4', severity: 'high', type: 'DoS SYN', src: '192.168.2.15', confidence: 0.93, time: '18m ago' },
    { id: '5', severity: 'low', type: 'Suspicious Scan', src: '10.0.1.100', confidence: 0.86, time: '25m ago' },
]

export default function DashboardPage() {
    const [stats, setStats] = useState<DashboardStats>({
        total_flows_24h: 142832,
        total_attacks_24h: 1243,
        attack_rate_percent: 0.87,
        active_models: 4,
        open_alerts: 23,
        critical_alerts: 3,
        model_ensemble_accuracy: 0.9743,
    })

    useEffect(() => {
        api.get('/dashboard/stats').then(res => setStats(res.data)).catch(() => { })
    }, [])

    const statCards = [
        {
            label: 'Total Flows (24h)',
            value: formatNumber(stats.total_flows_24h),
            icon: Activity,
            color: '#06B6D4',
            trend: '+12.3%',
            trendUp: true,
        },
        {
            label: 'Attacks Detected',
            value: formatNumber(stats.total_attacks_24h),
            icon: ShieldAlert,
            color: '#EF4444',
            trend: `${stats.attack_rate_percent}%`,
            trendUp: false,
        },
        {
            label: 'Active Models',
            value: stats.active_models.toString(),
            icon: Cpu,
            color: '#8B5CF6',
            trend: `${(stats.model_ensemble_accuracy * 100).toFixed(1)}% acc`,
            trendUp: true,
        },
        {
            label: 'Open Alerts',
            value: stats.open_alerts.toString(),
            icon: Bell,
            color: '#F97316',
            trend: `${stats.critical_alerts} critical`,
            trendUp: false,
        },
    ]

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
                                    fontSize: 12, color: card.trendUp ? '#22C55E' : '#EF4444',
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
                    <ResponsiveContainer width="100%" height={280}>
                        <AreaChart data={DEMO_TIMELINE}>
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
                            <Area type="monotone" dataKey="total" stroke="#06B6D4" fill="url(#totalGrad)" strokeWidth={2} name="Total Flows" />
                            <Area type="monotone" dataKey="attacks" stroke="#EF4444" fill="url(#attackGrad)" strokeWidth={2} name="Attack Flows" />
                        </AreaChart>
                    </ResponsiveContainer>
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
                    <ResponsiveContainer width="100%" height={280}>
                        <PieChart>
                            <Pie
                                data={DEMO_ATTACKS}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={90}
                                paddingAngle={3}
                                dataKey="value"
                            >
                                {DEMO_ATTACKS.map((entry, idx) => (
                                    <Cell key={idx} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: 8, color: '#F1F5F9' }} />
                            <Legend wrapperStyle={{ fontSize: 12, color: '#94A3B8' }} />
                        </PieChart>
                    </ResponsiveContainer>
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
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, color: '#F1F5F9' }}>
                    Recent Alerts
                </h3>
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
                        {DEMO_ALERTS.map((alert) => (
                            <tr key={alert.id}>
                                <td>
                                    <span className={`badge badge-${alert.severity}`}>
                                        {alert.severity}
                                    </span>
                                </td>
                                <td style={{ fontWeight: 500 }}>{alert.type}</td>
                                <td className="mono" style={{ color: '#94A3B8', fontSize: 13 }}>{alert.src}</td>
                                <td>
                                    <div style={{
                                        display: 'flex', alignItems: 'center', gap: 8,
                                    }}>
                                        <div style={{
                                            width: 60, height: 6, borderRadius: 3,
                                            background: '#1F2937',
                                        }}>
                                            <div style={{
                                                width: `${alert.confidence * 100}%`,
                                                height: '100%',
                                                borderRadius: 3,
                                                background: alert.confidence > 0.95 ? '#EF4444' : alert.confidence > 0.9 ? '#F97316' : '#06B6D4',
                                            }} />
                                        </div>
                                        <span style={{ fontSize: 13, color: '#94A3B8' }}>
                                            {(alert.confidence * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                </td>
                                <td style={{ fontSize: 13, color: '#64748B' }}>{alert.time}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </motion.div>
        </div>
    )
}
