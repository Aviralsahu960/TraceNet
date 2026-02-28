import pandas as pd
import numpy as np
import os
import random
from datetime import datetime, timedelta

os.makedirs('data', exist_ok=True)
random.seed(42)
np.random.seed(42)

print("=" * 60)
print("  TraceNet: Generating Multi-Channel AML Dataset")
print("=" * 60)

# ============================================================
# 1. USERS & ENTITIES
# ============================================================
num_users = 5000
channels = ["mobile_app", "web", "atm", "upi", "wire", "branch"]
jurisdictions = {
    "US": 0.1, "UK": 0.1, "IN": 0.05, "SG": 0.05, "AE": 0.3,
    "KY": 0.5, "PA": 0.5, "VG": 0.4, "NGA": 0.35, "RU": 0.4
}  # country: base_risk_score

users = []
for i in range(num_users):
    country = random.choice(list(jurisdictions.keys()))
    users.append({
        'user_id': f"U{i:05d}",
        'name': f"User_{i}",
        'country': country,
        'jurisdiction_risk': jurisdictions[country],
        'account_type': random.choice(['personal', 'business', 'shell_company']),
        'kyc_verified': random.choice([True, True, True, False]),  # 75% verified
        'account_age_days': random.randint(1, 1000),
        'linked_accounts': [],  # Will be populated for mules
        'is_mule': 0,
        'is_sanctioned': 0
    })

users_df = pd.DataFrame(users)

# ============================================================
# 2. MULE RINGS (Complex, Multi-Channel)
# ============================================================

# RING A: "The Scatter-Gather" - Boss distributes via Mobile, mules withdraw at ATMs
boss_A = "U00001"
mules_A = [f"U{i:05d}" for i in range(100, 150)]
gather_A = "U00099"  # The collector

# RING B: "The Shell Nesting" - Money bounces between shell companies across jurisdictions
shells_B = ["U00998", "U00997", "U00996", "U00995"]

# RING C: "The UPI Fragmentation Ring" - Splits large amounts into tiny UPI payments
boss_C = "U00500"
fragmenters_C = [f"U{i:05d}" for i in range(501, 521)]

# RING D: "The Cross-Border Velocity Ring" - Money moves across 4 countries in under 10 minutes
velocity_ring = ["U00800", "U00801", "U00802", "U00803", "U00804"]

# RING E: "The Circular Laundering Ring" - Money goes in a perfect circle
circle_ring = [f"U{i:05d}" for i in range(900, 910)]

# Mark all mules
all_mules = set([boss_A, gather_A] + mules_A + shells_B + [boss_C] + fragmenters_C + velocity_ring + circle_ring)
users_df.loc[users_df['user_id'].isin(all_mules), 'is_mule'] = 1

# Mark shell companies
users_df.loc[users_df['user_id'].isin(shells_B), 'account_type'] = 'shell_company'

# Mark sanctioned entities
sanctioned = random.sample(list(all_mules), 5)
users_df.loc[users_df['user_id'].isin(sanctioned), 'is_sanctioned'] = 1

# Set high-risk jurisdictions for mule rings
for uid in velocity_ring:
    users_df.loc[users_df['user_id'] == uid, 'country'] = random.choice(['KY', 'PA', 'VG', 'AE'])
for uid in shells_B:
    users_df.loc[users_df['user_id'] == uid, 'country'] = random.choice(['KY', 'VG', 'PA'])
    users_df.loc[users_df['user_id'] == uid, 'kyc_verified'] = False

# Link accounts (same person, multiple accounts)
users_df.at[users_df[users_df['user_id'] == boss_A].index[0], 'linked_accounts'] = str(["U00002", "U00003"])
users_df.at[users_df[users_df['user_id'] == "U00998"].index[0], 'linked_accounts'] = str(["U00997"])

# ============================================================
# 3. TRANSACTIONS (Multi-Channel, Time-Stamped)
# ============================================================
transactions = []
txn_id = 10000
base_time = datetime(2026, 2, 21, 8, 0, 0)

print("\nGenerating normal background transactions...")
# Normal transactions (15,000)
for _ in range(15000):
    sender = random.choice(users_df['user_id'].tolist())
    receiver = random.choice(users_df['user_id'].tolist())
    if sender != receiver:
        t = base_time + timedelta(minutes=random.randint(0, 1440))
        transactions.append({
            'txn_id': f"TXN_{txn_id}",
            'sender_id': sender,
            'receiver_id': receiver,
            'amount': round(random.uniform(5.0, 2500.0), 2),
            'channel': random.choice(channels),
            'timestamp': t.strftime("%Y-%m-%d %H:%M:%S"),
            'sender_country': users_df[users_df['user_id'] == sender]['country'].values[0],
            'receiver_country': users_df[users_df['user_id'] == receiver]['country'].values[0],
            'is_suspicious': 0
        })
        txn_id += 1

print("Generating Ring A: Scatter-Gather (Mobile -> ATM)...")
# RING A: Boss sends via MOBILE, mules withdraw at ATM within 5 minutes
for mule in mules_A:
    t1 = base_time + timedelta(hours=11, minutes=random.randint(0, 10))
    t2 = t1 + timedelta(minutes=random.randint(2, 5))  # ATM withdrawal within 5 min!
    
    # Boss -> Mule via Mobile App
    transactions.append({
        'txn_id': f"TXN_{txn_id}", 'sender_id': boss_A, 'receiver_id': mule,
        'amount': 9500.00, 'channel': 'mobile_app',
        'timestamp': t1.strftime("%Y-%m-%d %H:%M:%S"),
        'sender_country': 'US', 'receiver_country': 'US', 'is_suspicious': 1
    })
    txn_id += 1
    
    # Mule -> ATM withdrawal (different channel!)
    transactions.append({
        'txn_id': f"TXN_{txn_id}", 'sender_id': mule, 'receiver_id': gather_A,
        'amount': 9400.00, 'channel': 'atm',
        'timestamp': t2.strftime("%Y-%m-%d %H:%M:%S"),
        'sender_country': 'US', 'receiver_country': 'KY', 'is_suspicious': 1
    })
    txn_id += 1

print("Generating Ring B: Shell Company Nesting (Wire transfers)...")
# RING B: Shell companies bouncing money via wire transfers across jurisdictions
for _ in range(40):
    for i in range(len(shells_B) - 1):
        t = base_time + timedelta(hours=12, minutes=random.randint(0, 30))
        transactions.append({
            'txn_id': f"TXN_{txn_id}", 'sender_id': shells_B[i], 'receiver_id': shells_B[i+1],
            'amount': round(random.uniform(40000, 50000), 2), 'channel': 'wire',
            'timestamp': t.strftime("%Y-%m-%d %H:%M:%S"),
            'sender_country': random.choice(['KY', 'VG']), 'receiver_country': random.choice(['PA', 'AE']),
            'is_suspicious': 1
        })
        txn_id += 1
    # Loop back
    transactions.append({
        'txn_id': f"TXN_{txn_id}", 'sender_id': shells_B[-1], 'receiver_id': shells_B[0],
        'amount': round(random.uniform(39000, 49000), 2), 'channel': 'wire',
        'timestamp': t.strftime("%Y-%m-%d %H:%M:%S"),
        'sender_country': 'AE', 'receiver_country': 'KY', 'is_suspicious': 1
    })
    txn_id += 1

print("Generating Ring C: UPI Fragmentation...")
# RING C: Boss sends large amount, fragmenters split into tiny UPI payments
for frag in fragmenters_C:
    t1 = base_time + timedelta(hours=14, minutes=random.randint(0, 5))
    # Boss -> Fragmenter (large amount via web)
    transactions.append({
        'txn_id': f"TXN_{txn_id}", 'sender_id': boss_C, 'receiver_id': frag,
        'amount': 10000.00, 'channel': 'web',
        'timestamp': t1.strftime("%Y-%m-%d %H:%M:%S"),
        'sender_country': 'IN', 'receiver_country': 'IN', 'is_suspicious': 1
    })
    txn_id += 1
    
    # Fragmenter splits into 20 tiny UPI payments to random people
    for j in range(20):
        t2 = t1 + timedelta(minutes=j)
        receiver = random.choice(users_df['user_id'].tolist())
        transactions.append({
            'txn_id': f"TXN_{txn_id}", 'sender_id': frag, 'receiver_id': receiver,
            'amount': round(random.uniform(400, 550), 2), 'channel': 'upi',
            'timestamp': t2.strftime("%Y-%m-%d %H:%M:%S"),
            'sender_country': 'IN', 'receiver_country': 'IN', 'is_suspicious': 1
        })
        txn_id += 1

print("Generating Ring D: Cross-Border Velocity Ring...")
# RING D: Money hops across 4 countries in under 10 minutes
for _ in range(30):
    t = base_time + timedelta(hours=15, minutes=random.randint(0, 60))
    ring_countries = ['US', 'KY', 'AE', 'SG', 'VG']
    for i in range(len(velocity_ring) - 1):
        t_hop = t + timedelta(minutes=i * 2)  # 2 minutes per hop!
        transactions.append({
            'txn_id': f"TXN_{txn_id}", 'sender_id': velocity_ring[i], 'receiver_id': velocity_ring[i+1],
            'amount': round(random.uniform(20000, 30000), 2),
            'channel': random.choice(['wire', 'web']),
            'timestamp': t_hop.strftime("%Y-%m-%d %H:%M:%S"),
            'sender_country': ring_countries[i], 'receiver_country': ring_countries[i+1],
            'is_suspicious': 1
        })
        txn_id += 1

print("Generating Ring E: Circular Laundering...")
# RING E: Perfect circle - money goes A->B->C->D->...->A
for _ in range(25):
    t = base_time + timedelta(hours=16, minutes=random.randint(0, 60))
    for i in range(len(circle_ring)):
        next_i = (i + 1) % len(circle_ring)
        transactions.append({
            'txn_id': f"TXN_{txn_id}", 'sender_id': circle_ring[i], 'receiver_id': circle_ring[next_i],
            'amount': round(random.uniform(5000, 8000), 2),
            'channel': random.choice(channels),
            'timestamp': t.strftime("%Y-%m-%d %H:%M:%S"),
            'sender_country': random.choice(list(jurisdictions.keys())),
            'receiver_country': random.choice(list(jurisdictions.keys())),
            'is_suspicious': 1
        })
        txn_id += 1

txns_df = pd.DataFrame(transactions)
txns_df = txns_df.sort_values('timestamp').reset_index(drop=True)

# Save
users_df.to_csv('data/users.csv', index=False)
txns_df.to_csv('data/transactions.csv', index=False)

# Summary
print(f"\n{'=' * 60}")
print(f"  ✅ Total Users: {len(users_df)}")
print(f"  ✅ Total Transactions: {len(txns_df)}")
print(f"  ✅ Mule Accounts: {users_df['is_mule'].sum()}")
print(f"  ✅ Sanctioned Entities: {users_df['is_sanctioned'].sum()}")
print(f"  ✅ Suspicious Transactions: {txns_df['is_suspicious'].sum()}")
print(f"  ✅ Channels: {txns_df['channel'].nunique()} ({', '.join(txns_df['channel'].unique())})")
print(f"  ✅ Jurisdictions: {users_df['country'].nunique()}")
print(f"\n  Ring A: Scatter-Gather (Mobile → ATM)")
print(f"  Ring B: Shell Nesting (Wire cross-border)")
print(f"  Ring C: UPI Fragmentation")
print(f"  Ring D: Cross-Border Velocity")
print(f"  Ring E: Circular Laundering")
print(f"{'=' * 60}")