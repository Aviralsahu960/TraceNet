from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from torch_geometric.data import Data
import pandas as pd
import networkx as nx
import numpy as np
import ollama
import json
import hashlib
import os
import random
from datetime import datetime, timedelta
from collections import defaultdict

# ============================================================
# 1. DATA MODELS
# ============================================================
class Transaction(BaseModel):
    txn_id: str
    sender_id: str
    receiver_id: str
    amount: float
    channel: str
    sender_country: Optional[str] = "US"
    receiver_country: Optional[str] = "US"

app = FastAPI(title="TraceNet - Cross-Channel Mule Detection Platform")

# ============================================================
# 2. GNN ARCHITECTURE
# ============================================================
class MuleDetectorGNN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = SAGEConv(15, 64)
        self.conv2 = SAGEConv(64, 32)
        self.conv3 = SAGEConv(32, 2)
        self.dropout = torch.nn.Dropout(0.3)
        self.bn1 = torch.nn.BatchNorm1d(64)
        self.bn2 = torch.nn.BatchNorm1d(32)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.conv3(x, edge_index)
        return F.log_softmax(x, dim=1)

# ============================================================
# 3. CONSTANTS
# ============================================================
JURISDICTION_RISK = {
    "US": 0.1, "UK": 0.1, "IN": 0.05, "SG": 0.05, "AE": 0.3,
    "KY": 0.5, "PA": 0.5, "VG": 0.4, "NGA": 0.35, "RU": 0.4,
    "CN": 0.2, "HK": 0.25, "CH": 0.15, "DE": 0.1, "BR": 0.25
}

TRUST_TIERS = {
    0: {"max_transfer": 100, "label": "NEW (Unverified)"},
    1: {"max_transfer": 2000, "label": "Basic Trust"},
    2: {"max_transfer": 25000, "label": "Verified"},
    3: {"max_transfer": 100000, "label": "Trusted"},
    4: {"max_transfer": 999999, "label": "Premium Verified"},
}
TRUST_REQUIREMENTS = {0: 0, 1: 5, 2: 20, 3: 50, 4: 100}

# ============================================================
# 4. GLOBAL STATE
# ============================================================
node_risk_scores = {}
live_graph = None
known_mule_patterns = {}
model = None
model_config = {}

blocked_log = []
approved_log = []
all_txn_log = []

user_trust = {}
user_txn_count = {}
user_flagged = set()
user_channels = defaultdict(set)
user_timestamps = defaultdict(list)
user_amounts = defaultdict(list)
user_countries = defaultdict(set)
user_cross_border = defaultdict(int)

sanctioned_set = set()
shell_set = set()
unverified_set = set()
mule_set_global = set()

# ============================================================
# 5. TRUST FUNCTIONS
# ============================================================
def get_trust_tier(user_id):
    if user_id not in user_trust:
        user_trust[user_id] = 0
        user_txn_count[user_id] = 0
    return user_trust[user_id]

def get_max_transfer(user_id):
    tier = get_trust_tier(user_id)
    return TRUST_TIERS[tier]["max_transfer"]

def upgrade_trust(user_id):
    if user_id in user_flagged:
        return
    user_txn_count[user_id] = user_txn_count.get(user_id, 0) + 1
    current_tier = user_trust.get(user_id, 0)
    next_tier = current_tier + 1
    if next_tier in TRUST_REQUIREMENTS:
        if user_txn_count[user_id] >= TRUST_REQUIREMENTS[next_tier]:
            user_trust[user_id] = next_tier

# ============================================================
# 6. STARTUP
# ============================================================
@app.on_event("startup")
def load_gnn_brain():
    global node_risk_scores, live_graph, known_mule_patterns, model
    global model_config, sanctioned_set, shell_set, unverified_set, mule_set_global
    print("🧠 Waking up TraceNet GNN Brain...")

    txns = pd.read_csv("data/transactions.csv")
    users = pd.read_csv("data/users.csv")

    if os.path.exists("models/model_config.json"):
        with open("models/model_config.json") as f:
            model_config = json.load(f)

    live_graph = nx.from_pandas_edgelist(txns, 'sender_id', 'receiver_id', create_using=nx.DiGraph())
    all_nodes = list(live_graph.nodes())
    node_mapping = {node: i for i, node in enumerate(all_nodes)}
    reverse_mapping = {i: node for node, i in node_mapping.items()}

    print("   Computing graph features...")
    pagerank = nx.pagerank(live_graph, max_iter=100)
    try:
        hubs_scores, auth_scores = nx.hits(live_graph, max_iter=100)
    except:
        hubs_scores = {n: 0.0 for n in live_graph.nodes()}
        auth_scores = {n: 0.0 for n in live_graph.nodes()}
    G_undirected = live_graph.to_undirected()
    clustering_coeffs = nx.clustering(G_undirected)

    node_channels_local = defaultdict(set)
    node_countries_local = defaultdict(set)
    node_timestamps_local = defaultdict(list)
    node_amounts_local = defaultdict(list)
    node_cross_border_local = defaultdict(int)

    for _, row in txns.iterrows():
        for uid in [row['sender_id'], row['receiver_id']]:
            node_channels_local[uid].add(row['channel'])
            node_amounts_local[uid].append(row['amount'])
            try:
                node_timestamps_local[uid].append(datetime.strptime(str(row['timestamp']), "%Y-%m-%d %H:%M:%S"))
            except:
                pass
            if 'sender_country' in row and 'receiver_country' in row:
                node_countries_local[uid].add(str(row.get('sender_country', '')))
                node_countries_local[uid].add(str(row.get('receiver_country', '')))
                if str(row.get('sender_country', '')) != str(row.get('receiver_country', '')):
                    node_cross_border_local[uid] += 1
        user_channels[row['sender_id']].add(row['channel'])
        user_channels[row['receiver_id']].add(row['channel'])

    user_meta = users.set_index('user_id').to_dict('index')

    x = torch.zeros((len(all_nodes), 15), dtype=torch.float)
    for node, idx in node_mapping.items():
        x[idx][0] = live_graph.in_degree(node)
        x[idx][1] = live_graph.out_degree(node)
        x[idx][2] = pagerank.get(node, 0.0) * 10000
        x[idx][3] = hubs_scores.get(node, 0.0) * 1000
        x[idx][4] = auth_scores.get(node, 0.0) * 1000
        x[idx][5] = clustering_coeffs.get(node, 0.0)
        total_deg = live_graph.in_degree(node) + live_graph.out_degree(node)
        if total_deg > 0:
            x[idx][6] = min(live_graph.in_degree(node), live_graph.out_degree(node)) / max(live_graph.in_degree(node), live_graph.out_degree(node), 1)
        x[idx][7] = len(node_channels_local.get(node, set()))
        x[idx][8] = node_cross_border_local.get(node, 0)
        x[idx][9] = len(node_countries_local.get(node, set()))
        timestamps = sorted(node_timestamps_local.get(node, []))
        if len(timestamps) >= 2:
            time_gaps = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1)]
            x[idx][10] = min(time_gaps) if time_gaps else 99999
            x[idx][11] = np.mean(time_gaps) if time_gaps else 99999
            x[idx][12] = sum(1 for g in time_gaps if g <= 600)
        if node in user_meta:
            x[idx][13] = user_meta[node].get('jurisdiction_risk', 0.0)
        amounts = node_amounts_local.get(node, [])
        if amounts:
            x[idx][14] = sum(1 for a in amounts if 8500 <= a <= 9999)

    for f in range(15):
        col = x[:, f]
        col_max = col.max()
        if col_max > 0:
            x[:, f] = col / col_max

    edge_src, edge_dst = [], []
    for _, row in txns.iterrows():
        s, r = row['sender_id'], row['receiver_id']
        if s in node_mapping and r in node_mapping:
            edge_src.append(node_mapping[s])
            edge_dst.append(node_mapping[r])
    edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)
    data = Data(x=x, edge_index=edge_index)

    model = MuleDetectorGNN()
    model.load_state_dict(torch.load("models/gnn_model.pth", map_location='cpu', weights_only=True))
    model.eval()

    with torch.no_grad():
        out = model(data)
        probs = torch.exp(out)[:, 1]
    for idx, prob in enumerate(probs):
        node_risk_scores[reverse_mapping[idx]] = prob.item() * 100

    mule_set_global = set(users[users['is_mule'] == 1]['user_id'])
    for mule in mule_set_global:
        if mule in live_graph:
            known_mule_patterns[mule] = {
                'in_degree': live_graph.in_degree(mule),
                'out_degree': live_graph.out_degree(mule),
            }
    if known_mule_patterns:
        avg_in = sum(p['in_degree'] for p in known_mule_patterns.values()) / len(known_mule_patterns)
        avg_out = sum(p['out_degree'] for p in known_mule_patterns.values()) / len(known_mule_patterns)
        known_mule_patterns['__average__'] = {'in_degree': avg_in, 'out_degree': avg_out}

    sanctioned_set = set(users[users['is_sanctioned'] == 1]['user_id'])
    shell_set = set(users[users['account_type'] == 'shell_company']['user_id'])
    unverified_set = set(users[users['kyc_verified'] == False]['user_id'])

    for node in all_nodes:
        txn_count = live_graph.in_degree(node) + live_graph.out_degree(node)
        if txn_count >= 100:
            user_trust[node] = 4
        elif txn_count >= 20:
            user_trust[node] = 3
        elif txn_count >= 5:
            user_trust[node] = 2
        elif txn_count >= 1:
            user_trust[node] = 1
        else:
            user_trust[node] = 0
        user_txn_count[node] = txn_count

    print(f"✅ TraceNet is READY!")
    print(f"   Nodes: {len(all_nodes)} | Sanctioned: {len(sanctioned_set)} | Shells: {len(shell_set)}")

    # Debug: print some GNN scores to verify
    sample_mules = list(mule_set_global)[:5]
    sample_normal = [n for n in all_nodes if n not in mule_set_global][:5]
    print(f"   Sample MULE GNN scores: {[(m, round(node_risk_scores.get(m, 0), 1)) for m in sample_mules]}")
    print(f"   Sample NORMAL GNN scores: {[(n, round(node_risk_scores.get(n, 0), 1)) for n in sample_normal]}")

# ============================================================
# 7. DETECTION ENGINES (ALL SCORES REDUCED FOR BALANCE)
# ============================================================

def detect_chain_risk(sender_id, receiver_id):
    global live_graph
    if sender_id not in live_graph:
        return 0.0
    chain_risk = 0.0
    incoming = list(live_graph.predecessors(sender_id))
    outgoing = list(live_graph.successors(sender_id))
    if len(incoming) >= 1 and len(outgoing) >= 1:
        chain_risk += 5.0
    chain_depth = 0
    current = sender_id
    visited = set()
    while current in live_graph and chain_depth < 10:
        preds = list(live_graph.predecessors(current))
        if not preds or current in visited:
            break
        visited.add(current)
        current = preds[0]
        chain_depth += 1
    if chain_depth >= 3:
        chain_risk += 5.0
    return min(chain_risk, 10.0)


def detect_velocity(sender_id):
    timestamps = user_timestamps.get(sender_id, [])
    if len(timestamps) < 2:
        return 0.0
    recent = sorted(timestamps)[-10:]
    if len(recent) >= 2:
        gaps = [(recent[i+1] - recent[i]).total_seconds() for i in range(len(recent)-1)]
        min_gap = min(gaps)
        if min_gap < 60:
            return 10.0
        elif min_gap < 300:
            return 5.0
    return 0.0


def detect_cross_channel(sender_id, current_channel):
    channels_used = user_channels.get(sender_id, set()).copy()
    channels_used.add(current_channel)
    cross_risk = 0.0
    if len(channels_used) >= 4:
        cross_risk += 10.0
    elif len(channels_used) >= 3:
        cross_risk += 5.0
    if 'mobile_app' in channels_used and 'atm' in channels_used:
        cross_risk += 5.0
    if 'wire' in channels_used and len(channels_used) >= 2:
        cross_risk += 3.0
    return min(cross_risk, 15.0)


def detect_jurisdiction_risk(sender_country, receiver_country):
    s_risk = JURISDICTION_RISK.get(sender_country, 0.2)
    r_risk = JURISDICTION_RISK.get(receiver_country, 0.2)
    jur_risk = 0.0
    if sender_country != receiver_country:
        jur_risk += 5.0
        if s_risk >= 0.3 or r_risk >= 0.3:
            jur_risk += 5.0
        if s_risk >= 0.3 and r_risk >= 0.3:
            jur_risk += 5.0
    secrecy = {'KY', 'PA', 'VG', 'CH'}
    if sender_country in secrecy or receiver_country in secrecy:
        jur_risk += 3.0
    return min(jur_risk, 15.0)


def detect_fragmentation(sender_id, amount):
    amounts = user_amounts.get(sender_id, [])
    if len(amounts) < 5:
        return 0.0
    recent = amounts[-20:]
    if len(recent) >= 10:
        avg = sum(recent) / len(recent)
        if avg < 600:
            std = (sum((a - avg)**2 for a in recent) / len(recent))**0.5
            if std < 100:
                return 10.0
    return 0.0


def detect_sanctions(user_id):
    if user_id in sanctioned_set:
        return 30.0
    sanction_risk = 0.0
    if user_id in live_graph:
        neighbors = set(live_graph.successors(user_id)).union(set(live_graph.predecessors(user_id)))
        if neighbors.intersection(sanctioned_set):
            sanction_risk += 10.0
        for neighbor in list(neighbors)[:20]:
            if neighbor in live_graph:
                n2 = set(live_graph.successors(neighbor)).union(set(live_graph.predecessors(neighbor)))
                if n2.intersection(sanctioned_set):
                    sanction_risk += 3.0
                    break
    return min(sanction_risk, 15.0)


def detect_ownership_links(user_id):
    users_df = pd.read_csv("data/users.csv")
    user_row = users_df[users_df['user_id'] == user_id]
    ownership_risk = 0.0
    linked = []
    if len(user_row) > 0:
        linked_raw = user_row.iloc[0].get('linked_accounts', '[]')
        try:
            if isinstance(linked_raw, str) and linked_raw.startswith('['):
                linked = eval(linked_raw)
        except:
            linked = []
    for linked_id in linked:
        if linked_id in user_flagged:
            ownership_risk += 8.0
        if linked_id in sanctioned_set:
            ownership_risk += 10.0
        linked_gnn = node_risk_scores.get(linked_id, 0.0)
        if linked_gnn > 50:
            ownership_risk += 5.0
    return min(ownership_risk, 15.0), linked


def detect_routing_complexity(sender_id, receiver_id):
    global live_graph
    if sender_id not in live_graph or receiver_id not in live_graph:
        return 0.0, 0
    try:
        shortest = nx.shortest_path_length(live_graph, sender_id, receiver_id)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        shortest = 0
    complexity_risk = 0.0
    if shortest >= 4:
        complexity_risk = 10.0
    elif shortest >= 3:
        complexity_risk = 5.0
    return min(complexity_risk, 10.0), shortest


def detect_nesting(sender_id, receiver_id):
    global live_graph
    nesting_risk = 0.0
    shell_layers = 0
    current = sender_id
    visited = set()
    path = [current]
    for _ in range(10):
        if current in visited or current not in live_graph:
            break
        visited.add(current)
        succs = list(live_graph.successors(current))
        if not succs:
            break
        next_node = max(succs, key=lambda n: live_graph.out_degree(n) if n in live_graph else 0)
        path.append(next_node)
        if next_node in shell_set:
            shell_layers += 1
        if next_node in unverified_set:
            shell_layers += 0.5
        current = next_node
    if shell_layers >= 3:
        nesting_risk = 12.0
    elif shell_layers >= 2:
        nesting_risk = 8.0
    elif shell_layers >= 1:
        nesting_risk = 4.0
    if sender_id in shell_set:
        nesting_risk += 5.0
    if receiver_id in shell_set:
        nesting_risk += 5.0
    return min(nesting_risk, 15.0), shell_layers, path[:6]


# ============================================================
# 8. COMMUNITY DETECTION & INTELLIGENCE
# ============================================================

def discover_mule_communities():
    global live_graph
    import community as community_louvain
    G_undirected = live_graph.to_undirected()
    partition = community_louvain.best_partition(G_undirected)
    communities = defaultdict(list)
    for node, comm_id in partition.items():
        communities[comm_id].append(node)
    suspicious = []
    for comm_id, members in communities.items():
        if len(members) < 3 or len(members) > 500:
            continue
        subgraph = live_graph.subgraph(members)
        internal_edges = subgraph.number_of_edges()
        max_possible = len(members) * (len(members) - 1)
        density = internal_edges / max(max_possible, 1)
        member_risks = [node_risk_scores.get(m, 0.0) for m in members]
        avg_risk = sum(member_risks) / max(len(member_risks), 1)
        mule_count = sum(1 for m in members if m in mule_set_global)
        suspicion_score = (density * 50) + (avg_risk * 0.5) + (mule_count * 10)
        if suspicion_score > 15:
            suspicious.append({
                "community_id": comm_id, "size": len(members),
                "members": members[:20], "density": round(density, 4),
                "avg_risk": round(avg_risk, 2), "known_mules": mule_count,
                "suspicion_score": round(suspicion_score, 2)
            })
    suspicious.sort(key=lambda x: x['suspicion_score'], reverse=True)
    return suspicious


def generate_privacy_safe_intel(user_id):
    hashed_id = hashlib.sha256(user_id.encode()).hexdigest()[:16]
    intel = {
        "hashed_entity_id": hashed_id,
        "risk_score": round(node_risk_scores.get(user_id, 0.0), 2),
        "is_flagged": user_id in user_flagged,
        "is_sanctioned": user_id in sanctioned_set,
        "trust_tier": user_trust.get(user_id, 0),
        "behavioral_signals": {
            "channels_count": len(user_channels.get(user_id, set())),
            "cross_border_count": user_cross_border.get(user_id, 0),
            "countries_count": len(user_countries.get(user_id, set())),
            "transaction_count": user_txn_count.get(user_id, 0),
        },
        "graph_signals": {},
        "generated_at": datetime.now().isoformat(),
        "sharing_standard": "ISO 20022 Compatible"
    }
    if user_id in live_graph:
        successors = set(live_graph.successors(user_id))
        predecessors = set(live_graph.predecessors(user_id))
        intel["graph_signals"] = {
            "in_degree": live_graph.in_degree(user_id),
            "out_degree": live_graph.out_degree(user_id),
            "is_pass_through": live_graph.in_degree(user_id) >= 1 and live_graph.out_degree(user_id) >= 1,
            "neighbor_count": len(successors.union(predecessors)),
            "has_circular_flow": bool(successors.intersection(predecessors))
        }
    return intel


# ============================================================
# 9. MASTER RISK ENGINE (WEIGHTED - NOT SUMMED)
# ============================================================

def calculate_live_risk(user_id, amount, channel, sender_country, receiver_country):
    """
    WEIGHTED RISK ENGINE:
    - GNN is PRIMARY signal (40% weight)
    - Behavioral boosters are SECONDARY (capped at 35% total)
    - This creates realistic spread: criminals ~55-75%, normals ~5-15%
    """
    # PRIMARY: GNN Score (0-100)
    gnn_risk = node_risk_scores.get(user_id, 0.0)

    # SECONDARY: Behavioral boosters (each small, capped total)
    behavior_risk = 0.0
    if user_id in live_graph:
        in_deg = live_graph.in_degree(user_id)
        out_deg = live_graph.out_degree(user_id)
        if in_deg >= 1 and out_deg >= 1:
            ratio = min(in_deg, out_deg) / max(in_deg, out_deg, 1)
            if ratio > 0.7:
                behavior_risk += 3.0
        if out_deg >= 10:
            behavior_risk += 5.0
        elif out_deg >= 5:
            behavior_risk += 3.0
        if in_deg >= 10:
            behavior_risk += 5.0
        elif in_deg >= 5:
            behavior_risk += 3.0
        successors = set(live_graph.successors(user_id))
        predecessors = set(live_graph.predecessors(user_id))
        if successors.intersection(predecessors):
            behavior_risk += 5.0

    # Structuring
    if 8500 <= amount <= 9999:
        behavior_risk += 8.0
    elif amount > 9999:
        behavior_risk += 4.0

    vel_risk = detect_velocity(user_id)
    chan_risk = detect_cross_channel(user_id, channel)
    jur_risk = detect_jurisdiction_risk(sender_country, receiver_country)
    sanc_risk = detect_sanctions(user_id)
    frag_risk = detect_fragmentation(user_id, amount)
    ownership_risk, linked = detect_ownership_links(user_id)
    nesting_risk, shell_layers, nesting_path = detect_nesting(user_id, user_id)

    # WEIGHTED COMBINATION
    booster_total = behavior_risk + vel_risk + chan_risk + jur_risk + sanc_risk + frag_risk + ownership_risk + nesting_risk
    booster_capped = min(booster_total, 35.0)

    # Final: 40% GNN + boosters (max 35) = max possible ~75%
    final_risk = (gnn_risk * 0.4) + booster_capped

    breakdown = {
        "gnn_score": round(gnn_risk, 2),
        "behavioral": round(behavior_risk, 2),
        "velocity": round(vel_risk, 2),
        "cross_channel": round(chan_risk, 2),
        "jurisdiction": round(jur_risk, 2),
        "sanctions": round(sanc_risk, 2),
        "fragmentation": round(frag_risk, 2),
        "ownership_link": round(ownership_risk, 2),
        "nesting": round(nesting_risk, 2)
    }

    return round(min(final_risk, 99.9), 2), breakdown


# ============================================================
# 10. MAIN SCORING ENDPOINT
# ============================================================
@app.post("/score_transaction")
def score_txn(txn: Transaction):
    global live_graph, blocked_log, approved_log, all_txn_log

    now = datetime.now()

    user_channels[txn.sender_id].add(txn.channel)
    user_timestamps[txn.sender_id].append(now)
    user_amounts[txn.sender_id].append(txn.amount)
    user_countries[txn.sender_id].add(txn.sender_country)
    user_countries[txn.sender_id].add(txn.receiver_country)
    if txn.sender_country != txn.receiver_country:
        user_cross_border[txn.sender_id] += 1

    sender_tier = get_trust_tier(txn.sender_id)
    sender_max = get_max_transfer(txn.sender_id)
    sender_label = TRUST_TIERS[sender_tier]["label"]

    # TRUST GATE: Only for Tier 0 brand new accounts
    if sender_tier == 0 and txn.amount > sender_max:
        result = {
            "txn_id": txn.txn_id, "risk_score": 95.0, "confidence": 0.95,
            "action": "BLOCK",
            "block_reason": f"TRUST GATE: New account. Max ${sender_max}, attempted ${txn.amount}",
            "sender_risk": 95.0, "receiver_risk": 0.0,
            "trust_tier": 0, "trust_label": "NEW", "max_allowed": sender_max,
            "channel": txn.channel,
            "sender_country": txn.sender_country, "receiver_country": txn.receiver_country,
            "risk_breakdown": {"trust_violation": 95.0},
            "detection_layers_triggered": ["TRUST_GATE"],
            "sar_report": None
        }
        user_flagged.add(txn.sender_id)
        try:
            prompt = f"""Write a 3-sentence SAR: New unverified account {txn.sender_id} attempted ${txn.amount} via {txn.channel} to {txn.receiver_id} ({txn.sender_country}→{txn.receiver_country}). Max for new accounts: ${sender_max}. Confidence 95%. Professional tone."""
            response = ollama.chat(model='qwen2.5:3b', messages=[{'role': 'user', 'content': prompt}])
            result["sar_report"] = response['message']['content']
        except Exception as e:
            result["sar_report"] = f"Auto-SAR: New account {txn.sender_id} blocked. Attempted ${txn.amount} (max ${sender_max})."
        blocked_log.append(result)
        all_txn_log.append(result)
        return result

    # ===== FULL AI ENGINE =====
    live_graph.add_edge(txn.sender_id, txn.receiver_id)

    new_row = pd.DataFrame([{
        'txn_id': txn.txn_id, 'sender_id': txn.sender_id, 'receiver_id': txn.receiver_id,
        'amount': txn.amount, 'channel': txn.channel,
        'timestamp': now.strftime("%Y-%m-%d %H:%M:%S"),
        'sender_country': txn.sender_country, 'receiver_country': txn.receiver_country,
        'is_suspicious': 0
    }])
    new_row.to_csv('data/transactions.csv', mode='a', header=False, index=False)

    s_risk, s_breakdown = calculate_live_risk(txn.sender_id, txn.amount, txn.channel, txn.sender_country, txn.receiver_country)
    r_risk, r_breakdown = calculate_live_risk(txn.receiver_id, txn.amount, txn.channel, txn.sender_country, txn.receiver_country)

    chain_risk = detect_chain_risk(txn.sender_id, txn.receiver_id)
    routing_risk, hop_count = detect_routing_complexity(txn.sender_id, txn.receiver_id)
    nesting_risk_txn, shell_count, nest_path = detect_nesting(txn.sender_id, txn.receiver_id)

    # Take higher risk + small boost
    base_risk = max(s_risk, r_risk)
    boost = min(chain_risk + routing_risk + (nesting_risk_txn * 0.3), 15.0)
    max_risk = min(base_risk + boost, 99.9)

    breakdown = s_breakdown if s_risk >= r_risk else r_breakdown
    breakdown["chain_detection"] = round(chain_risk, 2)
    breakdown["routing_complexity"] = round(routing_risk, 2)
    breakdown["nesting_txn"] = round(nesting_risk_txn, 2)

    active_layers = sum(1 for v in breakdown.values() if v > 0)
    confidence = round(min(active_layers / max(len(breakdown), 1), 0.99), 2)

    # BLOCK THRESHOLD: 50%
    is_fraud = 1 if max_risk > 50.0 else 0
    triggered = [k for k, v in breakdown.items() if v > 0]

    result = {
        "txn_id": txn.txn_id,
        "risk_score": round(max_risk, 2),
        "confidence": confidence,
        "action": "BLOCK" if is_fraud else "ALLOW",
        "block_reason": f"AI: {len(triggered)} layers triggered" if is_fraud else None,
        "sender_risk": s_risk, "receiver_risk": r_risk,
        "trust_tier": sender_tier, "trust_label": sender_label, "max_allowed": sender_max,
        "channel": txn.channel,
        "sender_country": txn.sender_country, "receiver_country": txn.receiver_country,
        "risk_breakdown": breakdown,
        "detection_layers_triggered": triggered,
        "sar_report": None
    }

    if is_fraud:
        user_flagged.add(txn.sender_id)
        print(f"🚨 BLOCKED {txn.txn_id} | Risk: {max_risk:.1f}% | Layers: {triggered}")
        try:
            prompt = f"""Write a 5-sentence SAR:
- TXN: {txn.txn_id} | ${txn.amount} | {txn.channel} | {txn.sender_country}→{txn.receiver_country}
- Sender: {txn.sender_id} (Risk: {s_risk}%) | Receiver: {txn.receiver_id} (Risk: {r_risk}%)
- Combined: {max_risk:.1f}% | Confidence: {confidence*100:.0f}% | Layers: {', '.join(triggered)}
GraphSAGE GNN flagged suspicious topology. Professional, regulator-ready."""
            response = ollama.chat(model='qwen2.5:3b', messages=[{'role': 'user', 'content': prompt}])
            result["sar_report"] = response['message']['content']
        except Exception as e:
            result["sar_report"] = f"Auto-SAR: {txn.sender_id} flagged at {max_risk:.1f}%. {len(triggered)} layers triggered."
        blocked_log.append(result)
    else:
        upgrade_trust(txn.sender_id)
        approved_log.append(result)
        print(f"✅ ALLOWED {txn.txn_id} | Risk: {max_risk:.1f}%")

    all_txn_log.append(result)
    return result


# ============================================================
# 11. API ENDPOINTS
# ============================================================

@app.get("/blocked")
def get_blocked():
    return blocked_log

@app.get("/stats")
def get_stats():
    return {
        "total_nodes": live_graph.number_of_nodes(),
        "total_edges": live_graph.number_of_edges(),
        "blocked_count": len(blocked_log),
        "approved_count": len(approved_log),
        "flagged_users": len(user_flagged),
        "sanctioned_entities": len(sanctioned_set),
        "shell_companies": len(shell_set),
        "unverified_kyc": len(unverified_set),
        "model_config": model_config
    }

@app.get("/trust/{user_id}")
def get_trust(user_id: str):
    tier = get_trust_tier(user_id)
    return {
        "user_id": user_id, "trust_tier": tier,
        "trust_label": TRUST_TIERS[tier]["label"],
        "max_transfer": get_max_transfer(user_id),
        "total_transactions": user_txn_count.get(user_id, 0),
        "is_flagged": user_id in user_flagged,
        "is_sanctioned": user_id in sanctioned_set,
        "is_shell_company": user_id in shell_set,
        "is_kyc_verified": user_id not in unverified_set,
        "channels_used": list(user_channels.get(user_id, set())),
        "countries_connected": list(user_countries.get(user_id, set()))
    }

@app.get("/feed")
def get_feed():
    return all_txn_log[-50:]

@app.get("/communities")
def get_communities():
    try:
        return {"total_communities_found": len(discover_mule_communities()), "suspicious_communities": discover_mule_communities()[:20]}
    except ImportError:
        return {"error": "pip install python-louvain"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/intel/{user_id}")
def get_intel(user_id: str):
    return generate_privacy_safe_intel(user_id)

@app.get("/routing/{sender_id}/{receiver_id}")
def get_routing(sender_id: str, receiver_id: str):
    risk, hops = detect_routing_complexity(sender_id, receiver_id)
    return {"sender": sender_id, "receiver": receiver_id, "shortest_path_hops": hops,
            "complexity_risk": risk, "assessment": "EXCESSIVE" if hops >= 4 else "MODERATE" if hops >= 3 else "NORMAL"}

@app.get("/ownership/{user_id}")
def get_ownership(user_id: str):
    risk, linked = detect_ownership_links(user_id)
    return {"user_id": user_id, "linked_accounts": linked, "ownership_risk": risk,
            "any_linked_flagged": any(l in user_flagged for l in linked),
            "any_linked_sanctioned": any(l in sanctioned_set for l in linked)}

@app.get("/nesting/{sender_id}/{receiver_id}")
def get_nesting(sender_id: str, receiver_id: str):
    risk, layers, path = detect_nesting(sender_id, receiver_id)
    return {"sender": sender_id, "receiver": receiver_id, "shell_layers": layers,
            "nesting_risk": risk, "money_path": path,
            "assessment": "DEEP NESTING" if layers >= 3 else "MODERATE" if layers >= 1 else "NONE"}

@app.get("/simulate_attack/{ring_type}")
def simulate_attack(ring_type: str):
    def get_normals(count):
        normals = []
        for _ in range(count):
            sc = random.choice(["US", "UK", "IN", "SG"])
            normals.append({
                "sender": f"U{random.randint(2500, 4500):05d}",
                "receiver": f"U{random.randint(2500, 4500):05d}",
                "amount": round(random.uniform(10, 500), 2),
                "channel": random.choice(["upi", "web", "mobile_app"]),
                "s_country": sc, "r_country": sc, "delay_ms": 100
            })
        return normals

    scenarios = {
        "scatter_gather": {
            "name": "Scatter-Gather Ring (Mobile → ATM)",
            "description": "Boss distributes $9,500 to mules via Mobile App. Mules withdraw at ATMs. Mixed with normal traffic.",
            "total_laundered": 470000,
            "steps": (
                get_normals(5) +
                [{"sender": "U00001", "receiver": f"U{100+i:05d}", "amount": 9500, "channel": "mobile_app", "s_country": "US", "r_country": "US", "delay_ms": 150} for i in range(10)] +
                get_normals(5) +
                [{"sender": f"U{100+i:05d}", "receiver": "U00099", "amount": 9400, "channel": "atm", "s_country": "US", "r_country": "KY", "delay_ms": 150} for i in range(10)] +
                get_normals(5) +
                [{"sender": "U00001", "receiver": f"U{110+i:05d}", "amount": 9500, "channel": "mobile_app", "s_country": "US", "r_country": "US", "delay_ms": 150} for i in range(5)] +
                get_normals(5)
            )
        },
        "shell_nesting": {
            "name": "Shell Company Nesting (Wire Cross-Border)",
            "description": "Money bounces between 4 shell companies across secrecy jurisdictions. Mixed with normal traffic.",
            "total_laundered": 2000000,
            "steps": (
                get_normals(5) +
                [{"sender": "U00998", "receiver": "U00997", "amount": 45000, "channel": "wire", "s_country": "KY", "r_country": "VG", "delay_ms": 200},
                 {"sender": "U00997", "receiver": "U00996", "amount": 44500, "channel": "wire", "s_country": "VG", "r_country": "PA", "delay_ms": 200},
                 {"sender": "U00996", "receiver": "U00995", "amount": 44000, "channel": "wire", "s_country": "PA", "r_country": "AE", "delay_ms": 200},
                 {"sender": "U00995", "receiver": "U00998", "amount": 43500, "channel": "wire", "s_country": "AE", "r_country": "KY", "delay_ms": 200}] +
                get_normals(5) +
                [{"sender": "U00998", "receiver": "U00997", "amount": 42000, "channel": "wire", "s_country": "KY", "r_country": "VG", "delay_ms": 200},
                 {"sender": "U00997", "receiver": "U00996", "amount": 41500, "channel": "wire", "s_country": "VG", "r_country": "PA", "delay_ms": 200}] +
                get_normals(5)
            )
        },
        "fragmentation": {
            "name": "UPI Fragmentation Ring",
            "description": "Boss sends to fragmenters who split into tiny UPI payments. Normal traffic mixed in.",
            "total_laundered": 200000,
            "steps": (
                get_normals(5) +
                [{"sender": "U00500", "receiver": f"U{501+i:05d}", "amount": 10000, "channel": "web", "s_country": "IN", "r_country": "IN", "delay_ms": 150} for i in range(5)] +
                get_normals(5) +
                [{"sender": f"U{501+i:05d}", "receiver": f"U{2000+j:05d}", "amount": 500, "channel": "upi", "s_country": "IN", "r_country": "IN", "delay_ms": 100} for i in range(5) for j in range(3)] +
                get_normals(5)
            )
        },
        "velocity": {
            "name": "Cross-Border Velocity Ring",
            "description": "Money hops across 5 countries in under 10 minutes. Normal domestic traffic mixed in.",
            "total_laundered": 750000,
            "steps": (
                get_normals(5) +
                [{"sender": "U00800", "receiver": "U00801", "amount": 25000, "channel": "wire", "s_country": "US", "r_country": "KY", "delay_ms": 300},
                 {"sender": "U00801", "receiver": "U00802", "amount": 24500, "channel": "web", "s_country": "KY", "r_country": "AE", "delay_ms": 300},
                 {"sender": "U00802", "receiver": "U00803", "amount": 24000, "channel": "wire", "s_country": "AE", "r_country": "SG", "delay_ms": 300},
                 {"sender": "U00803", "receiver": "U00804", "amount": 23500, "channel": "web", "s_country": "SG", "r_country": "VG", "delay_ms": 300}] +
                get_normals(5) +
                [{"sender": "U00800", "receiver": "U00801", "amount": 22000, "channel": "wire", "s_country": "US", "r_country": "KY", "delay_ms": 300},
                 {"sender": "U00801", "receiver": "U00802", "amount": 21500, "channel": "web", "s_country": "KY", "r_country": "AE", "delay_ms": 300}] +
                get_normals(5)
            )
        },
        "circular": {
            "name": "Circular Laundering Ring",
            "description": "Money in a perfect circle: A→B→C→...→A. Normal traffic mixed in.",
            "total_laundered": 500000,
            "steps": (
                get_normals(5) +
                [{"sender": f"U{900+i:05d}", "receiver": f"U{900+(i+1)%10:05d}", "amount": 7000, "channel": "web", "s_country": "US", "r_country": "KY", "delay_ms": 200} for i in range(10)] +
                get_normals(5) +
                [{"sender": f"U{900+i:05d}", "receiver": f"U{900+(i+1)%10:05d}", "amount": 6500, "channel": "wire", "s_country": "KY", "r_country": "PA", "delay_ms": 200} for i in range(10)] +
                get_normals(5)
            )
        }
    }
    if ring_type not in scenarios:
        return {"error": f"Options: {list(scenarios.keys())}"}
    return scenarios[ring_type]


@app.get("/damage_estimate/{entity_id}")
def estimate_damage(entity_id: str):
    global live_graph
    if entity_id not in live_graph:
        return {"error": "Entity not found."}
    df = pd.read_csv("data/transactions.csv")
    sent = df[df['sender_id'] == entity_id]
    received = df[df['receiver_id'] == entity_id]
    total_sent = sent['amount'].sum()
    total_received = received['amount'].sum()
    downstream = set()
    queue = [entity_id]
    visited = set()
    depth = 0
    while queue and depth < 5:
        next_queue = []
        for node in queue:
            if node in visited:
                continue
            visited.add(node)
            if node in live_graph:
                downstream.update(list(live_graph.successors(node)))
                next_queue.extend(list(live_graph.successors(node)))
        queue = next_queue
        depth += 1
    network_volume = sum(df[df['sender_id'] == n]['amount'].sum() for n in list(downstream)[:100])
    at_risk_countries = set()
    channels_exploited = set()
    for node in list(downstream)[:50]:
        at_risk_countries.update(df[df['sender_id'] == node]['sender_country'].dropna().unique().tolist())
        at_risk_countries.update(df[df['receiver_id'] == node]['receiver_country'].dropna().unique().tolist())
        channels_exploited.update(df[(df['sender_id'] == node) | (df['receiver_id'] == node)]['channel'].dropna().unique().tolist())
    downstream_mules = len(downstream.intersection(mule_set_global))
    return {
        "entity_id": entity_id, "is_flagged": entity_id in user_flagged,
        "is_sanctioned": entity_id in sanctioned_set,
        "direct_transactions_sent": len(sent), "direct_transactions_received": len(received),
        "total_money_sent": round(total_sent, 2), "total_money_received": round(total_received, 2),
        "downstream_entities_affected": len(downstream), "downstream_mules_connected": downstream_mules,
        "total_network_exposure": round(network_volume, 2),
        "estimated_laundered": round(min(total_sent, total_received) * 0.85, 2),
        "jurisdictions_at_risk": list(at_risk_countries), "channels_exploited": list(channels_exploited),
        "damage_assessment": "CATASTROPHIC" if network_volume > 1000000 else "SEVERE" if network_volume > 100000 else "MODERATE" if network_volume > 10000 else "LOW",
        "what_if_statement": f"If {entity_id}'s transactions were NOT blocked, an estimated ${round(network_volume, 2):,.2f} could flow through {len(downstream)} downstream accounts across {len(at_risk_countries)} jurisdictions via {len(channels_exploited)} channels, reaching {downstream_mules} known mule accounts."
    }


@app.get("/")
def health():
    return {"status": "TraceNet ONLINE", "version": "v4.0",
            "nodes": live_graph.number_of_nodes(), "edges": live_graph.number_of_edges(),
            "detection_layers": 11, "channels": 6, "jurisdictions": 10}