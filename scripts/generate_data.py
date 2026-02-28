import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta
import os

fake = Faker()
os.makedirs('data', exist_ok=True)

NUM_USERS = 500
NUM_NORMAL_TXNS = 5000
NUM_MULE_RINGS = 20

print("Generating Users...")
users = [{"user_id": f"U_{i}", "name": fake.name(), "is_mule": 0} for i in range(NUM_USERS)]
start_date = datetime.now() - timedelta(days=30)

print("Generating Normal Transactions...")
transactions = []
for _ in range(NUM_NORMAL_TXNS):
    sender, receiver = random.sample(users, 2)
    transactions.append({
        "txn_id": fake.uuid4(),
        "sender_id": sender["user_id"],
        "receiver_id": receiver["user_id"],
        "amount": round(random.uniform(10.0, 500.0), 2),
        "timestamp": start_date + timedelta(minutes=random.randint(1, 40000)),
        "is_fraud": 0
    })

print("Injecting Mule Rings...")
for _ in range(NUM_MULE_RINGS):
    gang = random.sample(users, 5)
    boss = gang[0]
    
    for u in users:
        if u["user_id"] in [m["user_id"] for m in gang]: u["is_mule"] = 1

    ring_time = start_date + timedelta(minutes=random.randint(1, 40000))
    
    # Minions send to boss
    for minion in gang[1:]:
        transactions.append({
            "txn_id": fake.uuid4(), "sender_id": minion["user_id"], 
            "receiver_id": boss["user_id"], "amount": random.uniform(1900, 2100),
            "timestamp": ring_time, "is_fraud": 1
        })
    # Boss cashes out
    transactions.append({
        "txn_id": fake.uuid4(), "sender_id": boss["user_id"], 
        "receiver_id": "ATM_999", "amount": 7900.00,
        "timestamp": ring_time + timedelta(minutes=3), "is_fraud": 1
    })

pd.DataFrame(users).to_csv('data/users.csv', index=False)
pd.DataFrame(transactions).to_csv('data/transactions.csv', index=False)
print("✅ Data saved to data/users.csv and data/transactions.csv")