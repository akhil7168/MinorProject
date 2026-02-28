import { useState } from 'react'
import { motion } from 'framer-motion'
import { Save, Database, Bell, Brain, Shield } from 'lucide-react'

export default function SettingsPage() {
    const [settings, setSettings] = useState({
        supabase_url: '',
        supabase_key: '',
        redis_url: 'redis://localhost:6379',
        alert_threshold: 0.85,
        alert_dedupe_window: 60,
        default_model: 'ensemble',
        auto_retrain: false,
        pcap_interface: '',
        log_level: 'INFO',
        training_epochs: 50,
        batch_size: 256,
    })

    const [saved, setSaved] = useState(false)

    const saveSettings = () => {
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
    }

    const sections = [
        {
            title: 'Database',
            icon: Database,
            fields: [
                { label: 'Supabase URL', key: 'supabase_url', type: 'text', placeholder: 'https://your-project.supabase.co' },
                { label: 'Supabase Key', key: 'supabase_key', type: 'password', placeholder: 'your-service-key' },
                { label: 'Redis URL', key: 'redis_url', type: 'text' },
            ],
        },
        {
            title: 'Alert Settings',
            icon: Bell,
            fields: [
                { label: 'Alert Threshold', key: 'alert_threshold', type: 'number', step: 0.01 },
                { label: 'Dedup Window (sec)', key: 'alert_dedupe_window', type: 'number', step: 1 },
            ],
        },
        {
            title: 'Model Settings',
            icon: Brain,
            fields: [
                { label: 'Default Model', key: 'default_model', type: 'select', options: ['ensemble', 'cnn', 'lstm', 'autoencoder', 'transformer', 'hybrid'] },
                { label: 'Default Training Epochs', key: 'training_epochs', type: 'number' },
                { label: 'Default Batch Size', key: 'batch_size', type: 'number' },
            ],
        },
        {
            title: 'Capture',
            icon: Shield,
            fields: [
                { label: 'Network Interface', key: 'pcap_interface', type: 'text', placeholder: 'eth0' },
                { label: 'Log Level', key: 'log_level', type: 'select', options: ['DEBUG', 'INFO', 'WARNING', 'ERROR'] },
            ],
        },
    ]

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 700 }}>
            {sections.map((section, i) => (
                <motion.div
                    key={section.title}
                    className="card"
                    style={{ padding: 20 }}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                >
                    <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                        <section.icon size={18} color="#06B6D4" />
                        {section.title}
                    </h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        {section.fields.map((field: any) => (
                            <div key={field.key}>
                                <label style={{ fontSize: 12, color: '#94A3B8', display: 'block', marginBottom: 4 }}>{field.label}</label>
                                {field.type === 'select' ? (
                                    <select
                                        value={(settings as any)[field.key]}
                                        onChange={(e) => setSettings({ ...settings, [field.key]: e.target.value })}
                                        style={{ width: '100%' }}
                                    >
                                        {field.options.map((opt: string) => (
                                            <option key={opt} value={opt}>{opt}</option>
                                        ))}
                                    </select>
                                ) : (
                                    <input
                                        type={field.type}
                                        value={(settings as any)[field.key]}
                                        onChange={(e) => setSettings({ ...settings, [field.key]: field.type === 'number' ? parseFloat(e.target.value) : e.target.value })}
                                        placeholder={field.placeholder}
                                        step={field.step}
                                        style={{ width: '100%' }}
                                    />
                                )}
                            </div>
                        ))}
                    </div>
                </motion.div>
            ))}

            <button className="btn-primary" onClick={saveSettings}
                style={{ display: 'flex', alignItems: 'center', gap: 8, alignSelf: 'flex-start' }}>
                <Save size={16} />
                {saved ? '✓ Saved!' : 'Save Settings'}
            </button>
        </div>
    )
}
