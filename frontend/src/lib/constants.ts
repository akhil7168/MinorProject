export const ATTACK_COLORS: Record<string, string> = {
    BENIGN: '#22C55E',
    DoS: '#EF4444',
    DDoS: '#DC2626',
    Probe: '#F97316',
    PortScan: '#FB923C',
    R2L: '#A855F7',
    BruteForce: '#8B5CF6',
    Botnet: '#EC4899',
    WebAttack: '#EAB308',
    U2R: '#F43F5E',
    Unknown: '#6B7280',
}

export const SEVERITY_COLORS: Record<string, string> = {
    critical: '#EF4444',
    high: '#F97316',
    medium: '#EAB308',
    low: '#22C55E',
}

export const SEVERITY_BG: Record<string, string> = {
    critical: 'rgba(239, 68, 68, 0.15)',
    high: 'rgba(249, 115, 22, 0.15)',
    medium: 'rgba(234, 179, 8, 0.15)',
    low: 'rgba(34, 197, 94, 0.15)',
}

export const MODEL_TYPES = [
    { id: 'cnn', name: '1D CNN', icon: '🧠', desc: 'Fast local feature extraction' },
    { id: 'lstm', name: 'BiLSTM', icon: '🔄', desc: 'Temporal sequence modeling' },
    { id: 'autoencoder', name: 'Autoencoder', icon: '🔮', desc: 'Unsupervised anomaly detection' },
    { id: 'transformer', name: 'Transformer', icon: '⚡', desc: 'Attention-based patterns' },
    { id: 'hybrid', name: 'CNN+LSTM', icon: '🔗', desc: 'Best of both worlds' },
    { id: 'ensemble', name: 'Ensemble', icon: '🎯', desc: 'Maximum accuracy' },
]

export const CLASS_NAMES: Record<number, string> = {
    0: 'BENIGN', 1: 'DoS', 2: 'Probe', 3: 'R2L', 4: 'Botnet', 5: 'WebAttack',
}
