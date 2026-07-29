<div align="center">

# TraceNet
### Real-Time Temporal Graph Intelligence for Anti-Money Laundering

[![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-GNN-red?logo=pytorch)](https://pytorch.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph%20DB-008CC1?logo=neo4j)](https://neo4j.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Status](https://img.shields.io/badge/Status-In%20Development-yellow)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

> **TraceNet** uses Graph Neural Networks, an 11-Layer Detection Engine, and a locally hosted LLM to detect, block, and report cross-channel money mule rings in milliseconds.

</div>

---

## The Problem

Criminal rings exploit weaknesses in silo-based banking systems, laundering an estimated **$2 trillion annually**. They split transactions across Mobile Apps, ATMs, UPI, and Wire Transfers while routing funds through layers of shell companies in high-risk jurisdictions.

Traditional AML systems fail because:
- Blind spots between channels — no unified view across transaction rails
- Rule-based engines miss novel and adaptive laundering patterns
- Manual SAR (Suspicious Activity Report) generation is slow and error-prone
- Batch processing means detection happens hours or days too late

---

## Solution

TraceNet constructs a **unified temporal transaction graph** across all channels and applies Graph Neural Networks to detect, block, and report suspicious activity in real time.

```
Transaction Data (Multi-Channel)
        |
        v
+---------------------+
|  Temporal Graph      |  <- Neo4j Graph Database
|  Construction        |     Nodes: Accounts, Merchants
+----------+----------+     Edges: Transactions (timestamped)
           |
           v
+---------------------+
|  11-Layer Detection  |  <- GNN + Rule Engine
|  Engine              |     Velocity, Structuring, Loop,
+----------+----------+     Smurfing, Layering Detection
           |
           v
+---------------------+
|  Risk Scoring &      |  <- Real-time Blocking
|  Alert System        |     Threshold-based intervention
+----------+----------+
           |
           v
+---------------------+
|  LLM-Powered SAR     |  <- Local Qwen2.5 Model (Ollama)
|  Report Generator    |     Auto-generates regulatory reports
+---------------------+
```

---

## Features

| Feature | Description |
|---|---|
| **Unified Transaction Graph** | Aggregates data across UPI, ATM, Wire, Mobile into a single Neo4j graph |
| **Graph Neural Network Detection** | GNN-based anomaly detection trained on temporal transaction patterns |
| **Real-Time Processing** | Detects and blocks suspicious rings in milliseconds |
| **11-Layer Detection Engine** | Covers velocity checks, structuring, loop detection, smurfing, layering, and more |
| **Auto SAR Generation** | Locally hosted LLM (Qwen2.5 via Ollama) generates regulatory-ready reports |
| **Live Dashboard** | Streamlit-powered visualization of flagged transactions and ring networks |
| **REST API** | FastAPI backend for easy integration with existing banking systems |

---

## Architecture

```
+----------------------------------------------------------+
|                        TraceNet                          |
|                                                          |
|  +-------------+    +--------------+    +------------+  |
|  |  Data Layer |───>|  Graph Layer |───>|  AI Layer  |  |
|  |             |    |              |    |            |  |
|  | - Synthetic |    | - Neo4j DB   |    | - PyTorch  |  |
|  |   Generator |    | - Temporal   |    |   GNN      |  |
|  | - Multi-    |    |   Graph      |    | - 11-Layer |  |
|  |   channel   |    |   Builder    |    |   Engine   |  |
|  +-------------+    +--------------+    +-----+------+  |
|                                               |         |
|  +-------------+    +--------------+    +-----v------+  |
|  |  Report     |<---|  Alert &     |<---|  Risk      |  |
|  |  Layer      |    |  Block Layer |    |  Scoring   |  |
|  |             |    |              |    |            |  |
|  | - LLM SAR   |    | - Real-time  |    | - Threshold|  |
|  |   Generator |    |   Blocking   |    |   Engine   |  |
|  | - Qwen2.5   |    | - Alert API  |    | - Ring     |  |
|  |   (Ollama)  |    |              |    |   Detector |  |
|  +-------------+    +--------------+    +------------+  |
|                                                          |
|  +--------------------------------------------------+   |
|  |                Interface Layer                    |   |
|  |   FastAPI Backend  <---->  Streamlit Dashboard   |   |
|  +--------------------------------------------------+   |
+----------------------------------------------------------+
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Graph Database | Neo4j |
| GNN Framework | PyTorch + PyTorch Geometric |
| Backend API | FastAPI + Uvicorn |
| Frontend Dashboard | Streamlit |
| Local LLM | Qwen2.5:3b via Ollama |
| Data Processing | Python 3.10, Pandas, NumPy |
| Environment | Conda |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Conda
- CUDA-compatible GPU (recommended) or CPU
- [Ollama](https://ollama.com) installed
- Neo4j instance (local or cloud)

### 1. Clone the Repository
```bash
git clone https://github.com/Aviralsahu960/TraceNet.git
cd TraceNet
```

### 2. Set Up Environment
```bash
conda create -n tracenet python=3.10 -y
conda activate tracenet
pip install --upgrade pip

# For CUDA (recommended)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# For CPU only
pip install torch torchvision torchaudio

pip install torch-geometric
pip install -r requirements.txt
```

### 3. Pull the Local LLM
```bash
ollama pull qwen2.5:3b
```

### 4. Generate Synthetic Data
```bash
python scripts/get_real_data.py
```

### 5. Train the GNN Model
```bash
python scripts/train_model.py
```

### 6. Start the Backend API
```bash
# Terminal 1
conda activate tracenet
python -m uvicorn backend.api:app --reload
```

### 7. Launch the Dashboard
```bash
# Terminal 2
conda activate tracenet
streamlit run frontend/app.py
```

---

## Project Structure

```
TraceNet/
├── backend/
│   ├── api.py              # FastAPI routes
│   ├── detection_engine.py # 11-Layer detection logic
│   └── graph_builder.py    # Neo4j graph construction
├── frontend/
│   └── app.py              # Streamlit dashboard
├── models/
│   └── gnn_model.py        # PyTorch GNN architecture
├── scripts/
│   ├── get_real_data.py    # Synthetic data generator
│   └── train_model.py      # GNN training pipeline
├── reports/
│   └── sar_generator.py    # LLM-powered SAR report gen
├── requirements.txt
└── README.md
```

---

## Roadmap

- [x] Project architecture design
- [x] Synthetic data generation pipeline
- [x] GNN model training pipeline
- [x] FastAPI backend
- [x] Streamlit dashboard
- [ ] Neo4j integration (in progress)
- [ ] 11-Layer detection engine (in progress)
- [ ] LLM SAR report generation (in progress)
- [ ] Real-time blocking system
- [ ] Production deployment

---

## License

This project is licensed under the MIT License.

---

<div align="center">
  <b>TraceNet — Fighting Financial Crimes with Graph AI</b>
</div>
