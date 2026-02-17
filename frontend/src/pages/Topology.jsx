import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Server, Smartphone, Wifi, ShieldCheck, ShieldAlert, Cpu } from 'lucide-react';

const Topology = () => {
    const [networkData, setNetworkData] = useState({ devices: [], gateway: {} });

    useEffect(() => {
        fetchTopology();
        const interval = setInterval(fetchTopology, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchTopology = async () => {
        try {
            const response = await axios.get('http://localhost:8002/api/devices');
            setNetworkData(response.data);
        } catch (error) {
            console.error('Failed to fetch topology:', error);
        }
    };

    const getIcon = (type) => {
        switch (type) {
            case 'ESP32': return <Cpu className="w-8 h-8 text-blue-400" />;
            case 'Raspberry Pi': return <Server className="w-8 h-8 text-purple-400" />;
            case 'IP Camera': return <Smartphone className="w-8 h-8 text-yellow-400" />;
            case 'Smart Lock': return <ShieldCheck className="w-8 h-8 text-green-400" />;
            default: return <Wifi className="w-8 h-8 text-gray-400" />;
        }
    };

    return (
        <div className="max-w-7xl mx-auto">
            <h2 className="text-3xl font-bold mb-8">Network Topology</h2>

            <div className="flex flex-col items-center">

                {/* Router / Gateway */}
                <div className="relative mb-16">
                    <div className="bg-surface p-6 rounded-full border-4 border-primary w-32 h-32 flex items-center justify-center z-10 relative">
                        <Wifi className="w-16 h-16 text-white" />
                    </div>
                    <div className="text-center mt-4">
                        <h3 className="text-xl font-bold">{networkData.gateway.name || 'Gateway'}</h3>
                        <p className="text-gray-400">{networkData.gateway.ip}</p>
                    </div>

                    {/* Connection Lines (Vertical Stem) */}
                    <div className="absolute top-32 left-1/2 w-1 h-16 bg-gray-700 -translate-x-1/2"></div>
                </div>

                {/* Devices Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 w-full relative">

                    {/* Horizontal Connector Line */}
                    <div className="absolute -top-8 left-1/6 right-1/6 h-1 bg-gray-700 w-2/3 mx-auto"></div>

                    {networkData.devices.map((device, idx) => (
                        <div key={idx} className="relative flex flex-col items-center">
                            {/* Vertical Connector to Device */}
                            <div className="absolute -top-8 w-1 h-8 bg-gray-700"></div>

                            <div className={`bg-surface p-6 rounded-xl border-2 w-full transition-all duration-300 hover:scale-105 ${device.status === 'online' ? 'border-green-500 shadow-[0_0_15px_rgba(34,197,94,0.3)]' : 'border-red-500 opacity-70'}`}>
                                <div className="flex items-center gap-4">
                                    <div className="p-3 bg-background rounded-lg">
                                        {getIcon(device.type)}
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-lg">{device.name}</h4>
                                        <p className="text-sm text-gray-400">{device.type}</p>
                                        <p className="text-xs text-gray-500 font-mono mt-1">{device.ip}</p>
                                    </div>
                                    <div className={`ml-auto w-3 h-3 rounded-full ${device.status === 'online' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                                </div>
                                <div className="mt-4 pt-4 border-t border-gray-700 flex justify-between text-sm">
                                    <span className="text-gray-400">Status</span>
                                    <span className={device.status === 'online' ? 'text-green-400' : 'text-red-400'}>
                                        {device.status.toUpperCase()}
                                    </span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Topology;
