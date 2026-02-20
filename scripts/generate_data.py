import os
import random

import pandas as pd
from faker import Faker

fake = Faker()

RISK_TIERS = ["low", "medium", "high", "critical"]

records = [
    {
        "id": i + 1,
        "name": fake.name(),
        "account_number": fake.bban(),
        "risk_tier": random.choice(RISK_TIERS),
    }
    for i in range(100)
]

df = pd.DataFrame(records)

output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "users.csv")
df.to_csv(output_path, index=False)

print(f"Saved {len(df)} users to {output_path}")
