import os
import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from torch_geometric.data import Data
import pandas as pd
import networkx as nx
import numpy as np
from datetime import datetime

print("=" * 60)
print("  TraceNet GNN v3 - Cross-Channel Mule Detection")
print("=" * 60)

# ============================================================
# 1. LOAD DATA
# ============================================================
print("\n1. Loading Multi-Channel Transaction Network...")
users = pd.read_csv("data/users.csv")
txns = pd.read_csv("data/transactions.csv")

# Build directed graph
G = nx.from_pandas_edgelist(txns, 'sender_id', 'receiver_id', create_using=nx.DiGraph())
all_nodes = list(G.nodes())
node_mapping = {node: i for i, node in enumerate(all_nodes)}

print(f"   Nodes: {len(all_nodes)} | Edges: {G.number_of_edges()}")
print(f"   Channels: {txns['channel'].nunique()} | Jurisdictions: {users['country'].nunique()}")

# ============================================================
# 2. FEATURE ENGINEERING - 15 FEATURES
# ============================================================
print("\n2. Engineering 15 Graph + Channel + Velocity Features...")

num_features = 15
x = torch.zeros((len(all_nodes), num_features), dtype=torch.float)

# Pre-compute graph metrics
print("   Computing PageRank...")
pagerank = nx.pagerank(G, max_iter=100)

print("   Computing HITS Hub & Authority...")
try:
    hubs, authorities = nx.hits(G, max_iter=100)
except:
    hubs = {n: 0.0 for n in G.nodes()}
    authorities = {n: 0.0 for n in G.nodes()}

print("   Computing Clustering Coefficients...")
G_undirected = G.to_undirected()
clustering = nx.clustering(G_undirected)

# Pre-compute per-node channel and velocity stats
print("   Computing Channel Diversity & Velocity per node...")
node_channels = {}       # user -> set of channels used
node_countries = {}      # user -> set of countries
node_timestamps = {}     # user -> list of timestamps
node_amounts = {}        # user -> list of amounts
node_cross_border = {}   # user -> count of cross-border txns

for _, row in txns.iterrows():
    for uid in [row['sender_id'], row['receiver_id']]:
        if uid not in node_channels:
            node_channels[uid] = set()
            node_countries[uid] = set()
            node_timestamps[uid] = []
            node_amounts[uid] = []
            node_cross_border[uid] = 0
        
        node_channels[uid].add(row['channel'])
        node_amounts[uid].append(row['amount'])
        
        try:
            node_timestamps[uid].append(datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S"))
        except:
            pass
        
        if 'sender_country' in row and 'receiver_country' in row:
            node_countries[uid].add(row.get('sender_country', ''))
            node_countries[uid].add(row.get('receiver_country', ''))
            if row.get('sender_country', '') != row.get('receiver_country', ''):
                node_cross_border[uid] += 1

# Build jurisdiction risk lookup
jurisdiction_risk = dict(zip(users['country'], users['jurisdiction_risk']))

# Build user metadata lookup
user_meta = users.set_index('user_id').to_dict('index')

print("   Building feature vectors...")
for node, idx in node_mapping.items():
    # === GRAPH TOPOLOGY (Features 0-6) ===
    # F0: In-Degree
    x[idx][0] = G.in_degree(node)
    # F1: Out-Degree
    x[idx][1] = G.out_degree(node)
    # F2: PageRank
    x[idx][2] = pagerank.get(node, 0.0) * 10000
    # F3: Hub Score
    x[idx][3] = hubs.get(node, 0.0) * 1000
    # F4: Authority Score
    x[idx][4] = authorities.get(node, 0.0) * 1000
    # F5: Clustering Coefficient
    x[idx][5] = clustering.get(node, 0.0)
    # F6: In/Out Ratio (Pass-through indicator)
    total_deg = G.in_degree(node) + G.out_degree(node)
    if total_deg > 0:
        x[idx][6] = min(G.in_degree(node), G.out_degree(node)) / max(G.in_degree(node), G.out_degree(node), 1)
    
    # === CROSS-CHANNEL FEATURES (Features 7-9) ===
    # F7: Channel Diversity (How many different channels does this user use?)
    # Mules use MANY channels (receive mobile, send ATM, etc.)
    x[idx][7] = len(node_channels.get(node, set()))
    
    # F8: Cross-Border Transaction Count
    x[idx][8] = node_cross_border.get(node, 0)
    
    # F9: Jurisdiction Count (How many countries is this user connected to?)
    x[idx][9] = len(node_countries.get(node, set()))
    
    # === VELOCITY FEATURES (Features 10-12) ===
    timestamps = node_timestamps.get(node, [])
    if len(timestamps) >= 2:
        timestamps.sort()
        # F10: Minimum time between transactions (seconds)
        # Mules move money FAST - tiny gaps between transactions
        time_gaps = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1)]
        x[idx][10] = min(time_gaps) if time_gaps else 99999
        # F11: Average time between transactions
        x[idx][11] = np.mean(time_gaps) if time_gaps else 99999
        # F12: Transaction burst count (how many txns within 10 minutes)
        burst_count = sum(1 for g in time_gaps if g <= 600)
        x[idx][12] = burst_count
    
    # === RISK FEATURES (Features 13-14) ===
    # F13: Jurisdiction Risk Score (from user's country)
    if node in user_meta:
        x[idx][13] = user_meta[node].get('jurisdiction_risk', 0.0)
    
    # F14: Amount Structuring Indicator
    # How many transactions are between $8,500-$9,999 (just under reporting threshold)?
    amounts = node_amounts.get(node, [])
    if amounts:
        structuring_count = sum(1 for a in amounts if 8500 <= a <= 9999)
        x[idx][14] = structuring_count

# Normalize features
for f in range(num_features):
    col = x[:, f]
    col_max = col.max()
    if col_max > 0:
        x[:, f] = col / col_max

# ============================================================
# 3. LABELS
# ============================================================
y = torch.zeros(len(all_nodes), dtype=torch.long)
mule_set = set(users[users['is_mule'] == 1]['user_id'])
for node, idx in node_mapping.items():
    if node in mule_set:
        y[idx] = 1

print(f"   Mules in graph: {(y == 1).sum().item()} | Clean: {(y == 0).sum().item()}")

# ============================================================
# 4. EDGES
# ============================================================
edge_src = []
edge_dst = []
for _, row in txns.iterrows():
    s = row['sender_id']
    r = row['receiver_id']
    if s in node_mapping and r in node_mapping:
        edge_src.append(node_mapping[s])
        edge_dst.append(node_mapping[r])

edge_index = torch.tensor([edge_src, edge_dst], dtype=torch.long)

data = Data(x=x, edge_index=edge_index, y=y)

# ============================================================
# 5. THE GNN MODEL - 3-Layer GraphSAGE
# ============================================================
print(f"\n3. Building 3-Layer GraphSAGE with {num_features} input features...")

class MuleDetectorGNN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = SAGEConv(num_features, 64)
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

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = MuleDetectorGNN().to(device)
data = data.to(device)

# Use weighted loss to handle class imbalance (few mules vs many clean users)
num_clean = (y == 0).sum().item()
num_mule = (y == 1).sum().item()
weight = torch.tensor([1.0, num_clean / max(num_mule, 1)], dtype=torch.float).to(device)

optimizer = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=5e-4)

print(f"\n4. Training on {device.type.upper()} for 400 epochs (weighted loss)...")
model.train()
for epoch in range(400):
    optimizer.zero_grad()
    out = model(data)
    loss = F.nll_loss(out, data.y, weight=weight)
    loss.backward()
    optimizer.step()
    if epoch % 50 == 0:
        print(f'   Epoch {epoch:>3d} | Loss: {loss.item():.4f}')

# ============================================================
# 6. EVALUATION
# ============================================================
print("\n5. Evaluating...")
model.eval()
with torch.no_grad():
    out = model(data)
    pred = out.argmax(dim=1)
    probs = torch.exp(out)[:, 1]

correct = (pred == data.y).sum()
acc = int(correct) / len(data.y)

tp = ((pred == 1) & (data.y == 1)).sum().item()
fp = ((pred == 1) & (data.y == 0)).sum().item()
fn = ((pred == 0) & (data.y == 1)).sum().item()
tn = ((pred == 0) & (data.y == 0)).sum().item()
precision = tp / max(tp + fp, 1)
recall = tp / max(tp + fn, 1)
f1 = 2 * precision * recall / max(precision + recall, 0.001)

print(f"\n{'=' * 60}")
print(f"  TRACENET GNN v3 RESULTS ({device.type.upper()})")
print(f"{'=' * 60}")
print(f"  ✅ Accuracy:     {acc * 100:.2f}%")
print(f"  ✅ Precision:    {precision * 100:.2f}%")
print(f"  ✅ Recall:       {recall * 100:.2f}%")
print(f"  ✅ F1 Score:     {f1 * 100:.2f}%")
print(f"  ✅ True Pos:     {tp} (Mules caught)")
print(f"  ✅ False Pos:    {fp} (False alarms)")
print(f"  ✅ False Neg:    {fn} (Mules missed)")
print(f"  ✅ True Neg:     {tn} (Clean users cleared)")
print(f"  ✅ Features:     {num_features}")
print(f"  ✅ Channels:     {txns['channel'].nunique()}")
print(f"  ✅ Jurisdictions:{users['country'].nunique()}")
print(f"{'=' * 60}")

# Save
os.makedirs('models', exist_ok=True)
torch.save(model.state_dict(), 'models/gnn_model.pth')

# Also save the feature config so the API knows what to expect
import json
config = {
    "num_features": num_features,
    "hidden_1": 64,
    "hidden_2": 32,
    "node_count": len(all_nodes),
    "edge_count": len(edge_src),
    "mule_count": num_mule,
    "accuracy": round(acc * 100, 2),
    "precision": round(precision * 100, 2),
    "recall": round(recall * 100, 2),
    "f1": round(f1 * 100, 2),
    "channels": list(txns['channel'].unique()),
    "jurisdictions": list(users['country'].unique())
}
with open('models/model_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"\n✅ GNN v3 Brain saved to models/gnn_model.pth")
print(f"✅ Model config saved to models/model_config.json")