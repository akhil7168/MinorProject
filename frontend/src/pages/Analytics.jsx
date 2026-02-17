import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const Analytics = () => {
    const [modelInfo, setModelInfo] = useState(null);

    useEffect(() => {
        fetchModelInfo();
    }, []);

    const fetchModelInfo = async () => {
        try {
            const response = await axios.get('http://localhost:8002/api/model-info');
            setModelInfo(response.data);
        } catch (error) {
            console.error('Failed to fetch analytics:', error);
        }
    };

    if (!modelInfo) return <div className="p-8 text-center">Loading Analytics...</div>;

    const cmData = {
        labels: ['True Positive', 'True Negative', 'False Positive', 'False Negative'],
        datasets: [{
            data: [
                modelInfo.metrics.confusion_matrix.true_positive,
                modelInfo.metrics.confusion_matrix.true_negative,
                modelInfo.metrics.confusion_matrix.false_positive,
                modelInfo.metrics.confusion_matrix.false_negative
            ],
            backgroundColor: ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444'],
            borderWidth: 0
        }]
    };

    return (
        <div className="max-w-7xl mx-auto p-6">
            <h2 className="text-3xl font-bold mb-2">Model Analytics</h2>
            <p className="text-gray-400 mb-8">Performance metrics for {modelInfo.model_name}</p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8">
                <MetricCard title="Accuracy" value={modelInfo.metrics.accuracy} color="text-blue-400" />
                <MetricCard title="Precision" value={modelInfo.metrics.precision} color="text-green-400" />
                <MetricCard title="Recall" value={modelInfo.metrics.recall} color="text-purple-400" />
                <MetricCard title="F1 Score" value={modelInfo.metrics.f1_score} color="text-yellow-400" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                <div className="bg-surface p-6 rounded-xl border border-gray-700">
                    <h3 className="text-xl font-bold mb-6">Model Architecture</h3>
                    <div className="space-y-3">
                        {modelInfo.layers.map((layer, idx) => (
                            <div key={idx} className="flex items-center gap-4">
                                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-xs font-bold text-white">
                                    {idx + 1}
                                </div>
                                <div className="flex-1 bg-background p-3 rounded-lg border border-gray-700 flex justify-between items-center">
                                    <span className="font-semibold">{layer.name}</span>
                                    <span className="text-sm text-gray-400">
                                        {layer.filters ? `${layer.filters} filters` :
                                            layer.units ? `${layer.units} units` :
                                                layer.rate ? `Rate: ${layer.rate}` : ''}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="bg-surface p-6 rounded-xl border border-gray-700">
                    <h3 className="text-xl font-bold mb-4">Confusion Matrix</h3>
                    <div className="w-2/3 mx-auto h-64">
                        <Doughnut data={cmData} options={{ maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#fff' } } } }} />
                    </div>
                    <div className="mt-8 grid grid-cols-2 gap-4 text-center text-sm">
                        <div className="p-2 bg-green-900/20 rounded border border-green-900">TP: {modelInfo.metrics.confusion_matrix.true_positive}</div>
                        <div className="p-2 bg-blue-900/20 rounded border border-blue-900">TN: {modelInfo.metrics.confusion_matrix.true_negative}</div>
                        <div className="p-2 bg-yellow-900/20 rounded border border-yellow-900">FP: {modelInfo.metrics.confusion_matrix.false_positive}</div>
                        <div className="p-2 bg-red-900/20 rounded border border-red-900">FN: {modelInfo.metrics.confusion_matrix.false_negative}</div>
                    </div>
                </div>
            </div>

            <div className="bg-surface p-6 rounded-xl border border-gray-700">
                <h3 className="text-xl font-bold mb-4">Dataset Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <InfoItem label="Dataset Name" value={modelInfo.dataset} />
                    <InfoItem label="Input Features" value={modelInfo.input_features} />
                    <InfoItem label="Classes" value={modelInfo.classes.join(" / ")} />
                    <InfoItem label="Attack Types" value={modelInfo.attack_subtypes.join(", ")} />
                    <InfoItem label="Preprocessing" value={modelInfo.preprocessing} />
                </div>
            </div>
        </div>
    );
};

const MetricCard = ({ title, value, color }) => (
    <div className="bg-surface p-6 rounded-xl border border-gray-700 text-center">
        <p className="text-gray-400 mb-2 text-sm uppercase tracking-wider">{title}</p>
        <h3 className={`text-3xl font-bold ${color}`}>{(value * 100).toFixed(1)}%</h3>
    </div>
);

const InfoItem = ({ label, value }) => (
    <div className="bg-background border border-gray-700 p-4 rounded-lg">
        <p className="text-gray-500 text-xs uppercase tracking-wide mb-1">{label}</p>
        <p className="font-semibold text-white">{value}</p>
    </div>
);

export default Analytics;
