import React from 'react';
import { Shield, Cpu, Activity, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const Home = () => {
    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] text-center">
            <div className="mb-8 p-6 bg-surface rounded-full bg-opacity-50 animate-pulse">
                <Shield className="w-24 h-24 text-primary" />
            </div>

            <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                IoT Intrusion Detection System
            </h1>

            <p className="text-xl text-gray-400 max-w-2xl mb-12">
                Advanced AI-powered security for Internet of Things networks.
                Detect anomalies and potential attacks in real-time using Deep Learning.
            </p>

            <div className="flex gap-6 mb-16">
                <Link to="/detect" className="px-8 py-3 bg-primary hover:bg-sky-600 text-white rounded-lg font-semibold transition-all flex items-center gap-2">
                    Start Detection <ArrowRight className="w-5 h-5" />
                </Link>
                <Link to="/about" className="px-8 py-3 bg-surface hover:bg-slate-700 text-white rounded-lg font-semibold transition-all border border-gray-700">
                    Learn More
                </Link>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-5xl">
                <FeatureCard
                    icon={<Cpu className="w-10 h-10 text-secondary" />}
                    title="Deep Learning"
                    description="Utilizes Hybrid CNN-LSTM architecture for high-accuracy threat detection."
                />
                <FeatureCard
                    icon={<Activity className="w-10 h-10 text-green-400" />}
                    title="Real-time Analysis"
                    description="Process network traffic instantly and identify malicious patterns."
                />
                <FeatureCard
                    icon={<Shield className="w-10 h-10 text-purple-400" />}
                    title="Secure & Scalable"
                    description="Built on FastAPI and React, designed for modern IoT infrastructures."
                />
            </div>
        </div>
    );
};

const FeatureCard = ({ icon, title, description }) => (
    <div className="p-6 bg-surface rounded-xl border border-gray-700 hover:border-primary transition-all hover:transform hover:-translate-y-1">
        <div className="mb-4">{icon}</div>
        <h3 className="text-xl font-bold mb-2">{title}</h3>
        <p className="text-gray-400">{description}</p>
    </div>
);

export default Home;
