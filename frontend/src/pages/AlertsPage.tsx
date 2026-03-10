import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Filter, CheckCircle, XCircle, Eye, AlertTriangle,
    Clock,
} from 'lucide-react'
import { SEVERITY_COLORS, SEVERITY_BG } from '../lib/constants'
import api from '../lib/api'
import { timeAgo } from '../lib/utils'

interface Alert {
    id: string; severity: string; attack_type: string; src_ip: string;
    dst_ip: string; confidence: number; status: string; created_at: string;
    fingerprint: string; model_votes: any; shap_explanation: any[];
}

export default function AlertsPage() {
    const [alerts, setAlerts] = useState<Alert[]>([])
    const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)
    const [filterSeverity, setFilterSeverity] = useState<string>('all')
    const [filterStatus, setFilterStatus] = useState<string>('all')

    const fetchAlerts = async () => {
        try {
            const res = await api.get('/alerts')
            setAlerts(res.data.alerts || [])
        } catch { }
    }

    useEffect(() => {
        fetchAlerts()
        const interval = setInterval(fetchAlerts, 15000)
        return () => clearInterval(interval)
    }, [])

    const filteredAlerts = alerts.filter(a => {
        if (filterSeverity !== 'all' && a.severity !== filterSeverity) return false
        if (filterStatus !== 'all' && a.status !== filterStatus) return false
        return true
    })

    const acknowledgeAlert = async (id: string) => {
        try {
            await api.patch(`/alerts/${id}`, { status: 'acknowledged' })
            setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'acknowledged' } : a))
        } catch {
            setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'acknowledged' } : a))
        }
    }

    const resolveAlert = async (id: string) => {
        try {
            await api.patch(`/alerts/${id}`, { status: 'resolved' })
            setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'resolved' } : a))
        } catch {
            setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'resolved' } : a))
        }
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Summary */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                {['critical', 'high', 'medium', 'low'].map((sev) => {
                    const count = alerts.filter(a => a.severity === sev && a.status === 'open').length
                    return (
                        <motion.div key={sev} className="card" style={{ padding: 16 }}
                            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <div style={{ fontSize: 12, color: '#94A3B8', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 1 }}>{sev}</div>
                                    <div style={{ fontSize: 28, fontWeight: 800, color: SEVERITY_COLORS[sev] }}>{count}</div>
                                </div>
                                <div style={{ width: 40, height: 40, borderRadius: 10, background: SEVERITY_BG[sev], display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <AlertTriangle size={20} color={SEVERITY_COLORS[sev]} />
                                </div>
                            </div>
                        </motion.div>
                    )
                })}
            </div>

            {/* Filters */}
            <div className="card" style={{ padding: 16, display: 'flex', gap: 12, alignItems: 'center' }}>
                <Filter size={16} color="#94A3B8" />
                <select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)} style={{ fontSize: 13 }}>
                    <option value="all">All Severities</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                </select>
                <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)} style={{ fontSize: 13 }}>
                    <option value="all">All Status</option>
                    <option value="open">Open</option>
                    <option value="acknowledged">Acknowledged</option>
                    <option value="resolved">Resolved</option>
                </select>
                <span style={{ fontSize: 13, color: '#64748B', marginLeft: 'auto' }}>
                    {filteredAlerts.length} alerts
                </span>
            </div>

            {/* Alert Table */}
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                {filteredAlerts.length > 0 ? (
                    <table>
                        <thead>
                            <tr>
                                <th>Severity</th>
                                <th>Attack Type</th>
                                <th>Source IP</th>
                                <th>Destination IP</th>
                                <th>Confidence</th>
                                <th>Time</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredAlerts.map((alert) => (
                                <tr key={alert.id} style={{
                                    background: alert.severity === 'critical' && alert.status === 'open' ? 'rgba(239, 68, 68, 0.03)' : 'transparent',
                                }}>
                                    <td><span className={`badge badge-${alert.severity}`}>{alert.severity}</span></td>
                                    <td style={{ fontWeight: 500 }}>{alert.attack_type}</td>
                                    <td className="mono" style={{ fontSize: 13, color: '#94A3B8' }}>{alert.src_ip}</td>
                                    <td className="mono" style={{ fontSize: 13, color: '#94A3B8' }}>{alert.dst_ip}</td>
                                    <td>
                                        <span className="mono" style={{ fontSize: 13 }}>
                                            {(alert.confidence * 100).toFixed(0)}%
                                        </span>
                                    </td>
                                    <td style={{ fontSize: 12, color: '#64748B' }}>
                                        <Clock size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: '-1px' }} />
                                        {timeAgo(alert.created_at)}
                                    </td>
                                    <td>
                                        <span style={{
                                            fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5,
                                            color: alert.status === 'open' ? '#EF4444' : alert.status === 'acknowledged' ? '#EAB308' : '#22C55E',
                                        }}>
                                            {alert.status}
                                        </span>
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: 6 }}>
                                            <button onClick={() => setSelectedAlert(alert)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                                                <Eye size={14} color="#06B6D4" />
                                            </button>
                                            {alert.status === 'open' && (
                                                <button onClick={() => acknowledgeAlert(alert.id)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                                                    <CheckCircle size={14} color="#EAB308" />
                                                </button>
                                            )}
                                            {alert.status !== 'resolved' && (
                                                <button onClick={() => resolveAlert(alert.id)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                                                    <XCircle size={14} color="#22C55E" />
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : (
                    <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        padding: 48, color: '#64748B', fontSize: 14, gap: 8,
                    }}>
                        <AlertTriangle size={36} color="#334155" />
                        <span>No alerts yet. Alerts will appear here when the live capture detects attacks.</span>
                    </div>
                )}
            </div>

            {/* Alert Detail Drawer */}
            <AnimatePresence>
                {selectedAlert && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setSelectedAlert(null)}
                        style={{
                            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100,
                            display: 'flex', justifyContent: 'flex-end',
                        }}
                    >
                        <motion.div
                            initial={{ x: 400 }}
                            animate={{ x: 0 }}
                            exit={{ x: 400 }}
                            onClick={e => e.stopPropagation()}
                            style={{
                                width: 420, background: '#111827', borderLeft: '1px solid #1F2937',
                                padding: 24, overflowY: 'auto',
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                                <h3 style={{ fontSize: 18, fontWeight: 700 }}>Alert Details</h3>
                                <button onClick={() => setSelectedAlert(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94A3B8' }}>✕</button>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                <div>
                                    <span className={`badge badge-${selectedAlert.severity}`} style={{ marginBottom: 12 }}>
                                        {selectedAlert.severity}
                                    </span>
                                </div>
                                {[
                                    ['Attack Type', selectedAlert.attack_type],
                                    ['Source IP', selectedAlert.src_ip],
                                    ['Destination IP', selectedAlert.dst_ip],
                                    ['Confidence', `${(selectedAlert.confidence * 100).toFixed(1)}%`],
                                    ['Status', selectedAlert.status],
                                    ['Fingerprint', selectedAlert.fingerprint],
                                ].map(([label, value]) => (
                                    <div key={label}>
                                        <div style={{ fontSize: 12, color: '#94A3B8', marginBottom: 2 }}>{label}</div>
                                        <div style={{ fontWeight: 500, fontSize: 14 }}>{value}</div>
                                    </div>
                                ))}

                                {/* Model Votes */}
                                {selectedAlert.model_votes && Object.keys(selectedAlert.model_votes).length > 0 && (
                                    <div>
                                        <div style={{ fontSize: 12, color: '#94A3B8', marginBottom: 8 }}>Model Votes</div>
                                        {Object.entries(selectedAlert.model_votes).map(([model, vote]: any) => (
                                            <div key={model} style={{
                                                display: 'flex', justifyContent: 'space-between', padding: '6px 0',
                                                borderBottom: '1px solid #1F2937', fontSize: 13,
                                            }}>
                                                <span style={{ fontWeight: 500 }}>{model.toUpperCase()}</span>
                                                <span>{vote.class} ({(vote.confidence * 100).toFixed(0)}%)</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                                    {selectedAlert.status === 'open' && (
                                        <button className="btn-primary" style={{ flex: 1 }} onClick={() => { acknowledgeAlert(selectedAlert.id); setSelectedAlert(null) }}>
                                            Acknowledge
                                        </button>
                                    )}
                                    {selectedAlert.status !== 'resolved' && (
                                        <button className="btn-secondary" style={{ flex: 1 }} onClick={() => { resolveAlert(selectedAlert.id); setSelectedAlert(null) }}>
                                            Resolve
                                        </button>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
