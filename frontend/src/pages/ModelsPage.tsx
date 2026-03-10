import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Boxes, Check, X, BarChart3, Zap, Download, Clock } from 'lucide-react'
import api from '../lib/api'
import { MODEL_TYPES } from '../lib/constants'

interface Model {
    id: string; name: string; model_type: string; is_active: boolean;
    accuracy: number; f1_macro: number; detection_rate: number; false_alarm_rate: number;
    size_mb: number; created_at: string; model_path: string;
}

export default function ModelsPage() {
    const [models, setModels] = useState<Model[]>([])

    useEffect(() => {
        api.get('/models').then(res => {
            setModels(res.data.models || [])
        }).catch(() => { })
    }, [])

    const toggleActive = async (id: string) => {
        try {
            const model = models.find(m => m.id === id)
            if (!model) return
            await api.patch(`/models/${id}`, { is_active: !model.is_active })
            setModels(prev => prev.map(m => m.id === id ? { ...m, is_active: !m.is_active } : m))
        } catch {
            setModels(prev => prev.map(m => m.id === id ? { ...m, is_active: !m.is_active } : m))
        }
    }

    const getModelInfo = (type: string) => MODEL_TYPES.find(m => m.id === type)

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ fontSize: 18, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Boxes size={20} />
                    Model Registry
                </h2>
                <span style={{ fontSize: 13, color: '#94A3B8' }}>
                    {models.filter(m => m.is_active).length} active / {models.length} total
                </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380, 1fr))', gap: 16 }}>
                {models.length > 0 ? models.map((model, i) => {
                    const info = getModelInfo(model.model_type)
                    return (
                        <motion.div
                            key={model.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="card"
                            style={{
                                padding: 20,
                                border: model.is_active ? '1px solid rgba(6, 182, 212, 0.3)' : undefined,
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <span style={{ fontSize: 28 }}>{info?.icon || '🧠'}</span>
                                    <div>
                                        <div style={{ fontWeight: 700, fontSize: 16 }}>{info?.name || model.model_type.toUpperCase()}</div>
                                        <div className="mono" style={{ fontSize: 12, color: '#64748B' }}>{model.name}</div>
                                    </div>
                                </div>
                                <button
                                    onClick={() => toggleActive(model.id)}
                                    style={{
                                        width: 42, height: 22, borderRadius: 11, border: 'none', cursor: 'pointer',
                                        background: model.is_active ? '#06B6D4' : '#374151',
                                        position: 'relative', transition: 'background 0.3s',
                                    }}
                                >
                                    <div style={{
                                        width: 18, height: 18, borderRadius: 9, background: 'white',
                                        position: 'absolute', top: 2,
                                        left: model.is_active ? 22 : 2,
                                        transition: 'left 0.3s',
                                    }} />
                                </button>
                            </div>

                            {/* Metrics Grid */}
                            <div style={{
                                display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10,
                                marginTop: 16, padding: 12, borderRadius: 8, background: 'rgba(0,0,0,0.2)',
                            }}>
                                {[
                                    { label: 'Accuracy', value: model.accuracy, icon: BarChart3 },
                                    { label: 'F1 Macro', value: model.f1_macro, icon: Zap },
                                    { label: 'Det. Rate', value: model.detection_rate, icon: Check },
                                    { label: 'FA Rate', value: model.false_alarm_rate, icon: X },
                                ].map(metric => (
                                    <div key={metric.label}>
                                        <div style={{ fontSize: 11, color: '#94A3B8', marginBottom: 2 }}>{metric.label}</div>
                                        <div style={{ fontSize: 16, fontWeight: 700, color: metric.label === 'FA Rate' ? '#EF4444' : '#06B6D4' }}>
                                            {(metric.value * 100).toFixed(1)}%
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 12, fontSize: 12, color: '#64748B' }}>
                                <span><Download size={12} style={{ display: 'inline', marginRight: 4 }} />{model.size_mb} MB</span>
                                <span><Clock size={12} style={{ display: 'inline', marginRight: 4 }} />{new Date(model.created_at).toLocaleDateString()}</span>
                            </div>
                        </motion.div>
                    )
                }) : (
                    <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                        padding: 48, color: '#64748B', fontSize: 14, gap: 8, gridColumn: '1 / -1',
                    }}>
                        <Boxes size={36} color="#334155" />
                        <span>No models registered yet. Train a model first to see it here.</span>
                    </div>
                )}
            </div>
        </div>
    )
}
