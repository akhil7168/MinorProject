import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Line, Doughnut } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
} from 'chart.js';
import { Shield, AlertTriangle, Activity, Download, CheckCircle, Smartphone } from 'lucide-react';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    ArcElement
);

const Dashboard = () => {
    const [stats, setStats] = useState({
        total_predictions: 0,
        total_attacks: 0,
        detection_rate: 0,
        recent_attacks: 0,
        attack_types: {},
        threat_levels: {}
    });

    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    const [trafficData, setTrafficData] = useState({
        labels: [],
        datasets: [{
            label: 'Attack Confidence',
            data: [],
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.5)',
            tension: 0.4
        }]
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statsRes, historyRes] = await Promise.all([
                    axios.get('http://localhost:8002/api/stats'),
                    axios.get('http://localhost:8002/api/history')
                ]);

                setStats(statsRes.data);
                setHistory(historyRes.data.attacks);

                // Update Traffic Graph
                const labels = historyRes.data.attacks.slice(0, 20).reverse().map(a => new Date(a.timestamp).toLocaleTimeString());
                const data = historyRes.data.attacks.slice(0, 20).reverse().map(a => a.confidence);

                setTrafficData({
                    labels,
                    datasets: [{
                        label: 'Attack Confidence',
                        data,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.5)',
                        tension: 0.4
                    }]
                });

                setLoading(false);
            } catch (error) {
                console.error("Error fetching dashboard data", error);
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 3000); // Poll every 3 seconds
        return () => clearInterval(interval);
    }, []);

    const downloadReport = () => {
        window.open('http://localhost:8002/api/report', '_blank');
    };

    // Data for Attack Type Distribution (Pie Chart)
    const attackTypeData = {
        labels: Object.keys(stats.attack_types || {}),
        datasets: [{
            data: Object.values(stats.attack_types || {}),
            backgroundColor: ['#ef4444', '#f97316', '#eab308', '#84cc16', '#3b82f6'],
            borderWidth: 0
        }]
    };

    return (
        <div className="max-w-7xl mx-auto space-y-8">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold">Security Dashboard</h2>
                    <p className="text-gray-400">Real-time network monitoring and threat detection</p>
                </div>
                <button
                    onClick={downloadReport}
                    className="flex items-center gap-2 bg-primary hover:bg-primary/80 text-white px-4 py-2 rounded-lg transition-colors"
                >
                    <Download className="w-5 h-5" />
                    Download Report
                </button>
            </div>

            {/* Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard icon={<Activity />} title="Total Scans" value={stats.total_predictions} color="bg-blue-500/20 text-blue-500" />
                <StatCard icon={<AlertTriangle />} title="Threats Detected" value={stats.total_attacks} color="bg-red-500/20 text-red-500" />
                <StatCard icon={<Shield />} title="Detection Rate" value={`${stats.detection_rate}%`} color="bg-purple-500/20 text-purple-500" />
                <StatCard icon={<CheckCircle />} title="System Status" value="Online" color="bg-green-500/20 text-green-500" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Traffic Graph */}
                <div className="lg:col-span-2 bg-surface p-6 rounded-xl border border-gray-700 shadow-lg">
                    <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-primary" />
                        Live Attack Confidence Trend
                    </h3>
                    <div className="h-64">
                        <Line
                            data={trafficData}
                            options={{
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: {
                                    y: { beginAtZero: true, max: 1, grid: { color: '#374151' } },
                                    x: { grid: { display: false } }
                                },
                                plugins: { legend: { display: false } }
                            }}
                        />
                    </div>
                </div>

                {/* Attack Distribution */}
                <div className="bg-surface p-6 rounded-xl border border-gray-700 shadow-lg">
                    <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                        <Smartphone className="w-5 h-5 text-yellow-500" />
                        Attack Types
                    </h3>
                    <div className="h-48 flex items-center justify-center">
                        {Object.keys(stats.attack_types || {}).length > 0 ? (
                            <Doughnut
                                data={attackTypeData}
                                options={{
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    plugins: { legend: { position: 'right', labels: { color: '#fff', boxWidth: 10 } } }
                                }}
                            />
                        ) : (
                            <p className="text-gray-500">No attacks recorded yet</p>
                        )}
                    </div>
                </div>
            </div>

            {/* Recent Attacks List */}
            <div className="bg-surface p-6 rounded-xl border border-gray-700 shadow-lg">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-500" />
                    Recent Attack History
                </h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="text-gray-400 border-b border-gray-700">
                                <th className="p-3">Timestamp</th>
                                <th className="p-3">Type</th>
                                <th className="p-3">Confidence</th>
                                <th className="p-3">Threat Level</th>
                                <th className="p-3">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.length > 0 ? history.map((attack, index) => (
                                <tr key={index} className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                                    <td className="p-3 font-mono text-sm text-gray-300">
                                        {new Date(attack.timestamp).toLocaleTimeString()}
                                    </td>
                                    <td className="p-3 font-semibold text-yellow-400">{attack.attack_type || 'Generic Test'}</td>
                                    <td className="p-3">
                                        <div className="w-full bg-gray-700 rounded-full h-2.5 max-w-[100px]">
                                            <div
                                                className="bg-red-500 h-2.5 rounded-full"
                                                style={{ width: `${attack.confidence * 100}%` }}
                                            ></div>
                                        </div>
                                    </td>
                                    <td className="p-3">
                                        <span className={`px-2 py-1 rounded text-xs font-bold ${attack.threat_level === 'High' ? 'bg-red-500/20 text-red-400' :
                                            attack.threat_level === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                                                'bg-blue-500/20 text-blue-400'
                                            }`}>
                                            {attack.threat_level}
                                        </span>
                                    </td>
                                    <td className="p-3 text-red-400 flex items-center gap-1">
                                        <AlertTriangle className="w-4 h-4" /> Detected
                                    </td>
                                </tr>
                            )) : (
                                <tr>
                                    <td colSpan="5" className="p-8 text-center text-gray-500">
                                        No threats detected recently. System is secure.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ icon, title, value, color }) => (
    <div className="bg-surface p-6 rounded-xl border border-gray-700 shadow-lg flex items-center gap-4 hover:bg-surface/80 transition-colors">
        <div className={`p-4 rounded-lg ${color}`}>
            {React.cloneElement(icon, { className: "w-8 h-8" })}
        </div>
        <div>
            <p className="text-gray-400 text-sm">{title}</p>
            <h3 className="text-2xl font-bold">{value}</h3>
        </div>
    </div>
);

export default Dashboard;
