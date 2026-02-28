import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import {
    Upload, FileSearch, Shield, AlertTriangle, CheckCircle, Loader2, BarChart3,
} from 'lucide-react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { ATTACK_COLORS } from '../lib/constants'
import api from '../lib/api'

interface AnalysisResult {
    session: any
    detections: any[]
    attack_breakdown: Record<string, number>
}

export default function AnalysisPage() {
    const [file, setFile] = useState<File | null>(null)
    const [uploading, setUploading] = useState(false)
    const [progress, setProgress] = useState(0)
    const [result, setResult] = useState<AnalysisResult | null>(null)

    const onDrop = useCallback((accepted: File[]) => {
        if (accepted.length) setFile(accepted[0])
    }, [])

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/csv': ['.csv'],
            'application/vnd.tcpdump.pcap': ['.pcap', '.pcapng'],
        },
        maxFiles: 1,
    })

    const analyzeFile = async () => {
        if (!file) return
        setUploading(true)
        setProgress(10)

        try {
            const formData = new FormData()
            formData.append('file', file)
            formData.append('models', 'ensemble')

            setProgress(30)
            const res = await api.post('/analyze/file', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            })
            // session_id available in res.data.session_id
            setProgress(60)

            // Poll for results
            const poll = setInterval(async () => {
                try {
                    const r = await api.get(`/analyze/${res.data.session_id}/results`)
                    if (r.data.session?.status === 'completed' || r.data.session?.status === 'failed') {
                        clearInterval(poll)
                        setResult(r.data)
                        setProgress(100)
                        setUploading(false)
                    }
                } catch {
                    clearInterval(poll)
                    setUploading(false)
                }
            }, 2000)
        } catch {
            setUploading(false)
            setProgress(0)
        }
    }

    const breakdownData = result ? Object.entries(result.attack_breakdown).map(([name, count]) => ({
        name, count, color: ATTACK_COLORS[name] || '#6B7280',
    })) : []

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* File Upload */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="card"
                style={{ padding: 24 }}
            >
                <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, color: '#F1F5F9' }}>
                    <FileSearch size={20} style={{ display: 'inline', marginRight: 8, verticalAlign: '-4px' }} />
                    Analyze Network Traffic
                </h2>

                <div
                    {...getRootProps()}
                    style={{
                        border: `2px dashed ${isDragActive ? '#06B6D4' : '#374151'}`,
                        borderRadius: 12,
                        padding: '48px 24px',
                        textAlign: 'center',
                        cursor: 'pointer',
                        background: isDragActive ? 'rgba(6, 182, 212, 0.05)' : 'rgba(17, 24, 39, 0.5)',
                        transition: 'all 0.3s ease',
                    }}
                >
                    <input {...getInputProps()} />
                    <Upload size={40} color={isDragActive ? '#06B6D4' : '#64748B'} style={{ margin: '0 auto 16px' }} />

                    {file ? (
                        <div>
                            <div style={{ fontWeight: 600, color: '#F1F5F9', fontSize: 16 }}>{file.name}</div>
                            <div style={{ fontSize: 13, color: '#94A3B8', marginTop: 4 }}>
                                {(file.size / 1024 / 1024).toFixed(2)} MB
                            </div>
                        </div>
                    ) : (
                        <div>
                            <div style={{ fontWeight: 600, color: '#F1F5F9', fontSize: 16 }}>
                                Drop PCAP or CSV file here
                            </div>
                            <div style={{ fontSize: 13, color: '#64748B', marginTop: 4 }}>
                                Supports .pcap, .pcapng, .csv files
                            </div>
                        </div>
                    )}
                </div>

                {file && (
                    <div style={{ marginTop: 16, display: 'flex', gap: 12, alignItems: 'center' }}>
                        <button className="btn-primary" onClick={analyzeFile} disabled={uploading}
                            style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            {uploading ? <Loader2 size={16} className="animate-spin" /> : <Shield size={16} />}
                            {uploading ? 'Analyzing...' : 'Analyze with Ensemble'}
                        </button>
                        {uploading && (
                            <div style={{ flex: 1, height: 6, borderRadius: 3, background: '#1F2937' }}>
                                <motion.div
                                    animate={{ width: `${progress}%` }}
                                    style={{ height: '100%', borderRadius: 3, background: '#06B6D4' }}
                                />
                            </div>
                        )}
                    </div>
                )}
            </motion.div>

            {/* Results */}
            {result && (
                <>
                    {/* Summary Stats */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                        {[
                            { label: 'Total Flows', value: result.session?.total_flows || 0, icon: BarChart3, color: '#06B6D4' },
                            { label: 'Benign', value: result.session?.benign_count || 0, icon: CheckCircle, color: '#22C55E' },
                            { label: 'Attacks', value: result.session?.attack_count || 0, icon: AlertTriangle, color: '#EF4444' },
                            { label: 'Duration', value: `${result.session?.duration_seconds || 0}s`, icon: FileSearch, color: '#8B5CF6' },
                        ].map((stat, i) => (
                            <motion.div key={stat.label} className="card" style={{ padding: 16 }}
                                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
                                <stat.icon size={20} color={stat.color} />
                                <div style={{ fontSize: 24, fontWeight: 800, marginTop: 8 }}>{stat.value}</div>
                                <div style={{ fontSize: 12, color: '#94A3B8' }}>{stat.label}</div>
                            </motion.div>
                        ))}
                    </div>

                    {/* Attack Breakdown Chart */}
                    {breakdownData.length > 0 && (
                        <motion.div className="card" style={{ padding: 20 }}
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
                            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Attack Breakdown</h3>
                            <ResponsiveContainer width="100%" height={250}>
                                <BarChart data={breakdownData} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                                    <XAxis type="number" stroke="#64748B" fontSize={11} />
                                    <YAxis type="category" dataKey="name" stroke="#64748B" fontSize={12} width={100} />
                                    <Tooltip contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: 8, color: '#F1F5F9' }} />
                                    <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                                        {breakdownData.map((d, i) => (
                                            <Cell key={i} fill={d.color} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </motion.div>
                    )}

                    {/* Flow Results Table */}
                    <motion.div className="card" style={{ padding: 20 }}
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }}>
                        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Flow Detections</h3>
                        <div style={{ overflowX: 'auto' }}>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Predicted Class</th>
                                        <th>Confidence</th>
                                        <th>Model Votes</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(result.detections || []).slice(0, 50).map((d: any, i: number) => (
                                        <tr key={i} style={{
                                            background: d.predicted_class !== 'BENIGN' ? 'rgba(239, 68, 68, 0.03)' : 'transparent',
                                        }}>
                                            <td>
                                                <span style={{
                                                    display: 'inline-flex', alignItems: 'center', gap: 6,
                                                    padding: '2px 10px', borderRadius: 9999, fontSize: 12, fontWeight: 600,
                                                    background: `${ATTACK_COLORS[d.predicted_class] || '#6B7280'}15`,
                                                    color: ATTACK_COLORS[d.predicted_class] || '#6B7280',
                                                    border: `1px solid ${ATTACK_COLORS[d.predicted_class] || '#6B7280'}30`,
                                                }}>
                                                    {d.predicted_class}
                                                </span>
                                            </td>
                                            <td>
                                                <span className="mono" style={{ fontSize: 13 }}>
                                                    {((d.confidence || 0) * 100).toFixed(1)}%
                                                </span>
                                            </td>
                                            <td style={{ fontSize: 12, color: '#94A3B8' }}>
                                                {d.model_votes ? Object.entries(d.model_votes).map(([m, v]: any) => (
                                                    <span key={m} style={{ marginRight: 8 }}>{m}: {((v?.confidence || 0) * 100).toFixed(0)}%</span>
                                                )) : '—'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </motion.div>
                </>
            )}
        </div>
    )
}
