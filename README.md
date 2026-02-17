# IoT Intrusion Detection System (IDS)

A Deep Learning-based Intrusion Detection System for IoT Networks using the CICIDS2017 dataset. This project features a Hybrid CNN-LSTM model, a FastAPI backend, and a React-based dashboard.

## 🚀 Features
- **Deep Learning Model**: Hybrid CNN + LSTM for high-accuracy attack detection.
- **Real-time Analysis**: FASTAPI backend for low-latency predictions.
- **Interactive Dashboard**: React frontend to visualize traffic and threats.
- **Containerized**: Docker support for easy deployment.

## 📂 Project Structure
```
├── backend/            # FastAPI Backend
├── frontend/           # React Frontend
├── ml_engine/          # Machine Learning Scripts (Data Loader, Model, Training)
├── docker-compose.yml  # Container Orchestration
└── requirements.txt    # Python Dependencies
```

## 🛠️ Prerequisites
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose (optional, for containerization)
- CICIDS2017 Dataset (CSV format)

## 🏁 Getting Started

### 1. Data Preparation
1.  Download the **CICIDS2017** dataset (CSVs).
2.  Place the CSV files in `ml_engine/data/`.
3.  (Optional) Run training locally:
    ```bash
    cd ml_engine
    python train.py
    ```
    *Note: This will save `best_model.h5` and `scaler.pkl` to `ml_engine/saved_model/`.*

### 2. Running Locally (Manual)

#### Backend
```bash
cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload
```
API will be running at `http://localhost:8000`.

#### Frontend
```bash
cd frontend
npm install
npm run dev
```
Dashboard will be accessible at `http://localhost:5173`.

### 3. Running with Docker
Ensure you have placed the dataset in `ml_engine/data/` if you want to retrain, or ensure the `saved_model` folder exists inside `ml_engine`.

```bash
docker-compose up --build
```
- **Frontend**: `http://localhost:80`
- **Backend**: `http://localhost:8000`

## 🧪 Testing the API
You can use the **Detection** page on the frontend or `curl`:

```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{"features": [0.0, 1.2, ...]}'
```

## 📚 Documentation
- **Model Architecture**: 1D-CNN layers for feature extraction followed by LSTM for sequence dependency learning.
- **Dataset**: CICIDS2017 (Canadian Institute for Cybersecurity).
