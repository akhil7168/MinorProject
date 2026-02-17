import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Detection from './pages/Detection';
import Dashboard from './pages/Dashboard';
import Topology from './pages/Topology';
import Analytics from './pages/Analytics';
import About from './pages/About';

function App() {
    return (
        <Router>
            <div className="min-h-screen bg-background text-white font-sans">
                <Navbar />
                <div className="container mx-auto px-4 py-8">
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/detect" element={<Detection />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/topology" element={<Topology />} />
                        <Route path="/analytics" element={<Analytics />} />
                        <Route path="/about" element={<About />} />
                    </Routes>
                </div>
            </div>
        </Router>
    );
}

export default App;
