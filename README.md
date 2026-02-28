<div align="center">

# 🛡️ TraceNet

### Real-Time Cross-Channel Money Mule Detection Platform

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-Geometric-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)

**TraceNet uses Graph Neural Networks, an 11-Layer AI Risk Engine, and Local LLM-powered SAR generation to detect, block, and report cross-channel money mule rings in real-time.**

[Features](#-features) • [Architecture](#-architecture) • [Demo](#-live-demo) • [Setup](#-quick-start) • [Results](#-results)

---

</div>

## 🚨 The Problem

Every year, **$2 trillion** is laundered globally. Criminals don't move money in one transaction — they split it across Mobile Apps, ATMs, UPI, and Wire Transfers, bouncing it through shell companies in secrecy jurisdictions like the Cayman Islands, Panama, and Dubai.

**Current banking systems check each channel separately.** Mobile team sees nothing wrong. ATM team sees nothing wrong. But zoom out — and there's a criminal ring moving half a million dollars in 10 minutes.

> *TraceNet sees what siloed systems can't. We don't check transactions — we check relationships.*

---

## ✨ Features

### 🧠 11-Layer AI Detection Engine

| # | Layer | What It Does |
|---|-------|-------------|
| 1 | **GNN (GraphSAGE)** | 3-layer neural network trained on 15 graph features — PageRank, HITS, clustering coefficient, velocity patterns |
| 2 | **Behavioral Engine** | Detects pass-through accounts, fan-out, fan-in, circular flows, structuring ($8,500-$9,999) |
| 3 | **Velocity Detector** | Flags bursts of transactions under 2 minutes apart |
| 4 | **Cross-Channel** | Catches mobile→ATM, web→UPI multi-channel laundering patterns |
| 5 | **Jurisdiction Risk** | Scores 10 countries, flags secrecy jurisdictions (KY, PA, VG) |
| 6 | **Sanctions Screening** | Behavior-based, not just list matching — checks 2 hops deep |
| 7 | **Fragmentation** | Detects splitting large amounts into identical micro-payments |
| 8 | **Ownership Links** | Resolves linked accounts and propagates risk across entities |
| 9 | **Nesting Detector** | Traces money through layers of shell companies |
| 10 | **Chain Tracer** | Follows money 10 hops forward and backward |
| 11 | **Routing Complexity** | Measures hop-count between entities for excessive layering |

### 🎯 Platform Capabilities

- **⚔️ Live Attack Simulator** — Replay 5 real attack scenarios (Scatter-Gather, Shell Nesting, Fragmentation, Velocity, Circular) with mixed normal traffic
- **💀 What-If Damage Estimator** — Shows downstream impact if a criminal's transactions were NOT blocked
- **🕸️ Graph Forensics** — Interactive network visualization with channel-coded edges
- **🔮 Ring Discovery** — Louvain community detection auto-discovers hidden mule clusters
- **📜 Auto-Generated SAR Reports** — Qwen 2.5 LLM generates regulator-ready Suspicious Activity Reports
- **🔒 Privacy-Safe Intel Sharing** — SHA-256 hashed entity profiles for inter-bank sharing (ISO 20022)
- **👤 Entity Profiler** — Trust tiers, ownership links, behavioral patterns per entity
- **📊 Network Analytics** — Cross-border corridors, channel volumes, structuring detection

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                        │
│  Command Center │ Scanner │ Attack Sim │ Graph │ Analytics   │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────────┐
│                    FASTAPI BACKEND                           │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ GNN Engine  │  │ 10 Behavioral│  │ Qwen 2.5 LLM     │   │
│  ��� (GraphSAGE) │  │ Detection    │  │ (SAR Generation)  │   │
│  │ 3 Layers    │  │ Layers       │  │ Local via Ollama  │   │
│  │ 15 Features │  │              │  │                   │   │
│  └──────┬──────┘  └──────┬───────┘  └───────────────────┘   │
│         │                │                                    │
│  ┌──────▼────────────────▼───────┐                           │
│  │   WEIGHTED RISK ENGINE        │                           │
│  │   40% GNN + 35% Boosters     │                           │
│  │   Threshold: 50% → BLOCK     │                           │
│  └───────────────────────────────┘                           │
│                                                              │
│  ┌────────────┐  ┌─────────────┐  ┌───────────────────┐     │
│  │ NetworkX   │  │ Trust Tier  │  │ Louvain Community │     │
│  │ Live Graph │  │ System      │  │ Detection         │     │
│  └────────────┘  └─────────────┘  └───────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

---

## 📊 Results

```
============================================================
  TRACENET GNN v3 RESULTS
============================================================
  ✅ Accuracy:     99.96%
  ✅ Precision:    97.87%
  ✅ Recall:       100.00%  (zero mules missed)
  ✅ F1 Score:     98.92%
  ✅ True Pos:     92   (Mules caught)
  ✅ False Pos:    2    (False alarms)
  ✅ False Neg:    0    (Mules missed)
  ✅ True Neg:     4897 (Clean users cleared)
============================================================
```

| Metric | Value |
|--------|-------|
| Detection Layers | **11** |
| Payment Channels | **6** (Mobile, Web, ATM, UPI, Wire, Branch) |
| Jurisdictions | **10** (with risk scoring) |
| Entity Graph | **5,000 nodes, 15,000+ edges** |
| GNN Features | **15** (PageRank, HITS, velocity, cross-channel, jurisdiction) |
| Response Time | **Real-time per transaction** |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- CUDA-capable GPU (optional, CPU works too)
- [Ollama](https://ollama.ai) with `qwen2.5:3b` model

### Installation

```bash
# Clone the repository
git clone https://github.com/Aviralsahu960/TraceNet.git
cd TraceNet

# Create conda environment
conda create -n tracenet python=3.10 -y
conda activate tracenet

# Install dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install torch-geometric
pip install -r requirements.txt

# Pull the LLM model
ollama pull qwen2.5:3b

# Generate data & train GNN
python scripts/get_real_data.py
python scripts/train_model.py
```

### Running

**Terminal 1 — API Server:**
```bash
conda activate tracenet
python -m uvicorn backend.api:app --reload
```

**Terminal 2 — Frontend:**
```bash
conda activate tracenet
python -m streamlit run frontend/app.py
```

Open **http://localhost:8501** in your browser.

---

## 🎮 Live Demo

### 1. Transaction Scanner
Submit any transaction and watch 11 detection layers analyze it in real-time. Try the quick-test buttons: **Known Criminal**, **New Scammer**, **Coffee Purchase**, **Shell Transfer**.

### 2. Attack Simulator
Launch real attack scenarios and watch TraceNet intercept them:
- 🎯 **Scatter-Gather** — Boss distributes to 50 mules via mobile, mules withdraw at ATMs
- 🏦 **Shell Nesting** — Money bounces between 4 shell companies across secrecy jurisdictions
- 💥 **Fragmentation** — $10K split into micro UPI payments of $500 each
- ⚡ **Velocity** — Money hops across 5 countries in under 10 minutes
- 🔄 **Circular** — Perfect money circle: A→B→C→D→...→A

### 3. Damage Report
Enter any entity ID to see what would happen if their transactions were NOT blocked — downstream exposure, jurisdictions at risk, mule accounts reached.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **GNN Engine** | PyTorch Geometric (GraphSAGE, 3 layers, 15 features) |
| **API Server** | FastAPI |
| **Graph Engine** | NetworkX (directed graph, real-time updates) |
| **LLM (SAR Reports)** | Qwen 2.5 3B (local, via Ollama) |
| **Frontend** | Streamlit + streamlit-agraph |
| **Community Detection** | Louvain Algorithm (python-louvain) |
| **ML Framework** | PyTorch with CUDA support |

---

## 📁 Project Structure

```
TraceNet/
├── backend/
│   ├── __init__.py
│   └── api.py              # FastAPI server + 11-layer risk engine
├── frontend/
│   └── app.py              # Streamlit glassmorphism UI
├── scripts/
│   ├── get_real_data.py     # Synthetic data generator
│   ├── generate_data.py     # Data generation utilities
│   ├── train_model.py       # GNN training pipeline
│   └── simulator.py         # Attack simulation logic
├── models/
│   ├── gnn_model.pth        # Trained GraphSAGE weights
│   ├── model_config.json    # Model performance metrics
│   └── xgb_model.pkl        # XGBoost ensemble model
├── data/                    # Generated at runtime
│   ├── transactions.csv     # 15,000+ synthetic transactions
│   └── users.csv            # 5,000 user profiles
├── requirements.txt
└── README.md
```

---

## 🔑 Key Innovations

1. **Unified Cross-Channel Graph** — All 6 payment channels feed into one graph. No siloed detection.

2. **Weighted Risk Architecture** — GNN provides 40% of the signal, behavioral boosters contribute up to 35%. This creates clear separation: criminals score 55-75%, normal users score 5-15%.

3. **Proactive Ring Discovery** — Louvain community detection finds suspicious clusters BEFORE they transact, not after.

4. **Privacy-Safe Intelligence** — SHA-256 hashed entity profiles enable inter-bank sharing without exposing PII. ISO 20022 compatible.

5. **Local LLM SAR Generation** — Qwen 2.5 runs entirely on-device. No data leaves the machine. Every blocked transaction gets a regulator-ready SAR report.

---

## 👤 Author

**Aviral Sahu** — [@Aviralsahu960](https://github.com/Aviralsahu960)
**K Kushal Varma**
---

<div align="center">

*TraceNet — Because criminals don't operate in silos, and neither should we.*

</div>
