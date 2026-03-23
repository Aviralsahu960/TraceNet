<div align="center">

# 🛡️ TraceNet

### Real-Time Cross-Channel Money Mule Detection Platform

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-Geometric-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)

TraceNet is a cutting-edge Anti-Money Laundering (AML) platform that leverages **Graph Neural Networks**, an **11-Layer Detection Engine**, and **locally hosted LLM-powered SAR Reports** to monitor, intercept, and prevent cross-channel money laundering activities in real time.

[✨ Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start-guide) • [Results](#-results)

---

</div>

## 🚨 Problem Statement

Criminal rings exploit weaknesses in silo-based banking systems, laundering $2 trillion annually. They split transactions across Mobile Apps, ATMs, UPI, and Wire Transfers while routing funds through layers of shell companies in high-risk jurisdictions. 
Traditional systems fail due to **blind spots between channels** and manual, inefficient detection methods.

TraceNet solves this by constructing a unified **transaction graph** across diverse channels, applying **Graph Neural Networks (GNNs)** and advanced AI techniques to detect, block, and report suspicious activity.

---

## ✨ Features

### Key Capabilities
1. **🧠 GNN-augmented Risk Scoring**:
   - **11-Layer Detection Engine**, combining:
     - GraphSAGE-based GNN inference
     - Behavioral analysis (fan-in/out, velocity, circular flows, jurisdictions).
   - Weighted risk assessment combining 40% GNN scores and 35% additional behavioral signals.
   
2. **📜 SAR (Suspicious Activity Reports)**
   - LLM (Qwen 2.5 via Ollama) generates actionable regulator-ready reports that include flagged entities, risk breakdowns, and narrative analysis.
   
3. **⚔️ Realistic Attack Simulator**
   - Replay real-world laundering rings (Scatter-Gather, Shell Nesting, Money Fragmentation, Velocity, Circular flows).

4. **🕵️ Graph Forensics Analysis**:
   - Interactive network visualization showing channels, accounts, and fraud traces.

5. **🔮 Mule Ring Discovery**:
   - Louvain-based analysis discovers criminal subgraphs for proactive action.

6. **💀 Damage Report**:
   - **What-If Estimator** calculates the financial and operational damage if suspicious transactions hadn't been blocked.

7. **🔒 Privacy-Safe Interbank Intelligence Sharing**:
   - Data anonymization (SHA-256 hashes, no PII leaks) for safe compliance and collaborative detection.

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                         │
│ Dashboard │ Scanner │ Attack Sim │ Graph Forensics │ SAR      │
└──────────────────────┬───────────────────────────────────────┘
             API Calls  │ HTTP
┌──────────────────────▼───────────────────────────────────────┐
│                      FASTAPI BACKEND                         │
│                                                               │
│  ┌───────────────┐  ┌───────────────────┐  ┌───────────────┐ │
│  │ GNN Engine    │  │ Risk Engine       │  │ Qwen 2.5 LLM  │ │
│  │ (GraphSAGE)   │  │ 11 Detection      │  │ Local SAR Gen │ │
│  └───────────────┘  └───────────────────┘  └───────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **A GPU with CUDA support** (optional but recommended; CPU fallback is available).
- **Ollama** for local large language model-driven Suspicious Activity Reports (LLM SAR reports). [Install Ollama](https://ollama.ai).

---

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Aviralsahu960/TraceNet.git
   cd TraceNet
   ```

2. **Create a Conda environment:**
   ```bash
   conda create -n tracenet python=3.10 -y
   conda activate tracenet
   ```

3. **Install required dependencies:**
   ```bash
   pip install --upgrade pip
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121   # For CUDA
   pip install torch-geometric
   pip install -r requirements.txt
   ```

4. **Pull the Local LLM Model:**
   ```bash
   ollama pull qwen2.5:3b
   ```

5. **Generate Synthetic Data:**
   ```bash
   python scripts/get_real_data.py
   ```

6. **Train the GNN Model:**
   ```bash
   python scripts/train_model.py
   ```

---

### Running the Application

7. **Start the API Server:**
   Open the first terminal, activate your environment, and start the backend server:
   ```bash
   conda activate tracenet
   python -m uvicorn backend.api:app --reload
   ```

8. **Start the Frontend App:**
   Open another terminal, activate the same environment, and start the frontend app:
   ```bash
   conda activate tracenet
   python -m streamlit run frontend/app.py
   ```

### Access the Platform:
- Open your browser and go to: **http://localhost:8501**
- Start using the platform for real-time money laundering detection.

---

## 📊 Results

- **Performance Metrics**:
  ```
  ============================================================
    TRACENET GNN v3 RESULTS
  ============================================================
    ✅ Accuracy: 99.96%
    ✅ Precision: 97.87%
    ✅ Recall: 100.00% (zero mules missed)
    ✅ F1 Score: 98.92%
    ✅ True Pos: 92   (Mules caught)
    ✅ False Pos: 2    (False alarms)
    ✅ False Neg: 0    (Mules missed)
    ✅ True Neg: 4897 (Clean users cleared)
  ============================================================
  ```

| Metric       | Score  |
|--------------|--------|
| **Accuracy** | 99.96% |
| **Precision**| 97.87% |
| **Recall**   | 100%   |
| **F1 Score** | 98.92% |

---

## 🔍 Key Features to Test

1. **Transaction Scanner**: Use preloaded scenarios like "Known Criminal" or "Coffee Purchase" and analyze real-time results.
2. **Attack Simulations**: Launch and monitor real laundering scenarios (e.g., Scatter-Gather).
3. **Generate Damage Reports**: Simulate what happens if flagged transactions are approved post-scan.
4. **SAR Reports**: Auto-generate regulator-ready reports, with clear LLM-generated narratives.

---

## 📁 Project Structure

```
TraceNet/
├── backend/                        # API Server with FastAPI
│   ├── api.py                      # 11-layer AI detection logic
├── frontend/                       # Streamlit, Glassmorphism UI
│   └── app.py
├── scripts/                        # Training and data generation scripts
│   ├── get_real_data.py
│   ├── train_model.py
│   └── simulator.py
├── models/
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
└── .gitignore                      # Git ignored files
```

---

## ✉️ Author

- **Aviral Sahu**
   GitHub: [Aviralsahu960](https://github.com/Aviralsahu960)
   Email: aviralsahu960@gmail.com
   LinkedIn: https://www.linkedin.com/in/aviral-sahu-vyntaxdev/


<div align="center">
  
*TraceNet — Fighting Financial Crimes with Cutting-Edge AI Solutions.*
  
</div>
