import React from 'react';

const About = () => {
    return (
        <div className="max-w-4xl mx-auto bg-surface p-8 rounded-xl border border-gray-700">
            <h2 className="text-3xl font-bold mb-6">About the Project</h2>

            <div className="space-y-6 text-gray-300">
                <p>
                    The <strong>IoT Intrusion Detection System (IDS)</strong> is a cutting-edge security solution designed
                    to protect Internet of Things (IoT) networks from cyber threats. Utilizing deep learning algorithms,
                    specifically a hybrid <strong>CNN-LSTM architecture</strong>, the system analyzes network traffic patterns
                    to identify anomalies and malicious activities in real-time.
                </p>

                <h3 className="text-xl font-bold text-white mt-4">Key Features</h3>
                <ul className="list-disc pl-6 space-y-2">
                    <li>Real-time traffic analysis and classification.</li>
                    <li>High accuracy detection using Deep Learning (CNN + LSTM).</li>
                    <li>Comprehensive dashboard for network monitoring.</li>
                    <li>Scalable architecture using FastAPI and React.</li>
                </ul>

                <h3 className="text-xl font-bold text-white mt-4">Technology Stack</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-2">
                    <TechItem name="Python" />
                    <TechItem name="TensorFlow / Keras" />
                    <TechItem name="FastAPI" />
                    <TechItem name="React.js" />
                    <TechItem name="Tailwind CSS" />
                    <TechItem name="Docker" />
                </div>

                <h3 className="text-xl font-bold text-white mt-4">Dataset</h3>
                <p>
                    The model is trained on the <a href="https://www.unb.ca/cic/datasets/ids-2017.html" target="_blank" rel="noreferrer" className="text-primary hover:underline">CICIDS2017</a> dataset,
                    a comprehensive benchmark dataset that includes benign and the most common attacks,
                    resembling true real-world data (PCAPs).
                </p>
            </div>
        </div>
    );
};

const TechItem = ({ name }) => (
    <div className="bg-background px-4 py-2 rounded-lg border border-gray-600 text-center text-sm font-medium">
        {name}
    </div>
);

export default About;
