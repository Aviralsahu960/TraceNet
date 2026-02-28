import time
import random
import requests
import uuid

API_URL = "http://127.0.0.1:8000/score_transaction"

print("🔌 Connecting to TraceNet Live API...")
time.sleep(1)

# Generate a pool of fake users
users = [f"user_{i}" for i in range(1, 100)]
# Add some specific nodes that might be recognized by the graph as high-risk
atms = ["ATM_1", "ATM_999", "ATM_500"]

while True:
    # 1. Create a fake transaction
    sender = random.choice(users)
    
    # 20% chance to simulate a shady, high-value transfer to a central node
    if random.random() < 0.2:
        receiver = random.choice(atms)
        amount = round(random.uniform(5000, 15000), 2) # Big money
    else:
        receiver = random.choice(users)
        amount = round(random.uniform(10, 500), 2) # Normal coffee/rent money
        
    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    
    payload = {
        "txn_id": txn_id,
        "sender_id": sender,
        "receiver_id": receiver,
        "amount": amount,
        "channel": random.choice(["mobile", "web", "branch"])
    }
    
    # 2. Fire it at our API!
    try:
        print(f"[{time.strftime('%H:%M:%S')}] 💸 Processing ${amount} from {sender} to {receiver}...")
        response = requests.post(API_URL, json=payload).json()
        
        # 3. Read the API's decision
        if response["action"] == "BLOCK":
            print(f"   🚨 BLOCKED! Risk Score: {response['risk_score']}%")
            print(f"   📜 Qwen AI Report: {response['sar_report']}\n")
        else:
            print(f"   ✅ APPROVED. Risk Score: {response['risk_score']}%\n")
            
    except Exception as e:
        print(f"   ❌ Waiting for API to come online...")
        
    # Wait 3 seconds before the next transaction
    time.sleep(3)
    