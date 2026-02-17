import React, { useState } from 'react';
import axios from 'axios';
import { AlertTriangle, CheckCircle, Loader } from 'lucide-react';

const Detection = () => {
    const [inputData, setInputData] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handlePredict = async () => {
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            // Parse input data (assuming comma separated values)
            const features = inputData.split(',').map(item => parseFloat(item.trim()));

            if (features.some(isNaN)) {
                throw new Error("Invalid input: All values must be numbers.");
            }

            const response = await axios.post('http://localhost:8000/predict', { features });
            setResult(response.data);
        } catch (err) {
            setError(err.response?.data?.detail || err.message || "Failed to predict");
        } finally {
            setLoading(false);
        }
    };

    const loadSampleData = () => {
        // Sample data matching CICIDS2017 78 features
        // This vector represents a standard traffic pattern (normalized or raw depending on model expectation)
        // Since model uses a scaler, we can pass raw-looking values
        const sample = [
            80, 56321, 4, 3, 256, 120, 64, 0, 64, 20.2, // 1-10
            60, 0, 40, 15.5, 1000.5, 50.2, 10.5, 5.2, 20.1, 1.2, // 11-20
            100, 50, 10, 60, 0, 80, 40, 5, 50, 2, // 21-30
            0, 1, 0, 0, 32, 32, 100.2, 120.5, 64, 1500, // 31-40
            512.5, 200.2, 10050.5, 0, 1, 0, 0, 1, 0, 0, // 41-50
            0, 1, 150.2, 64, 64, 20, 100, 5, 20, 100, // 51-60
            5, 20, 4, 256, 3, 120, 65535, 65535, 2, 32, // 61-70
            0, 0, 0, 0, 0, 0, 0, 0 // 71-78
        ];

        // Ensure we have exactly 78 features
        // If the array is short, pad it; if long, slice it (just in case)
        const finalSample = sample.length === 78 ? sample : Array(78).fill(0).map((_, i) => sample[i] || 0);

        setInputData(finalSample.join(', '));
    };

    return (
        <div className="max-w-4xl mx-auto">
            <h2 className="text-3xl font-bold mb-8 flex items-center gap-3">
                <AlertTriangle className="text-yellow-500" />
                Intrusion Detection
            </h2>

            <div className="bg-surface p-8 rounded-xl border border-gray-700 mb-8">
                <label className="block text-gray-300 mb-2 font-medium">
                    Input Features (Comma Separated CSV Row)
                </label>
                <textarea
                    className="w-full bg-background border border-gray-600 rounded-lg p-4 text-gray-300 focus:outline-none focus:border-primary font-mono h-32"
                    placeholder="e.g. 0.0, 1.2, 55, ..."
                    value={inputData}
                    onChange={(e) => setInputData(e.target.value)}
                />

                <div className="flex justify-end gap-4 mt-4">
                    <button
                        onClick={loadSampleData}
                        className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                    >
                        Load Sample Data
                    </button>
                    <button
                        onClick={handlePredict}
                        disabled={loading || !inputData}
                        className="px-6 py-2 bg-primary hover:bg-sky-600 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-semibold transition-all flex items-center gap-2"
                    >
                        {loading && <Loader className="animate-spin w-4 h-4" />}
                        Analyze Traffic
                    </button>
                </div>
            </div>

            {error && (
                <div className="bg-red-500/10 border border-red-500 text-red-500 p-4 rounded-lg mb-8">
                    {error}
                </div>
            )}

            {result && (
                <div className={`p-8 rounded-xl border ${result.is_attack ? 'bg-red-900/20 border-red-500' : 'bg-green-900/20 border-green-500'} animate-fade-in`}>
                    <div className="flex items-center gap-4 mb-4">
                        {result.is_attack ? (
                            <AlertTriangle className="w-12 h-12 text-red-500" />
                        ) : (
                            <CheckCircle className="w-12 h-12 text-green-500" />
                        )}
                        <div>
                            <h3 className={`text-2xl font-bold ${result.is_attack ? 'text-red-400' : 'text-green-400'}`}>
                                {result.label} Detected
                            </h3>
                            <p className="text-gray-400">Confidence: {(result.confidence * 100).toFixed(2)}%</p>
                        </div>
                    </div>
                    <p className="text-gray-300">
                        The system has analyzed the network traffic pattern and determined it to be
                        <strong> {result.label}</strong>.
                    </p>
                </div>
            )}
        </div>
    );
};

export default Detection;
