import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Download, Database, Brain, Play, Loader2, CheckCircle } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { MODEL_TYPES } from '../lib/constants'
import api from '../lib/api'

interface Dataset {
    id: string; name: string; display_name: string; description: string;
    status: string; download_progress: number; num_features: number; num_classes: number;
}

interface TrainingRun {
    id: string; model_type: string; status: string; current_epoch: number;
    total_epochs: number; metrics: any; training_history: any[];
}

export default function TrainingPage() {
    const [datasets, setDatasets] = useState<Dataset[]>([])
    const [selectedModel, setSelectedModel] = useState('cnn')
    const [selectedDataset, setSelectedDataset] = useState('')
    const [training, setTraining] = useState(false)
    const [trainingRun, setTrainingRun] = useState<TrainingRun | null>(null)
    const [config, setConfig] = useState({
        epochs: 50, batch_size: 256, learning_rate: 0.001,
        loss_fn: 'focal', balance_strategy: 'class_weight', mode: 'multiclass',
        dropout_rate: 0.3, window_size: 10,
    })

    useEffect(() => {
        api.get('/datasets').then(res => {
            setDatasets(res.data.datasets || [])
            if (res.data.datasets?.length) setSelectedDataset(res.data.datasets[0].id)
        }).catch(() => {
            // Demo datasets
            setDatasets([
                { id: '1', name: 'CICIDS-2017', display_name: 'CICIDS 2017', description: '2.8M flows, 78 features. Modern attacks.', status: 'ready', download_progress: 100, num_features: 78, num_classes: 6 },
                { id: '2', name: 'NSL-KDD', display_name: 'NSL-KDD', description: '148K records, 41 features.', status: 'not_downloaded', download_progress: 0, num_features: 41, num_classes: 5 },
                { id: '3', name: 'UNSW-NB15', display_name: 'UNSW-NB15', description: '2.5M records, 49 features.', status: 'not_downloaded', download_progress: 0, num_features: 49, num_classes: 10 },
            ])
            setSelectedDataset('1')
        })
    }, [])

    const startTraining = async () => {
        setTraining(true)
        try {
            const res = await api.post('/training/start', {
                model_type: selectedModel, dataset_id: selectedDataset, ...config,
            })
            const runId = res.data.training_run_id
            // Poll for progress
            const poll = setInterval(async () => {
                try {
                    const p = await api.get(`/training/${runId}/progress`)
                    setTrainingRun(p.data)
                    if (p.data.status === 'completed' || p.data.status === 'failed') {
                        clearInterval(poll)
                        setTraining(false)
                        if (p.data.status === 'failed') {
                            alert("Training failed: " + (p.data.error_message || "Unknown error"))
                        }
                    }
                } catch (err: any) {
                    clearInterval(poll);
                    setTraining(false);
                    console.error("Progress poll error:", err)
                }
            }, 2000)
        } catch (err: any) {
            setTraining(false)
            const msg = err.response?.data?.detail || err.message
            alert("Failed to start training: " + msg)
            console.error("Start training error:", err)
        }
    }

    const downloadDataset = async (name: string) => {
        try {
            await api.post(`/datasets/${name}/download`)
            // Refresh datasets
            const res = await api.get('/datasets')
            setDatasets(res.data.datasets || [])
        } catch { }
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            {/* Datasets */}
            <div>
                <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, color: '#F1F5F9' }}>
                    <Database size={20} style={{ display: 'inline', marginRight: 8, verticalAlign: '-4px' }} />
                    Datasets
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                    {datasets.map((ds, i) => (
                        <motion.div
                            key={ds.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="card"
                            style={{
                                padding: 16, cursor: 'pointer',
                                border: selectedDataset === ds.id ? '1px solid #06B6D4' : undefined,
                            }}
                            onClick={() => setSelectedDataset(ds.id)}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <h4 style={{ fontWeight: 600 }}>{ds.display_name}</h4>
                                {ds.status === 'ready' ? (
                                    <CheckCircle size={16} color="#22C55E" />
                                ) : ds.status === 'downloading' ? (
                                    <Loader2 size={16} color="#06B6D4" className="animate-spin" />
                                ) : (
                                    <button onClick={(e) => { e.stopPropagation(); downloadDataset(ds.name) }}
                                        style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                                        <Download size={16} color="#94A3B8" />
                                    </button>
                                )}
                            </div>
                            <p style={{ fontSize: 12, color: '#94A3B8', marginTop: 6 }}>{ds.description}</p>
                            <div style={{ display: 'flex', gap: 12, marginTop: 10, fontSize: 11, color: '#64748B' }}>
                                <span>{ds.num_features} features</span>
                                <span>{ds.num_classes} classes</span>
                            </div>
                            {ds.status === 'downloading' && (
                                <div style={{ marginTop: 8, height: 4, borderRadius: 2, background: '#1F2937' }}>
                                    <div style={{ width: `${ds.download_progress}%`, height: '100%', borderRadius: 2, background: '#06B6D4', transition: 'width 0.3s' }} />
                                </div>
                            )}
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* Model Selection */}
            <div>
                <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, color: '#F1F5F9' }}>
                    <Brain size={20} style={{ display: 'inline', marginRight: 8, verticalAlign: '-4px' }} />
                    Select Model
                </h2>
                <div style={{ display: 'flex', gap: 10, overflowX: 'auto', paddingBottom: 8 }}>
                    {MODEL_TYPES.map((model) => (
                        <motion.div
                            key={model.id}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            className="card"
                            style={{
                                padding: '14px 18px', cursor: 'pointer', minWidth: 150, flexShrink: 0,
                                border: selectedModel === model.id ? '1px solid #06B6D4' : undefined,
                                background: selectedModel === model.id ? 'rgba(6, 182, 212, 0.08)' : undefined,
                            }}
                            onClick={() => setSelectedModel(model.id)}
                        >
                            <div style={{ fontSize: 24, marginBottom: 6 }}>{model.icon}</div>
                            <div style={{ fontWeight: 600, fontSize: 14 }}>{model.name}</div>
                            <div style={{ fontSize: 11, color: '#94A3B8', marginTop: 4 }}>{model.desc}</div>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* Hyperparameters + Start Training */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div className="card" style={{ padding: 20 }}>
                    <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Hyperparameters</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                        {[
                            { label: 'Epochs', key: 'epochs', type: 'number' },
                            { label: 'Batch Size', key: 'batch_size', type: 'number' },
                            { label: 'Learning Rate', key: 'learning_rate', type: 'number' },
                            { label: 'Dropout', key: 'dropout_rate', type: 'number' },
                        ].map((field) => (
                            <div key={field.key}>
                                <label style={{ fontSize: 12, color: '#94A3B8', display: 'block', marginBottom: 4 }}>{field.label}</label>
                                <input
                                    type={field.type}
                                    value={(config as any)[field.key]}
                                    onChange={(e) => setConfig({ ...config, [field.key]: parseFloat(e.target.value) || 0 })}
                                    style={{ width: '100%' }}
                                    step={field.key === 'learning_rate' || field.key === 'dropout_rate' ? 0.001 : 1}
                                />
                            </div>
                        ))}
                        <div>
                            <label style={{ fontSize: 12, color: '#94A3B8', display: 'block', marginBottom: 4 }}>Loss Function</label>
                            <select value={config.loss_fn} onChange={(e) => setConfig({ ...config, loss_fn: e.target.value })} style={{ width: '100%' }}>
                                <option value="focal">Focal Loss</option>
                                <option value="weighted_ce">Weighted CE</option>
                                <option value="standard">Standard CE</option>
                            </select>
                        </div>
                        <div>
                            <label style={{ fontSize: 12, color: '#94A3B8', display: 'block', marginBottom: 4 }}>Balance Strategy</label>
                            <select value={config.balance_strategy} onChange={(e) => setConfig({ ...config, balance_strategy: e.target.value })} style={{ width: '100%' }}>
                                <option value="class_weight">Class Weights</option>
                                <option value="smote">SMOTE</option>
                                <option value="undersample">Undersample</option>
                            </select>
                        </div>
                    </div>

                    <button
                        className="btn-primary"
                        onClick={startTraining}
                        disabled={training}
                        style={{ marginTop: 20, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
                    >
                        {training ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                        {training ? 'Training...' : 'Start Training'}
                    </button>
                </div>

                {/* Training Progress */}
                <div className="card" style={{ padding: 20 }}>
                    <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Training Progress</h3>
                    {trainingRun?.training_history?.length ? (
                        <>
                            <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
                                <div className="badge badge-medium">
                                    Epoch {trainingRun.current_epoch}/{trainingRun.total_epochs}
                                </div>
                                <div className={`badge badge-${trainingRun.status === 'completed' ? 'low' : 'medium'}`}>
                                    {trainingRun.status}
                                </div>
                            </div>
                            <ResponsiveContainer width="100%" height={200}>
                                <LineChart data={trainingRun.training_history}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#1F2937" />
                                    <XAxis dataKey="epoch" stroke="#64748B" fontSize={11} />
                                    <YAxis stroke="#64748B" fontSize={11} />
                                    <Tooltip contentStyle={{ background: '#1F2937', border: '1px solid #374151', borderRadius: 8, color: '#F1F5F9' }} />
                                    <Legend wrapperStyle={{ fontSize: 12 }} />
                                    <Line type="monotone" dataKey="loss" stroke="#EF4444" strokeWidth={2} dot={false} name="Loss" />
                                    <Line type="monotone" dataKey="val_loss" stroke="#F97316" strokeWidth={2} dot={false} name="Val Loss" />
                                    <Line type="monotone" dataKey="accuracy" stroke="#06B6D4" strokeWidth={2} dot={false} name="Accuracy" />
                                </LineChart>
                            </ResponsiveContainer>
                        </>
                    ) : (
                        <div style={{
                            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                            height: 200, color: '#64748B', fontSize: 14,
                        }}>
                            <Brain size={40} style={{ marginBottom: 12, opacity: 0.3 }} />
                            <div>Start training to see progress here</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
