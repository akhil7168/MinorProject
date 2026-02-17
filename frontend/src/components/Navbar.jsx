import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Activity, BarChart2, Info } from 'lucide-react';

const Navbar = () => {
    const location = useLocation();

    const isActive = (path) => {
        return location.pathname === path ? 'text-primary' : 'text-gray-400 hover:text-white';
    };

    return (
        <nav className="bg-surface border-b border-gray-700 py-4 sticky top-0 z-50">
            <div className="container mx-auto px-6 flex justify-between items-center">
                <Link to="/" className="flex items-center gap-2 text-2xl font-bold text-white">
                    <Shield className="w-8 h-8 text-primary" />
                    <span>IoT Guardian</span>
                </Link>

                <div className="flex gap-8">
                    <Link to="/" className={`flex items-center gap-2 transition-colors ${isActive('/')}`}>
                        <Activity className="w-5 h-5" />
                        Home
                    </Link>
                    <Link to="/detect" className={`flex items-center gap-2 transition-colors ${isActive('/detect')}`}>
                        <Shield className="w-5 h-5" />
                        Detect
                    </Link>
                    <Link to="/dashboard" className={`flex items-center gap-2 transition-colors ${isActive('/dashboard')}`}>
                        <BarChart2 className="w-5 h-5" />
                        Dashboard
                    </Link>
                    <Link to="/topology" className={`flex items-center gap-2 transition-colors ${isActive('/topology')}`}>
                        <Activity className="w-5 h-5" />
                        Topology
                    </Link>
                    <Link to="/analytics" className={`flex items-center gap-2 transition-colors ${isActive('/analytics')}`}>
                        <BarChart2 className="w-5 h-5" />
                        Analytics
                    </Link>
                    <Link to="/about" className={`flex items-center gap-2 transition-colors ${isActive('/about')}`}>
                        <Info className="w-5 h-5" />
                        About
                    </Link>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
